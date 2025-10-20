# pyright: reportCallIssue=false
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    db_url:str 
    ollama_url:str
    ollama_model:str
    ncm_csv_path:str
    top_k:int

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings()

