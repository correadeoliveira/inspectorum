import os
import glob
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts import PromptTemplate
import time
import threading

# --- CONSTANTES DE CONFIGURAÇÃO ---
INDEX_PATH = "faiss_index_mistral"
PDF_DIRECTORY_PATH = "documentos"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
LLM_MODEL_NAME = "phi3:3.8b-mini-4k-instruct-q4_0"

# --- FUNÇÃO PRINCIPAL DE CONSTRUÇÃO DO ÍNDICE ---
def build_index():
    """
    Verifica a pasta 'documentos', carrega os PDFs,
    e cria um novo índice FAISS do zero.
    """
    print("--- Iniciando construção do índice FAISS ---")
    
    if os.path.exists(os.path.join(INDEX_PATH, "index.faiss")):
        print(f"[INFO] O índice em '{INDEX_PATH}' já existe. Construção pulada.")
        return

    if not os.path.exists(PDF_DIRECTORY_PATH) or not glob.glob(os.path.join(PDF_DIRECTORY_PATH, "*.pdf")):
        print(f"[ERRO] A pasta '{PDF_DIRECTORY_PATH}' não existe ou está vazia.")
        print("Por favor, adicione arquivos PDF para construir o índice.")
        return

    print(f"Carregando documentos da pasta '{PDF_DIRECTORY_PATH}'...")
    all_pdf_files = glob.glob(os.path.join(PDF_DIRECTORY_PATH, "*.pdf"))
    
    documents = []
    for pdf_file in all_pdf_files:
        loader = PyPDFLoader(pdf_file)
        documents.extend(loader.load())
    
    if not documents:
        print("[ERRO] Nenhum documento pôde ser carregado dos arquivos PDF.")
        return
        
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=750, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    
    print("Gerando embeddings e construindo o índice (isso pode levar alguns minutos)...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vectorstore = FAISS.from_documents(texts, embeddings)
    
    print(f"Salvando o índice em '{INDEX_PATH}'...")
    os.makedirs(INDEX_PATH, exist_ok=True)
    vectorstore.save_local(INDEX_PATH)
    
    print("--- ✅ Índice FAISS construído e salvo com sucesso! ---")


# --- BLOCO DE EXECUÇÃO PARA TESTE INTERATIVO ---
if __name__ == "__main__":
    build_index()

    if not os.path.exists(os.path.join(INDEX_PATH, "index.faiss")):
        print("\n[FALHA] O índice não foi encontrado. Encerrando o chat de teste.")
    else:
        print("\nCarregando o índice e o modelo para o chat de teste...")
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        vector_store = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        llm = OllamaLLM(model=LLM_MODEL_NAME)

        # --- PROMPT DE RAG COMPLETO E RESTAURADO ---
        main_chain_prompt_template = """
REGRA MAIS IMPORTANTE: NÃO USE NENHUM CONHECIMENTO EXTERNO. Responda APENAS com a informação contida no CONTEXTO fornecido abaixo.

Você é um assistente especialista na Doutrina Católica. Sua tarefa é responder à pergunta do usuário utilizando estritamente o contexto fornecido.
O contexto é uma coleção de trechos de vários documentos, cada um com sua fonte e número de página.

Regras:
1. Sintetize a informação dos diferentes trechos em uma resposta coesa e pastoral.
2. Ao compor sua resposta, sempre que utilizar uma informação de um trecho, cite a fonte e a página correspondente imediatamente após a frase, no formato (nome_do_arquivo.pdf, pág. X).
3. Se os trechos de contexto não contêm informação suficiente para responder à pergunta, responda EXATAMENTE com a frase: 'A informação necessária para responder a esta pergunta não foi encontrada nos documentos fornecidos.' Não tente inventar uma resposta.

--- CONTEXTO ---
{summaries}
---
Pergunta: {question}
Resposta Detalhada com Citações:
"""
        main_chain_prompt = PromptTemplate.from_template(main_chain_prompt_template)
        document_prompt = PromptTemplate(input_variables=["page_content", "metadata"], template="Fonte: {source}, Página: {page}\nConteúdo: {page_content}")
        chain_type_kwargs = {"prompt": main_chain_prompt, "document_prompt": document_prompt}
        retriever = vector_store.as_retriever(search_kwargs={"k": 4})
        
        qa_chain = RetrievalQAWithSourcesChain.from_chain_type(
            llm,
            retriever=retriever,
            chain_type_kwargs=chain_type_kwargs,
            return_source_documents=True
        )

        print("\n✅ Sistema RAG pronto para teste. Digite 'sair' para terminar.")
        
        while True:
            question = input("\nPergunta: ")
            if question.lower() == 'sair':
                break
            
            start_time = time.perf_counter()
            result = qa_chain.invoke({"question": question})
            end_time = time.perf_counter()

            print("\n--- RESPOSTA ---")
            print(result["answer"].strip())
            
            print("\n--- FONTES UTILIZADAS ---")
            print(result["sources"].strip())
            print(f"\n[Tempo de resposta: {end_time - start_time:.2f} segundos]")