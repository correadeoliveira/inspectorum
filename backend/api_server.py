from flask import Flask, jsonify, request
from flask_cors import CORS
import yaml
import os
import json
from datetime import datetime, date, timedelta
from langchain_ollama import OllamaLLM
import threading
import sqlite3
import ollama
from database import DATABASE_NAME, init_db
from llm_classifier import analyze_and_store_exam, CLASSIFICATION_PROMPT_TEMPLATE
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

# --- CONFIGURAÇÕES ---
ARQUIVO_PERGUNTAS = 'perguntas.yaml'
ARQUIVO_RESPOSTAS = 'respostas.yaml'
LLM_MODEL_NAME = "phi3:3.8b-mini-4k-instruct-q4_0"
LOCK_FILE_PATH = 'analysis.lock'
RAG_INDEX_PATH = "faiss_index_mistral"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# --- INICIALIZAÇÃO DO FLASK ---
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# --- LÓGICA DE CARREGAMENTO DO RAG (Lazy Loading) ---
qa_chain = None
def get_rag_chain():
    global qa_chain
    if qa_chain is None:
        print("Inicializando a cadeia de RAG pela primeira vez...")
        if not os.path.exists(RAG_INDEX_PATH):
            raise FileNotFoundError(f"Índice RAG não encontrado em '{RAG_INDEX_PATH}'.")
        
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        vector_store = FAISS.load_local(RAG_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        llm = OllamaLLM(model=LLM_MODEL_NAME, temperature=0.1)
        
        simplified_rag_template = """
Use a seguinte informação de contexto para responder à pergunta no final. Responda de forma pastoral e baseie-se estritamente no texto fornecido. Se a resposta não estiver no contexto, diga de forma clara que a informação não foi encontrada nos documentos disponíveis.

Contexto:
{context}

Pergunta: {question}
Resposta:
"""
        prompt = PromptTemplate(template=simplified_rag_template, input_variables=["context", "question"])
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(),
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        print("Cadeia de RAG pronta.")
    return qa_chain

# --- ROTA DE VERIFICAÇÃO DO SISTEMA ---
@app.route('/api/system/health', methods=['GET'])
def system_health_check():
    errors = []
    required_files = ['perguntas.yaml', 'faiss_index_mistral/index.faiss']
    for file_path in required_files:
        if not os.path.exists(file_path):
            if 'progress.db' in file_path:
                print("Arquivo 'progress.db' não encontrado, será criado no primeiro exame.")
            else:
                errors.append(f"Arquivo essencial não encontrado: {file_path}")

    try:
        print("Verificando a disponibilidade do modelo LLM...")
        llm = OllamaLLM(model=LLM_MODEL_NAME)
        llm.invoke("teste") 
        print("Modelo LLM carregado com sucesso.")
    except Exception as e:
        error_message = str(e)
        if "404" in error_message:
             errors.append(f"Modelo LLM '{LLM_MODEL_NAME}' não encontrado no Ollama. Execute 'ollama pull {LLM_MODEL_NAME}'.")
        else:
            errors.append(f"Não foi possível carregar o modelo do Ollama. O serviço está rodando? Erro: {e}")

    if not errors:
        return jsonify({"status": "ok", "message": "Sistema pronto."})
    else:
        return jsonify({"status": "error", "errors": errors}), 500

# --- FUNÇÕES AUXILIARES E ROTAS DO EXAME ---

def carregar_perguntas():
    with open(ARQUIVO_PERGUNTAS, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)['perguntas']

def carregar_respostas_salvas():
    if not os.path.exists(ARQUIVO_RESPOSTAS): return []
    try:
        with open(ARQUIVO_RESPOSTAS, 'r', encoding='utf-8') as file:
            dados = yaml.safe_load(file)
            return dados.get('respostas', []) if dados else []
    except (yaml.YAMLError, IOError):
        return []

def analyze_and_store_exam_with_lock():
    try:
        with open(LOCK_FILE_PATH, 'w') as f: f.write('processing')
        analyze_and_store_exam()
    finally:
        if os.path.exists(LOCK_FILE_PATH): os.remove(LOCK_FILE_PATH)
        print("Tarefa de análise de progresso finalizada e lock removido.")

@app.route('/api/exame/start-new', methods=['POST'])
def start_new_exam():
    if os.path.exists(ARQUIVO_RESPOSTAS):
        os.remove(ARQUIVO_RESPOSTAS)
    return jsonify({"message": "Novo exame iniciado."})

@app.route('/api/exame/current-state', methods=['GET'])
def get_current_state():
    if os.path.exists(ARQUIVO_RESPOSTAS):
        try:
            with open(ARQUIVO_RESPOSTAS, 'r', encoding='utf-8') as f:
                dados_salvos = yaml.safe_load(f)
                if dados_salvos and 'data_exame' in dados_salvos:
                    data_salva = datetime.fromisoformat(dados_salvos['data_exame']).date()
                    if data_salva < date.today():
                        print(f"Exame do dia {data_salva} encontrado. Limpando para o novo dia.")
                        os.remove(ARQUIVO_RESPOSTAS)
        except Exception as e:
            print(f"Erro ao verificar data do exame antigo: {e}")

    todas_as_perguntas = carregar_perguntas()
    respostas_salvas = carregar_respostas_salvas()
    mapa_perguntas = {p['id']: p for p in todas_as_perguntas}
    history, ids_respondidos = [], set()
    for resposta in respostas_salvas:
        question_id = resposta['id_pergunta']
        if question_id in mapa_perguntas:
            pergunta_obj = mapa_perguntas[question_id]
            history.append({"id": f"q-{question_id}", "type": "ai", "content": pergunta_obj['texto'], "categoria": pergunta_obj['categoria'], "timestamp": datetime.now().isoformat()})
            history.append({"id": f"a-{question_id}", "type": "user", "content": resposta['resposta'], "timestamp": datetime.now().isoformat()})
            ids_respondidos.add(question_id)
    perguntas_a_fazer = [p for p in todas_as_perguntas if p['id'] not in ids_respondidos]
    if not perguntas_a_fazer:
        return jsonify({ "status": "completed", "history": history })
    else:
        next_question = perguntas_a_fazer[0]
        history.append({"id": f"q-{next_question['id']}", "type": "ai", "content": next_question['texto'], "categoria": next_question['categoria'], "timestamp": datetime.now().isoformat()})
        return jsonify({"status": "in_progress", "history": history, "next_question": next_question})

@app.route('/api/exame/submit-answer', methods=['POST'])
def submit_answer():
    data = request.json
    respostas_salvas = carregar_respostas_salvas()
    respostas_salvas.append({'id_pergunta': data.get('question_id'), 'resposta': data.get('answer')})
    # Corrigindo para usar a função salvar_progresso que já existe
    salvar_progresso(respostas_salvas)
    return jsonify({"message": "Resposta salva com sucesso."})

@app.route('/api/exame/analyze', methods=['POST'])
def analyze_exam():
    try:
        init_db()
        perguntas_data = {p['id']: p for p in carregar_perguntas()}
        respostas_data = carregar_respostas_salvas()
        
        llm_classifier = OllamaLLM(model=LLM_MODEL_NAME, format='json', temperature=0.1)
        prompt_template_classifier = PromptTemplate.from_template(CLASSIFICATION_PROMPT_TEMPLATE)
        
        pecados_identificados = []
        for resp in respostas_data:
            question_id, answer_text = resp['id_pergunta'], resp['resposta']
            question_text = perguntas_data.get(question_id, {}).get('texto', "")
            if not question_text or not answer_text.strip(): continue

            prompt_clf = prompt_template_classifier.format(question=question_text, answer=answer_text)
            try:
                llm_output_str = llm_classifier.invoke(prompt_clf)
                llm_output = json.loads(llm_output_str)
                if llm_output.get('pecado') == 1:
                    pecados_identificados.append({"pergunta": question_text, "resposta": answer_text})
            except Exception as e:
                print(f"Erro ao classificar pergunta {question_id}: {e}")
        
        if not pecados_identificados:
            analise_textual = "Análise concluída. Com base em suas respostas, não foram identificados pecados claros. Continue perseverando no caminho da virtude e na vigilância."
        else:
            texto_consolidado = ""
            for pecado in pecados_identificados:
                texto_consolidado += f"Pergunta: {pecado['pergunta']}\nResposta: {pecado['resposta']}\n\n"
            
            prompt_final = f"""
            A seguir estão as respostas de um exame de consciência onde o usuário indicou ter cometido um pecado. 
            Sua tarefa é analisar essas quedas com sensibilidade e profundidade espiritual, focando em padrões de comportamento e áreas que necessitam de mais atenção.
            Ofereça uma reflexão construtiva e encorajadora sobre esses pontos, sugerindo um ou dois pontos práticos para o desenvolvimento espiritual.

            --- PECADOS IDENTIFICADOS ---
            {texto_consolidado}
            --- FIM DOS PECADOS ---

            Análise e Reflexão:
            """
            
            # ===== MUDANÇA 1: Controle do LLM (stop e num_predict) =====
            llm_textual_analyzer = OllamaLLM(
                model=LLM_MODEL_NAME,
                num_predict=1024,  # Limita a resposta a 1024 tokens
                stop=["###", "Instruction:"] # Para de gerar se encontrar esses termos
            )
            # ==========================================================

            analise_bruta = llm_textual_analyzer.invoke(prompt_final)

            # ===== MUDANÇA 2: Medida de Segurança para Cortar a Saída =====
            # Corta a string no primeiro "###" que encontrar e limpa espaços
            analise_textual = analise_bruta.split("###")[0].strip()
            # ==============================================================

        print("Iniciando a tarefa de salvamento de progresso em background...")
        thread = threading.Thread(target=analyze_and_store_exam_with_lock)
        thread.start()
        
        return jsonify({"analysis": analise_textual})

    except Exception as e:
        print(f"Erro na análise principal: {e}")
        return jsonify({"error": "Falha ao gerar a análise."}), 500

@app.route('/api/rag/query', methods=['POST'])
def rag_query():
    try:
        user_question = request.json.get('question')
        if not user_question:
            return jsonify({"error": "Nenhuma pergunta fornecida."}), 400
        
        chain = get_rag_chain()
        result = chain.invoke({"query": user_question})
        
        answer = result.get("result", "Não foi possível gerar uma resposta.")
        
        sources = []
        if result.get("source_documents"):
            for doc in result["source_documents"]:
                source_name = os.path.basename(doc.metadata.get('source', 'desconhecida'))
                page_num = doc.metadata.get('page', 'N/A')
                sources.append(f"{source_name} (pág. {page_num})")
        
        sources_text = ", ".join(list(set(sources))) if sources else "Nenhuma fonte encontrada."
        return jsonify({"answer": answer, "sources": sources_text})
        
    except Exception as e:
        print(f"Erro na consulta RAG: {e}")
        return jsonify({"error": "Falha ao processar a pergunta com o RAG."}), 500

# --- ROTAS DO DASHBOARD E OUTRAS FUNÇÕES ---
def get_consecutive_days(dates):
    if not dates: return 0
    date_objects = sorted(list(set(date.fromisoformat(d[0]) for d in dates)))
    if not date_objects: return 0
    today = date.today()
    if today - date_objects[-1] > timedelta(days=1): return 0
    consecutive_count = 1
    for i in range(len(date_objects) - 1, 0, -1):
        if date_objects[i] - date_objects[i-1] == timedelta(days=1):
            consecutive_count += 1
        else:
            break
    return consecutive_count

@app.route('/api/dashboard/status', methods=['GET'])
def get_dashboard_status():
    if os.path.exists(LOCK_FILE_PATH):
        return jsonify({"status": "processing"})
    else:
        return jsonify({"status": "idle"})

@app.route('/api/dashboard/progress', methods=['GET'])
def get_progress_data():
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        seven_days_ago = (date.today() - timedelta(days=6)).isoformat()
        cursor.execute("SELECT exam_date, SUM(is_sin), COUNT(is_sin) FROM progress WHERE exam_date >= ? GROUP BY exam_date ORDER BY exam_date ASC", (seven_days_ago,))
        weekly_data = cursor.fetchall()
        chart_data, date_map = [], {d[0]: {'sins': d[1], 'virtues': d[2] - d[1]} for d in weekly_data}
        for i in range(7):
            day = date.today() - timedelta(days=i)
            data_point = date_map.get(day.isoformat(), {'sins': 0, 'virtues': 0})
            chart_data.append({'day': day.strftime('%a'), 'sins': data_point['sins'], 'virtues': data_point['virtues']})
        chart_data.reverse()

        cursor.execute("SELECT COUNT(DISTINCT exam_date) FROM progress")
        total_sessions = cursor.fetchone()[0]
        cursor.execute("SELECT exam_date FROM progress ORDER BY exam_date DESC")
        all_dates = cursor.fetchall()
        consecutive_days = get_consecutive_days(all_dates)

        today_str = date.today().isoformat()
        yesterday_str = (date.today() - timedelta(days=1)).isoformat()
        cursor.execute("SELECT SUM(is_sin) FROM progress WHERE exam_date = ?", (today_str,))
        today_sins = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(is_sin) FROM progress WHERE exam_date = ?", (yesterday_str,))
        yesterday_sins = cursor.fetchone()[0] or 0
        
        daily_improvement = 0
        if yesterday_sins > 0:
            improvement = ((yesterday_sins - today_sins) / yesterday_sins) * 100
            daily_improvement = round(improvement)
        elif today_sins == 0:
            daily_improvement = 0
        else:
            daily_improvement = -100
        conn.close()
        return jsonify({
            "chartData": chart_data,
            "summary": {
                "totalSessions": total_sessions or 0,
                "dailyImprovement": daily_improvement,
                "consecutiveDays": consecutive_days or 0
            }
        })
    except Exception as e:
        print(f"Erro ao buscar dados do dashboard: {e}")
        return jsonify({"error": "Falha ao buscar dados de progresso."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)