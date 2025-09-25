import pandas as pd
import logging
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from .normalize_service import limpar_texto

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, ncm_csv_path: str):
        df = pd.read_csv(ncm_csv_path, encoding="utf-8")
        df.columns = [c.lower() for c in df.columns]
        if not all(c in df.columns for c in ["ncm", "descricao", "descricao_longa"]):
            raise ValueError("CSV precisa ter colunas: ncm, descricao, descricao_longa")

        df["ncm"] = df["ncm"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(8)
        df["descricao_clean"] = df["descricao"].astype(str).apply(limpar_texto)
        self.df_ncm = df

        # modelo embeddings
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        logger.info("Gerando embeddings NCM... isso pode demorar alguns segundos...")
        self.embeddings = self.model.encode(self.df_ncm["descricao_clean"].tolist(), convert_to_numpy=True)

    def find_top_ncm(self, query_text: str, top_k=5):
        q_vec = self.model.encode([limpar_texto(query_text)], convert_to_numpy=True)
        sims = cosine_similarity(q_vec, self.embeddings).flatten()
        top_indices = sims.argsort()[-top_k:][::-1]
        return self.df_ncm.iloc[top_indices].to_dict(orient="records")
