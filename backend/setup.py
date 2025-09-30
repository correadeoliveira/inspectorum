import os
import subprocess
import sys
import ollama
from database import init_db
from rag_engineering import build_index, INDEX_PATH # Importa a função e a constante

LLM_MODEL_NAME = "phi3:3.8b-mini-4k-instruct-q4_0"

def run_command(command):
    """Executa um comando no terminal e lida com erros."""
    try:
        # Usamos sys.executable para garantir que estamos usando o pip do venv correto
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError:
        return False, f"Comando '{command[0]}' não encontrado. Verifique se está instalado e no PATH do sistema."

def setup_application():
    """
    Script de instalação que verifica e configura todas as dependências necessárias.
    """
    print("-" * 50)
    print("INICIANDO SCRIPT DE CONFIGURAÇÃO DO AMBIENTE")
    print("-" * 50)

    # --- ETAPA 1: BANCO DE DADOS ---
    print("\n[ETAPA 1 de 3] Verificando o banco de dados SQLite...")
    try:
        init_db()
        print("[SUCESSO] Banco de dados 'progress.db' está pronto.")
    except Exception as e:
        print(f"[ERRO] Falha ao criar o banco de dados: {e}")
        sys.exit(1)

    # --- ETAPA 2: ÍNDICE FAISS ---
    print("\n[ETAPA 2 de 3] Verificando o índice vetorial FAISS...")
    if os.path.exists(os.path.join(INDEX_PATH, "index.faiss")):
        print("[INFO] Índice FAISS já existe. Etapa pulada.")
    else:
        print("[INFO] Índice FAISS não encontrado. Construindo agora...")
        try:
            build_index()
        except Exception as e:
            print(f"[ERRO] Falha ao construir o índice FAISS: {e}")
            sys.exit(1)
            
    # --- ETAPA 3: MODELO OLLAMA ---
    print("\n[ETAPA 3 de 3] Verificando o modelo LLM no Ollama...")
    try:
        model_list = [m.get('name') for m in ollama.list()['models']]
        if LLM_MODEL_NAME in model_list:
            print(f"[INFO] Modelo '{LLM_MODEL_NAME}' já está instalado.")
        else:
            print(f"[INFO] Modelo '{LLM_MODEL_NAME}' não encontrado. Baixando agora...")
            print("Isso pode levar vários minutos e requer conexão com a internet.")
            
            success, error_msg = run_command(['ollama', 'pull', LLM_MODEL_NAME])
            
            if success:
                print(f"[SUCESSO] Modelo '{LLM_MODEL_NAME}' baixado com sucesso.")
            else:
                print(f"[ERRO] Falha ao baixar o modelo. Verifique se o Ollama está rodando.")
                print(f"Detalhes: {error_msg}")
                sys.exit(1)
                
    except Exception as e:
        print(f"[ERRO] Não foi possível comunicar com o serviço do Ollama. Ele está rodando?")
        print(f"Detalhes: {e}")
        sys.exit(1)

    print("-" * 50)
    print("✅ Configuração concluída com sucesso! Você já pode iniciar a aplicação.")
    print("-" * 50)

if __name__ == "__main__":
    setup_application()