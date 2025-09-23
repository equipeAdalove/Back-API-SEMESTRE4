# Backend de Classificação Fiscal (FastAPI + Qwen3 RAG)

Este projeto implementa um **backend em FastAPI** que recebe arquivos **PDF** com descrições de componentes eletrônicos, extrai **PartNumbers e descrições reduzidas**, utiliza o modelo **Qwen3** via **Ollama** combinado com **RAG (Retrieval-Augmented Generation)** sobre uma base de **NCM em CSV** para sugerir a classificação fiscal, e retorna ao usuário um arquivo **Excel** contendo os resultados.

---

## 🚀 Funcionalidades

- Upload de arquivos PDF pelo frontend ou via API.
- Extração automática de PartNumbers e descrições.
- Busca inteligente na base de NCM (`ncm.csv`) via **TF-IDF + Similaridade de Cosseno**.
- Uso do **Qwen3 (Ollama)** para sugerir NCM e gerar descrição fiscal detalhada.
- Retorno de um arquivo **Excel (.xlsx)** com as colunas:
  - `PartNumber`
  - `Descrição Reduzida`
  - `Descrição Fiscal`
  - `NCM Sugerido`
- Base de NCM carregada **em cache** para melhor performance.

---

## 📂 Estrutura do Projeto

```
backend/
│── app/
│   ├── main.py                # Ponto de entrada FastAPI
│   ├── routes/
│   │   └── process_pdf.py     # Rotas da API
│   ├── services/
│   │   ├── pipeline_service.py # Orquestração do processo
│   │   ├── pdf_service.py      # Extração de texto do PDF
│   │   ├── rag_service.py      # Busca de NCM (RAG)
│   │   └── llm_service.py      # Integração com Qwen3 (Ollama)
│   └── models/                # Futuro uso para persistência
│── requirements.txt
│── .env
│── README.md
```

---

## ⚙️ Pré-requisitos

- Python 3.10+
- [Ollama](https://ollama.com/) instalado e modelo **qwen3** disponível

---

## 📥 Instalação

1. Clone este repositório:

```bash
git clone https://github.com/equipeAdalove/Back-API-SEMESTRE4.git
cd Back-API-SEMESTRE4/backend
```

2. Crie e ative um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate ou source venv/Scripts/activate  # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure o arquivo `.env`:

```ini
NCM_CSV_PATH=[caminho do csv]
OLLAMA_MODEL="qwen3:1.7b"
OLLAMA_URL=http://localhost:11434/api/generate

```

⚠️ O arquivo `ncm.csv` deve conter pelo menos as colunas:

- `ncm`
- `descricao`

Codificação: **latin1**  
Separador: **, (vírgula)**

---

## ▶️ Executando

Inicie o servidor FastAPI:

```bash
uvicorn main:app --reload
```

A API estará disponível em:

```
http://localhost:8000
```

## 📄 Documentação da API

O FastAPI gera documentação automática:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)  
  Interface interativa para testar endpoints.

- **Redoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)  
  Documentação detalhada da API.
