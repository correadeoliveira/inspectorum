import yaml
from datetime import datetime
import os

ARQUIVO_PERGUNTAS = 'perguntas.yaml'
ARQUIVO_RESPOSTAS = 'respostas.yaml'

def carregar_perguntas(arquivo=ARQUIVO_PERGUNTAS):
    """Carrega todas as perguntas do arquivo YAML."""
    with open(arquivo, 'r', encoding='utf-8') as file:
        dados = yaml.safe_load(file)
    return dados['perguntas']

def carregar_respostas_salvas(arquivo=ARQUIVO_RESPOSTAS):
    """Carrega as respostas de um exame em andamento, se o arquivo existir."""
    if not os.path.exists(arquivo):
        return []
    try:
        with open(arquivo, 'r', encoding='utf-8') as file:
            dados = yaml.safe_load(file)
            # Retorna a lista de respostas, ou uma lista vazia se o arquivo estiver mal formatado
            return dados.get('respostas', []) if dados else []
    except (yaml.YAMLError, IOError):
        # Em caso de erro de leitura ou arquivo corrompido, trata como se não houvesse respostas
        return []


def salvar_progresso(respostas, arquivo=ARQUIVO_RESPOSTAS):
    """Salva a lista completa de respostas, substituindo o arquivo anterior."""
    dados_para_salvar = {
        # A data é atualizada a cada salvamento
        'data_exame': datetime.now().isoformat(),
        'respostas': respostas
    }
    with open(arquivo, 'w', encoding='utf-8') as file:
        yaml.dump(dados_para_salvar, file, allow_unicode=True, sort_keys=False)

def preparar_prompt_para_llm(perguntas, respostas):
    """Junta perguntas e respostas para criar um prompt formatado para o LLM."""
    mapa_perguntas = {p['id']: p['texto'] for p in perguntas}
    
    texto_consolidado = ""
    for r in respostas:
        id_pergunta = r['id_pergunta']
        if id_pergunta in mapa_perguntas:
            texto_pergunta = mapa_perguntas[id_pergunta]
            texto_resposta = r['resposta']
            texto_consolidado += f"Pergunta: {texto_pergunta}\nResposta: {texto_resposta}\n\n"
            
    prompt_final = f"""
    A seguir estão as perguntas e respostas de um exame de consciência. 
    Sua tarefa é analisar essas reflexões com sensibilidade e profundidade espiritual. 
    Com base nas respostas fornecidas, identifique os principais pontos de virtude, as áreas que necessitam de mais atenção e crescimento, e possíveis padrões de comportamento.
    Ofereça uma reflexão construtiva e encorajadora, sugerindo um ou dois pontos práticos para o desenvolvimento espiritual da pessoa, sem ser prescritivo ou autoritário.

    --- INÍCIO DO EXAME ---
    {texto_consolidado}
    --- FIM DO EXAME ---

    Análise e Reflexão:
    """
    
    return prompt_final

# --- LÓGICA PRINCIPAL DO SCRIPT ---
if __name__ == "__main__":
    # 1. Carregar todas as perguntas e as respostas já existentes
    todas_as_perguntas = carregar_perguntas()
    respostas_salvas = carregar_respostas_salvas()
    
    ids_respondidos = {r['id_pergunta'] for r in respostas_salvas}

    # 2. Verificar se o exame anterior foi concluído
    if len(ids_respondidos) == len(todas_as_perguntas) and respostas_salvas:
        print("Você completou o exame de consciência anterior.")
        iniciar_novo = input("Deseja iniciar um novo exame? (Isso apagará o anterior) [s/n]: ").lower()
        if iniciar_novo == 's':
            respostas_salvas = []  # Reinicia a lista de respostas
            ids_respondidos = set()      # Esvazia o conjunto de IDs
            print("\nIniciando um novo exame...")
        else:
            print("Ok, encerrando o programa.")
            # Opcional: Preparar o prompt do exame concluído antes de sair
            prompt = preparar_prompt_para_llm(todas_as_perguntas, respostas_salvas)
            with open('prompt_para_llm.txt', 'w', encoding='utf-8') as f:
                f.write(prompt)
            print("Prompt do exame anterior salvo em 'prompt_para_llm.txt'.")
            exit() # Encerra o script

    # 3. Determinar as perguntas que ainda faltam
    perguntas_a_fazer = [p for p in todas_as_perguntas if p['id'] not in ids_respondidos]

    # 4. Coletar novas respostas
    if not perguntas_a_fazer:
        print("Nenhuma pergunta nova para fazer. O exame parece estar configurado incorretamente.")
    else:
        print("Iniciando o Exame de Consciência.")
        if respostas_salvas:
            print(f"Continuando de onde você parou. Você já respondeu {len(respostas_salvas)} de {len(todas_as_perguntas)} perguntas.\n")
        
        try:
            for pergunta in perguntas_a_fazer:
                print(f"[{pergunta['categoria']}]")
                resposta_usuario = input(f"{pergunta['texto']}\nSua resposta: ")
                
                respostas_salvas.append({
                    'id_pergunta': pergunta['id'],
                    'resposta': resposta_usuario
                })
                
                # Salva o progresso total após cada nova resposta
                salvar_progresso(respostas_salvas)
                print("...progresso salvo.\n" + "-" * 20)

        except KeyboardInterrupt:
            print("\n\nExame interrompido. Seu progresso foi salvo. Você pode continuar depois.")
            exit()

    # 5. Finalização e preparação para o LLM
    print("\nExame de consciência concluído!")
    print("Preparando o resumo para análise...")
    
    prompt_final = preparar_prompt_para_llm(todas_as_perguntas, respostas_salvas)
    
    with open('prompt_para_llm.txt', 'w', encoding='utf-8') as f:
        f.write(prompt_final)
        
    print("Prompt para o LLM foi gerado e salvo em 'prompt_para_llm.txt'.")