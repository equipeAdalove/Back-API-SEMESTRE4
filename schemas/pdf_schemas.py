from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ExtractedItem(BaseModel):
    partnumber: str
    descricao_raw: str
    ncm: Optional[str] = None  # <- NOVO CAMPO OPCIONAL


class ExtractionResponse(BaseModel):
    transacao_id: int
    items: List[ExtractedItem]


class ProcessRequest(BaseModel):
    items: List[ExtractedItem]


class FinalItem(BaseModel):
    partnumber: str
    fabricante: str
    localizacao: str
    ncm: str
    descricao: str
    is_new_manufacturer: bool


class ExcelRequest(BaseModel):
    items: List[FinalItem]


class TransacaoInfo(BaseModel):
    id: int
    nome: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RenameRequest(BaseModel):
    nome: str


class TransacaoDetailResponse(BaseModel):
    transacao_id: int
    processed_items: List[FinalItem] = []
    pending_items: List[ExtractedItem] = []

    class Config:
        from_attributes = True