import re, unidecode

STOPWORDS_PT = set([...])  # mesmo set do seu código

def clean_text(text: str) -> str:
    text = str(text).lower()
    text = unidecode.unidecode(text)
    text = re.sub(r"[^\w\s]", " ", text)
    tokens = [w for w in text.split() if w not in STOPWORDS_PT]
    return " ".join(tokens).strip()

def split_partnumber_and_description(item_line: str):
    pn = ""
    descricao = item_line
    match_pn = re.search(r'PN:([^\s]+)', item_line, flags=re.IGNORECASE)
    if match_pn:
        pn = match_pn.group(1).strip()
        descricao = re.sub(r'PN:[^\s]+', '', item_line, flags=re.IGNORECASE).strip()
    else:
        match_inicio = re.match(r'^([A-Z0-9\.\-]+)\s+(.*)$', item_line)
        if match_inicio:
            pn = match_inicio.group(1).strip()
            descricao = match_inicio.group(2).strip()
    return pn, descricao
