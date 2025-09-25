import pdfplumber
import io
import re
from typing import List

def extract_lines_from_pdf_bytes(pdf_bytes: bytes) -> List[str]:
    """
    Recebe bytes de um PDF e retorna as linhas de itens extraídas.
    """
    itens = []
    pdf_buffer = io.BytesIO(pdf_bytes) 

    with pdfplumber.open(pdf_buffer) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if not texto:
                continue
            # Regex para capturar apenas a descrição do item
            pattern_itens = r'^\d{2}\s+\d{6,}\s*-\s*(.*?)(?:\s\d{3,4}\s\d{2}/\d{2}/\d{2,4}\s[\d.,]+\s[\d.,]+\s[\d.,]+)?$'
            for linha in texto.splitlines():
                match = re.match(pattern_itens, linha.strip())
                if match:
                    itens.append(match.group(1).strip())
    print("#######################EXTRACT SERVICE")
    for item in itens:
        print(item)
    return itens