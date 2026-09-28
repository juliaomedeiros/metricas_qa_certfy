import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

class PostgresDB:
    def __init__(self):
        # Conexão direta com o Docker local
        db_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://qa_admin:qa_password123@localhost:5432/qametrics")
        self.engine = create_engine(db_url)
        self._create_tables()

    def _create_tables(self):
        with self.engine.connect() as conn:
            # Tabela base (agora com tipo_card)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS qa_cards (
                    id INTEGER PRIMARY KEY,
                    tipo_card TEXT,
                    titulo TEXT,
                    qa_responsavel TEXT,
                    tag_agrupada TEXT,
                    tempo_qa_pai FLOAT,
                    tempo_rework_filhos FLOAT,
                    qtd_defeitos INTEGER,
                    possui_defeito BOOLEAN,
                    card_count INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # MIGRATION AUTOMÁTICA: Tenta adicionar a coluna caso a tabela já existisse antes
            try:
                conn.execute(text("ALTER TABLE qa_cards ADD COLUMN tipo_card TEXT;"))
            except:
                pass # A coluna já existe, segue o jogo

            conn.commit()

    def upsert_data(self, df):
        if df is None or df.empty: return
        with self.engine.connect() as conn:
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO qa_cards 
                    (id, tipo_card, titulo, qa_responsavel, tag_agrupada, tempo_qa_pai, tempo_rework_filhos, qtd_defeitos, possui_defeito, card_count, last_updated)
                    VALUES (:id, :tipo_card, :titulo, :qa_responsavel, :tag_agrupada, :tempo_qa_pai, :tempo_rework_filhos, :qtd_defeitos, :possui_defeito, :card_count, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO UPDATE SET
                        tipo_card = EXCLUDED.tipo_card,
                        titulo = EXCLUDED.titulo,
                        qa_responsavel = EXCLUDED.qa_responsavel,
                        tag_agrupada = EXCLUDED.tag_agrupada,
                        tempo_qa_pai = EXCLUDED.tempo_qa_pai,
                        tempo_rework_filhos = EXCLUDED.tempo_rework_filhos,
                        qtd_defeitos = EXCLUDED.qtd_defeitos,
                        possui_defeito = EXCLUDED.possui_defeito,
                        last_updated = CURRENT_TIMESTAMP
                """), {
                    "id": row['ID'], 
                    "tipo_card": row['Tipo_Card'],
                    "titulo": row['Titulo'], 
                    "qa_responsavel": row['QA_Responsavel'],
                    "tag_agrupada": row['Tag_Agrupada'], 
                    "tempo_qa_pai": row['Tempo_QA_Pai'],
                    "tempo_rework_filhos": row['Tempo_Rework_Filhos'], 
                    "qtd_defeitos": row['Qtd_Defeitos'],
                    "possui_defeito": row['Possui_Defeito'], 
                    "card_count": row['Card_Count']
                })
            conn.commit()

    def get_all_data(self):
        # A query de consulta agora traz o tipo do card também
        query = """
            SELECT 
                id as "ID", 
                tipo_card as "Tipo_Card", 
                titulo as "Titulo", 
                qa_responsavel as "QA_Responsavel", 
                tag_agrupada as "Tag_Agrupada", 
                tempo_qa_pai as "Tempo_QA_Pai", 
                tempo_rework_filhos as "Tempo_Rework_Filhos", 
                qtd_defeitos as "Qtd_Defeitos", 
                possui_defeito as "Possui_Defeito", 
                card_count as "Card_Count" 
            FROM qa_cards
        """
        return pd.read_sql(query, self.engine)