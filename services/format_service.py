import re
from typing import List, Dict

def format_many(itens: List[str]) -> List[Dict[str, str]]:
    """
    Recebe uma lista de strings e separa em partnumber e descricao_raw.
    Retorna lista de dicts com chaves: 'partnumber', 'descricao_raw'.
    
    Prioriza 'PN:'; só usa a primeira palavra se 'PN:' não existir.
    """
    resultado = []

    for item in itens:
        pn = ""
        desc = item.strip()

        match_pn = re.search(r'\bPN:\s*([^\s]+)', desc, flags=re.IGNORECASE)
        if match_pn:
            pn = match_pn.group(1).strip()
            desc = re.sub(r'\bPN:\s*[^\s]+', '', desc, flags=re.IGNORECASE).strip()
        else:
            # caso não haja "PN:", assume que o PN é a primeira palavra que não seja só número/medida
            #Provisório -> tem que trocar caso outro PDF não siga essa lógica
            match_inicio = re.match(r'^([A-Z0-9\.\-]+)\s+(.*)$', desc, flags=re.IGNORECASE)
            if match_inicio:
                pn = match_inicio.group(1).strip()
                desc = match_inicio.group(2).strip()

        resultado.append({"partnumber": pn, "descricao_raw": desc})

    print(resultado)
    return resultado
