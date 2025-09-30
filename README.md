<p align="center">
  <img src="frontend/public/logo.png" alt="Logo do Inspectorum" width="150">
</p>

# Inspectorum: Exame de Consciência com IA

Inspectorum é uma aplicação de desktop local e privada para a prática do exame de consciência católico. A ferramenta guia o usuário através de uma série de perguntas baseadas nos Dez Mandamentos, permitindo uma reflexão estruturada. Ao final, utiliza modelos de linguagem locais (LLMs) para gerar uma análise espiritual personalizada sobre os pontos que necessitam de mais atenção, além de alimentar um painel de progresso para acompanhamento diário e semanal.

O projeto também inclui um assistente de doutrina que responde a perguntas do usuário com base em uma coleção de documentos fornecidos (RAG), garantindo respostas fiéis e contextualizadas.

Toda a operação ocorre localmente na máquina do usuário, garantindo 100% de privacidade.

## ✨ Funcionalidades

* **Exame de Consciência Guiado:** Um chatbot que apresenta perguntas de forma sequencial.
* **Análise por IA:** Após o exame, uma IA local analisa as respostas e gera uma reflexão pastoral.
* **Painel de Progresso:** Gráficos e estatísticas que monitoram a evolução espiritual do usuário.
* **Assistente de Doutrina (RAG):** Um modo de chat pós-análise que permite ao usuário tirar dúvidas sobre a fé.
* **Privacidade Total:** Todos os dados, LLMs e processos rodam localmente.

## 🛠️ Stack Tecnológica

* **Frontend:** Next.js (React), TypeScript, Tailwind CSS, shadcn/ui.
* **Backend:** Python, Flask, LangChain.
* **Modelos de Linguagem:** Ollama (rodando `phi3:3.8b-mini-4k-instruct-q4_0` localmente).
* **Banco de Dados Vetorial:** FAISS para o sistema RAG.
* **Banco de Dados de Progresso:** SQLite.
* **Orquestrador:** Node.js, pnpm e `concurrently`.

## 🚀 Guia de Instalação (Do Zero)

Siga estes passos para configurar o projeto em uma nova máquina.

### 1. Pré-requisitos

Certifique-se de que os seguintes softwares estão instalados:

* **Git:** Para clonar o repositório.
* **Python:** Versão 3.9 ou superior.
* **Node.js:** Versão 18 ou superior.
* **pnpm:** Após instalar o Node.js, instale o pnpm globalmente:
    ```bash
    npm install -g pnpm
    ```
* **Ollama:** Baixe e instale o aplicativo do [Ollama](https://ollama.com/). Após a instalação, **inicie o aplicativo** para que ele fique rodando em segundo plano.

### 2. Instalação do Projeto

1.  **Clone o Repositório:**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd projeto-exame-consciencia
    ```

2.  **Instale as Dependências do Backend (Python):**
    ```bash
    # Entre na pasta do backend
    cd backend
    # Crie o ambiente virtual
    python -m venv venv
    # Ative o ambiente (use o comando para o seu sistema operacional)
    # No Windows:
    .\venv\Scripts\activate
    # No macOS/Linux:
    source venv/bin/activate
    # Instale os pacotes
    pip install -r requirements.txt
    # Volte para a raiz do projeto
    cd ..
    ```

3.  **Instale as Dependências do Frontend (Node.js):**
    ```bash
    # Na pasta raiz, instale as dependências da raiz
    pnpm install
    # Instale as dependências do subprojeto frontend
    pnpm --prefix frontend install
    ```

4.  **Configure o Conteúdo (RAG):**
    * Dentro da pasta `backend/`, localize a subpasta `documentos/`.
    * **Coloque seus arquivos PDF** de referência dentro desta pasta. Sem eles, o "Assistente de Doutrina" não terá base de conhecimento.

5.  **Execute o Script de Setup Automatizado:**
    * Este script irá criar o banco de dados, construir o índice dos seus PDFs e baixar o modelo de IA.
    * Certifique-se de que o ambiente virtual do backend (`venv`) esteja ativo.
    * Na pasta **raiz** do projeto, execute:
        ```bash
        python backend/setup.py
        ```

### 3. Como Rodar a Aplicação (Uso Diário)

Após a configuração inicial ser concluída, o processo para iniciar o aplicativo é muito simples:

1.  **Verifique se o Ollama está rodando** em segundo plano (ícone na barra de tarefas).
2.  Abra um terminal na **pasta raiz** do projeto.
3.  **Ative o ambiente virtual do backend**:
    * **No Windows:** `.\backend\venv\Scripts\activate`
    * **No macOS/Linux:** `source backend/venv/bin/activate`
4.  Execute o comando principal:
    ```bash
    pnpm run dev
    ```
O backend e o frontend serão iniciados, e seu navegador abrirá automaticamente em `http://localhost:3000`.

## ⚙️ Funcionamento Técnico

* **Backend (Flask):** Serve uma API local que gerencia o estado do exame, executa as duas análises de LLM (a textual e a de classificação), salva os dados no SQLite e processa as perguntas para o sistema RAG.
* **Frontend (Next.js):** Constrói a interface do usuário, incluindo o chatbot e o dashboard, e se comunica com a API Flask para buscar e enviar dados.
* **Fluxo de Dados:** O exame começa lendo o `perguntas.yaml`. As respostas são salvas em `respostas.yaml`. A análise de progresso é salva em `progress.db`, que por sua vez alimenta o dashboard. O chat RAG consulta o índice `faiss_index_mistral` para responder às perguntas.
  
## 🤝 Como Contribuir

Consulte o nosso guia de contribuição em [`CONTRIBUTING.md`](./CONTRIBUTING.md) para saber como você pode ajudar a melhorar o Inspectorum.

## 📄 Licença

Este projeto é licenciado sob a Licença MIT. Veja o arquivo [`LICENSE`](./LICENSE) para mais detalhes.
