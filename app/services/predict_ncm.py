import joblib
import logging
from pathlib import Path
import re
import unidecode

logger = logging.getLogger(__name__)

def limpar_descricao(descricao: str) -> str:
    descricao = re.sub(r'PN:\s*\S+', '', descricao, flags=re.IGNORECASE).strip()
    descricao = descricao.lower()
    descricao = unidecode.unidecode(descricao)
    descricao = re.sub(r'[^a-z0-9\s]', '', descricao)
    return descricao.strip()

class PredictNCMService:
    def __init__(self, model_path: str):
        "Carrega o modelo de Machine Learning"
        full_model_path = Path.cwd() / model_path
        logger.info("Carrega modelo: %s", full_model_path)
        try:
            self.model = joblib.load(full_model_path)
        except FileNotFoundError:
            logger.error("Arquivo do modelo não encontrado em: %s", full_model_path)
            raise

    def suggest_ncm(self, description: str) -> str:
        "Recebe uma descrição limpa e manda sugestão de NCM."
        if not hasattr(self, 'model'):
            raise RuntimeError("O modelo não foi carregado corretamente.")
        
        cleaned_description = limpar_descricao(description)
        prediction = self.model.predict([cleaned_description])
        return str(prediction[0])