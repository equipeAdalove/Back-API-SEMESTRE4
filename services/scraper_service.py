import re
from collections import Counter
from ddgs import DDGS

# Certifique-se de que o arquivo 'fabricantes.txt' está na raiz do seu projeto (Back-API-SEMESTRE4/).
FABRICANTES_TXT_PATH = "fabricantes.txt"

def carregar_fabricantes_com_variacoes(caminho_txt: str) -> dict[str, list[str]]:
    """
    Carrega fabricantes do arquivo de texto e cria um dicionário com suas variações.
    """
    fabricantes_map = {}
    try:
        with open(caminho_txt, "r", encoding="utf-8") as f:
            for linha in f:
                nome_completo = linha.strip()
                if not nome_completo:
                    continue
                
                nome_principal = nome_completo.split('/')[0].strip()
                
                if nome_principal not in fabricantes_map:
                    fabricantes_map[nome_principal] = []
                
                fabricantes_map[nome_principal].append(nome_completo)
    except FileNotFoundError:
        print(f"ERRO: O arquivo de fabricantes '{caminho_txt}' não foi encontrado.")
        return None
            
    return fabricantes_map

def buscar_fabricante_com_pontuacao(part_number: str, fabricantes_map: dict[str, list[str]]) -> str | None:
    """
    Busca por um part number no DuckDuckGo e retorna o fabricante conhecido com a maior
    quantidade de menções nos resultados da busca.
    """
    if not part_number:
        return None
        
    query = f'"{part_number}" manufacturer datasheet'
    ocorrencias = Counter()

    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(query, max_results=10))
            if not resultados:
                return None

            texto_completo_busca = " ".join([r.get("title", "") + " " + r.get("body", "") for r in resultados])

            for nome_principal, variacoes in fabricantes_map.items():
                for variacao in variacoes:
                    padrao = r"\b" + re.escape(variacao) + r"\b"
                    if re.search(padrao, texto_completo_busca, re.IGNORECASE):
                        ocorrencias[nome_principal] += 1
    
    except Exception as e:
        print(f"[ERRO DDGS - Fabricante] Falha ao buscar: {e}")
        return None

    if not ocorrencias:
        return None

    return ocorrencias.most_common(1)[0][0]

def extrair_cidade_pais(texto_endereco: str) -> str | None:
    """
    Usa RegEx para extrair o padrão 'Cidade, País' de um bloco de texto.
    """
    if not texto_endereco:
        return None
    padrao = r"([A-Z][a-zA-Z\s-]+,\s*[A-Z][a-zA-Z\s\.-]+)"
    matches = re.findall(padrao, texto_endereco)
    return matches[-1].strip() if matches else None

def buscar_cidade_pais_com_ddg(company_name: str) -> str | None:
    """
    Busca o endereço e extrai a cidade/país.
    """
    if not company_name:
        return None

    query = f"{company_name} headquarters address"
    
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(query, max_results=5))
            if not resultados:
                return None
            
            texto_enderecos = " ".join([r.get('body', '') for r in resultados])
            return extrair_cidade_pais(texto_enderecos)
    except Exception as e:
        print(f"[ERRO DDGS - Endereço] Falha ao buscar: {e}")
        return None

# --- Função Orquestradora para ser chamada pela Rota ---
def find_manufacturer_and_location(part_number: str):
    """
    Orquestra a busca por fabricante e, em seguida, por sua localização.
    """
    print(f"Iniciando busca de fabricante para o PN: {part_number}")
    fabricantes = carregar_fabricantes_com_variacoes(FABRICANTES_TXT_PATH)
    if not fabricantes:
        return {"fabricante": "Arquivo 'fabricantes.txt' não encontrado", "localizacao": ""}

    fabricante_encontrado = buscar_fabricante_com_pontuacao(part_number, fabricantes)
    
    if not fabricante_encontrado:
        return {"fabricante": "Não identificado", "localizacao": ""}
        
    localizacao = buscar_cidade_pais_com_ddg(fabricante_encontrado)

    return {
        "fabricante": fabricante_encontrado,
        "localizacao": localizacao if localizacao else "Não encontrada"
    }