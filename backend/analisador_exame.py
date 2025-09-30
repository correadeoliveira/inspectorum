import os
import time
import threading
from langchain_ollama import OllamaLLM

# --- CONFIGURAÇÕES ---
# Certifique-se de que este é o mesmo modelo que você está servindo com o Ollama
# Usei o nome completo que você forneceu para garantir a compatibilidade.
LLM_MODEL_NAME = "phi3:3.8b-mini-4k-instruct-q4_0"
PROMPT_FILE_PATH = "prompt_para_llm.txt"

def get_llm():
    """Inicializa e retorna a instância do LLM do Ollama."""
    return OllamaLLM(model=LLM_MODEL_NAME)

def ler_prompt_do_arquivo(caminho_arquivo):
    """Lê o conteúdo completo de um arquivo de texto."""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERRO: O arquivo '{caminho_arquivo}' não foi encontrado.")
        print("Por favor, execute primeiro o script 'exame_consciencia.py' para gerar o prompt.")
        return None

# --- LÓGICA PRINCIPAL DA ANÁLISE ---
if __name__ == "__main__":
    print("✅ Iniciando o sistema de análise de exame de consciência...")

    # 1. Carregar o prompt do arquivo de texto
    prompt_texto = ler_prompt_do_arquivo(PROMPT_FILE_PATH)
    
    # Se o arquivo não existir, o programa encerra.
    if not prompt_texto:
        exit()

    print(f"Modelo LLM local a ser utilizado: {LLM_MODEL_NAME}")
    print("Iniciando a análise do seu exame. Isso pode levar alguns instantes...")
    print("="*50)

    # 2. Inicializar o LLM
    llm = get_llm()

    # 3. Preparar e executar a análise em uma thread separada (para o timer funcionar)
    result_container = {}
    done_event = threading.Event()

    def run_analysis():
        """Função que será executada na thread para não bloquear a interface."""
        # A chamada é direta: o LLM recebe o prompt e gera a continuação.
        result = llm.invoke(prompt_texto)
        result_container['result'] = result
        done_event.set()

    analysis_thread = threading.Thread(target=run_analysis)
    analysis_thread.start()

    # 4. Exibir o timer de "Pensando..." enquanto a análise ocorre
    start_time = time.perf_counter()
    line_width = 50 
    while not done_event.is_set():
        elapsed_time = time.perf_counter() - start_time
        output_string = f"Analisando... Tempo decorrido: {elapsed_time:.1f}s"
        padded_string = output_string.ljust(line_width)
        print(padded_string, end="\r", flush=True)
        time.sleep(0.1)

    # Limpa a linha do timer
    print(" " * line_width, end="\r", flush=True)
    
    final_duration = time.perf_counter() - start_time
    analise_final = result_container.get('result', "Ocorreu um erro ao obter a análise.")

    # 5. Exibir o resultado final
    print("\n--- ANÁLISE E REFLEXÃO ESPIRITUAL ---")
    print(analise_final.strip())
    print("\n" + "="*50)
    print(f"[Análise concluída em {final_duration:.2f} segundos]")