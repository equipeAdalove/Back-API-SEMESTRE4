import io
import logging
import re
from typing import List, Dict, Optional, Tuple

import pdfplumber

logger = logging.getLogger(__name__)


# ============================================================
# Leitura e detecção de tipo
# ============================================================

def _read_pdf_text_from_bytes(pdf_bytes: bytes) -> str:
    """
    Lê o PDF a partir de bytes e retorna o texto concatenado de todas as páginas.
    """
    texto: List[str] = []
    pdf_buffer = io.BytesIO(pdf_bytes)

    with pdfplumber.open(pdf_buffer) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texto.append(t)

    return "\n".join(texto).strip()


def _detect_pdf_type_from_text(conteudo: str) -> str:
    """
    Detecta o tipo do PDF com base no texto completo.
    Retorna: 'avnet', 'mouser', 'xworks' ou 'desconhecido'.
    """
    conteudo_lower = conteudo.lower()

    if "avnet" in conteudo_lower:
        return "avnet"
    if "mouser" in conteudo_lower:
        return "mouser"
    if "xworks" in conteudo_lower or "x works" in conteudo_lower:
        return "xworks"
    return "desconhecido"


# ============================================================
# Lógica AVNET (extração de linhas + format_many embutido)
# ============================================================

def _extract_avnet_lines_from_pdf_bytes(pdf_bytes: bytes) -> List[str]:
    """
    Recebe bytes de um PDF e retorna as linhas de itens extraídas (formato bruto AVNET).
    """
    itens: List[str] = []
    pdf_buffer = io.BytesIO(pdf_bytes)

    with pdfplumber.open(pdf_buffer) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if not texto:
                continue

            # Regex para capturar apenas a descrição do item (seu padrão atual)
            pattern_itens = (
                r'^\d{2}\s+\d{6,}\s*-\s*(.*?)(?:\s\d{3,4}\s\d{2}/\d{2}/\d{2,4}\s'
                r'[\d.,]+\s[\d.,]+\s[\d.,]+)?$'
            )
            for linha in texto.splitlines():
                match = re.match(pattern_itens, linha.strip())
                if match:
                    linha_item = match.group(1).strip()
                    logger.debug(f"[AVNET] Linha extraída: {linha_item}")
                    itens.append(linha_item)

    return itens


def _format_many_avnet(itens: List[str]) -> List[Dict[str, str]]:

    resultado: List[Dict[str, str]] = []

    for item in itens:
        pn = ""
        desc = item.strip()

        # Prioriza "PN:"
        match_pn = re.search(r"\bPN:\s*([^\s]+)", desc, flags=re.IGNORECASE)
        if match_pn:
            pn = match_pn.group(1).strip()
            desc = re.sub(
                r"\bPN:\s*[^\s]+",
                "",
                desc,
                flags=re.IGNORECASE,
            ).strip()
        else:
            # Se não houver "PN:", assume que o PN é a primeira palavra "decente"
            match_inicio = re.match(
                r"^([A-Z0-9\.\-]+)\s+(.*)$",
                desc,
                flags=re.IGNORECASE,
            )
            if match_inicio:
                pn = match_inicio.group(1).strip()
                desc = match_inicio.group(2).strip()

        resultado.append({"partnumber": pn, "descricao_raw": desc})

    logger.debug(f"[AVNET] Itens formatados: {resultado}")
    return resultado


# ============================================================
# Lógica MOUSER
# ============================================================

def _limpar_partnumber_mouser(partnumber_raw: str) -> str:
    """
    Remove sufixos como #PBF, #TR, etc. do partnumber.
    Ex.: 584-LTC3625EDE#PBF -> 584-LTC3625EDE
    """
    return re.sub(r"#.*$", "", partnumber_raw)


def _extrair_itens_mouser(conteudo: str) -> List[Dict[str, str]]:
    """
    A partir do texto de uma fatura Mouser, extrai uma lista de itens:
    [ {partnumber, descricao, ncm}, ... ]
    """
    linhas = conteudo.splitlines()
    itens: List[Dict[str, str]] = []
    i = 0

    # padrão do início de item: "1 871-B32932A3224K189 700 700"
    padrao_item = re.compile(r"^(\d+)\s+(\d{3}-\S+)")

    while i < len(linhas):
        linha = linhas[i].strip()

        m = padrao_item.match(linha)
        if m:
            partnumber_raw = m.group(2)
            partnumber = _limpar_partnumber_mouser(partnumber_raw)

            descricao = ""
            ncm = ""

            j = i + 1
            while j < len(linhas):
                l = linhas[j].strip()

                # Se encontrarmos outro item, paramos o lookahead
                if padrao_item.match(l):
                    break

                # Linha com NCM:
                # "BR NCM:85322590 ECCN:EAR99 COO:CN"
                if "NCM:" in l:
                    n = re.search(r"NCM:(\d{8})", l)
                    if n:
                        ncm = n.group(1)
                    j += 1
                    break

                # Se tiver só US HTS (sem NCM), consideramos fim do bloco do item
                if "US HTS:" in l and "NCM:" not in l:
                    j += 1
                    break

                # Linha de descrição em português (sua lógica atual)
                if (
                    descricao == ""
                    and "/" in l
                    and "Mouser Part Number" not in l
                    and "Item-Cliente" not in l
                    and "Customer/MFG" not in l
                    and "MFG Part No" not in l
                    and "Line No." not in l
                    and "Quantity" not in l
                    and "Ordered Shipped Pending" not in l
                    and "Price(USD)" not in l
                    and "NCM:" not in l
                    and "US HTS:" not in l
                ):
                    partes = l.split("/")
                    esquerdo = partes[0].strip()
                    direito = partes[-1].strip()

                    # Evita linhas onde o lado esquerdo é só código numérico
                    if not re.fullmatch(r"\d+", esquerdo):
                        desc_bruta = direito
                        desc_bruta = re.sub(r"\s+", " ", desc_bruta)
                        descricao = desc_bruta

                j += 1

            itens.append(
                {
                    "partnumber": partnumber,
                    "descricao": descricao,
                    "ncm": ncm,
                }
            )
            i = j
        else:
            i += 1

    return itens


# ============================================================
# Lógica XWORKS
# ============================================================

def _limpar_descricao_xworks(desc: str) -> str:
    # remover qualquer coisa entre parenteses
    desc = re.sub(r"\([^)]*\)", "", desc)
    # remover sinais indesejados
    desc = re.sub(r"[-~<>]", " ", desc)
    # reduzir múltiplos espaços
    desc = " ".join(desc.split())
    return desc.strip()


def _extrair_partnumbers_xworks(texto: str) -> List[Tuple[str, str]]:
    """
    A partir do texto completo XWORKS, extrai (partnumber, descricao).
    """
    padrao = r"PN:\s*([A-Za-z0-9\-\_]+)\s+DESC[:\-]?\s*(.*?)(?=PN:|$)"

    matches = re.findall(padrao, texto, flags=re.IGNORECASE | re.DOTALL)
    resultado: List[Tuple[str, str]] = []

    for pn, desc in matches:
        desc = desc.strip()

        # cortar tudo depois de "MFR:"
        desc = re.split(r"\bMFR:", desc, flags=re.IGNORECASE)[0].strip()

        # limpar sinais e parenteses
        desc = _limpar_descricao_xworks(desc)

        # limitar para 12 palavras
        palavras = desc.split()
        if len(palavras) > 12:
            desc = " ".join(palavras[:12])

        resultado.append((pn.strip(), desc.strip()))

    return resultado


# ============================================================
# Orquestrador
# ============================================================

def extract_items_from_pdf_bytes(pdf_bytes: bytes) -> List[Dict[str, Optional[str]]]:
    """
    Ponto único para o workflow usar.

    - Lê o PDF a partir de bytes;
    - Detecta o tipo (avnet, mouser, xworks, desconhecido);
    - Usa o extrator adequado;
    - Retorna SEMPRE uma lista de dicts:
      { "partnumber": str, "descricao_raw": str, "ncm": Optional[str] }
    """
    conteudo = _read_pdf_text_from_bytes(pdf_bytes)
    tipo = _detect_pdf_type_from_text(conteudo)

    logger.info(f"Tipo de PDF detectado: {tipo}")

    # MOUSER: já extrai partnumber + descrição + NCM
    if tipo == "mouser":
        itens_mouser = _extrair_itens_mouser(conteudo)
        return [
            {
                "partnumber": item["partnumber"],
                "descricao_raw": item["descricao"],
                "ncm": item.get("ncm") or None,
            }
            for item in itens_mouser
        ]

    # XWORKS: extrai partnumber + descrição curta, sem NCM
    if tipo == "xworks":
        pn_desc_list = _extrair_partnumbers_xworks(conteudo)
        return [
            {
                "partnumber": pn,
                "descricao_raw": desc,
                "ncm": None,
            }
            for pn, desc in pn_desc_list
        ]

    # AVNET / DESCONHECIDO: usa leitura de linhas + format_many interno
    linhas_avnet = _extract_avnet_lines_from_pdf_bytes(pdf_bytes)
    itens_formatados = _format_many_avnet(linhas_avnet)

    return [
        {
            "partnumber": item["partnumber"],
            "descricao_raw": item["descricao_raw"],
            "ncm": None,
        }
        for item in itens_formatados
    ]
