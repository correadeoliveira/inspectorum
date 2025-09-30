import sqlite3

# ANTES: DATABASE_NAME = 'backend/progress.db'
# DEPOIS (CORRETO):
DATABASE_NAME = 'progress.db'

def init_db():
    """
    Inicializa o banco de dados e cria a tabela 'progress' se ela não existir.
    """
    try:
        # Agora ele vai criar/acessar o DB dentro da pasta 'backend', que é o correto
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # Cria a tabela para armazenar o resultado de cada pergunta
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_date TEXT NOT NULL,
                question_id TEXT NOT NULL,
                is_sin INTEGER NOT NULL CHECK(is_sin IN (0, 1))
            )
        ''')

        conn.commit()
        conn.close()
        print(f"Banco de dados '{DATABASE_NAME}' inicializado com sucesso.")
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")

if __name__ == '__main__':
    init_db()