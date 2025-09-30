import sqlite3
import yaml
import json
from datetime import date
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from database import init_db, DATABASE_NAME

LLM_MODEL_NAME = "phi3:3.8b-mini-4k-instruct-q4_0"

# =================================================================
# CORREÇÃO APLICADA AQUI: AS CHAVES {} NOS EXEMPLOS FORAM DUPLICADAS
# =================================================================
CLASSIFICATION_PROMPT_TEMPLATE = """
Você é um teólogo moral e um especialista em análise de texto. Sua tarefa é analisar um par de pergunta e resposta de um exame de consciência.
Com base na resposta do usuário NO CONTEXTO da pergunta, determine se a resposta indica a ocorrência de um pecado.

**Definição de Pecado:** Para esta tarefa, considere que a resposta indica um pecado se o usuário admitir uma falha, omissão ou ação deliberada que vai contra o ensinamento da pergunta. A resposta deve ser uma admissão clara de culpa ou falha.

**REGRAS IMPORTANTES:**
1.  Responda APENAS com um objeto JSON. Não inclua nenhuma outra palavra ou explicação.
2.  O JSON deve ter uma única chave: "pecado".
3.  O valor de "pecado" deve ser 1 se a resposta indicar um pecado, ou 0 se não indicar.

**Exemplos:**
- Pergunta: "Eu neguei ou abandonei a minha fé?"
- Resposta: "Sim"
- Sua saída: {{"pecado": 1}}

- Pergunta: "Tenho a preocupação de conhecê-la melhor?"
- Resposta: "Sim"
- Sua saída: {{"pecado": 0}}

- Pergunta: "Fui honesto e diligente no meu trabalho?"
- Resposta: "Não"
- Sua saída: {{"pecado": 1}}

Agora, analise o seguinte par:
---
Pergunta: {question}
Resposta: {answer}
---
Sua saída:
"""

def analyze_and_store_exam(respostas_path='respostas.yaml', perguntas_path='perguntas.yaml'):
    """
    Lê um exame, usa o LLM para classificar cada resposta e salva no SQLite.
    """
    init_db()

    try:
        with open(perguntas_path, 'r', encoding='utf-8') as f:
            perguntas_data = {p['id']: p['texto'] for p in yaml.safe_load(f)['perguntas']}
    except FileNotFoundError:
        print(f"ERRO CRÍTICO: O arquivo de perguntas '{perguntas_path}' não foi encontrado.")
        return
    
    try:
        with open(respostas_path, 'r', encoding='utf-8') as f:
            respostas_data = yaml.safe_load(f)['respostas']
    except FileNotFoundError:
        print(f"AVISO: O arquivo de respostas '{respostas_path}' não foi encontrado. Nenhuma análise de progresso será feita.")
        return

    llm = OllamaLLM(model=LLM_MODEL_NAME, format='json')
    prompt_template = PromptTemplate.from_template(CLASSIFICATION_PROMPT_TEMPLATE)
    
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    today_str = date.today().isoformat()

    # ===== ADICIONADO: Apaga os registros antigos do mesmo dia =====
    print(f"Limpando registros existentes para a data: {today_str}...")
    cursor.execute("DELETE FROM progress WHERE exam_date = ?", (today_str,))
    # ==========================================================

    print("Iniciando classificação das respostas com o LLM...")
    for resp in respostas_data:
        question_id = resp['id_pergunta']
        question_text = perguntas_data.get(question_id, "")
        answer_text = resp['resposta']

        if not question_text or not answer_text.strip():
            continue

        prompt = prompt_template.format(question=question_text, answer=answer_text)
        
        try:
            llm_output_str = llm.invoke(prompt)
            llm_output = json.loads(llm_output_str) if isinstance(llm_output_str, str) else llm_output_str
            is_sin = llm_output.get('pecado')

            if is_sin is not None:
                print(f"  - Pergunta {question_id}: Pecado? {'Sim' if is_sin == 1 else 'Não'}")
                cursor.execute(
                    "INSERT INTO progress (exam_date, question_id, is_sin) VALUES (?, ?, ?)",
                    (today_str, question_id, is_sin)
                )
            else:
                print(f"  - Pergunta {question_id}: LLM não retornou a chave 'pecado'.")

        except (json.JSONDecodeError, Exception) as e:
            print(f"Erro ao processar a pergunta {question_id}: {e}")

    conn.commit()
    conn.close()
    print("Análise de progresso salva no banco de dados.")