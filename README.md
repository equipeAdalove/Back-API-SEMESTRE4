# Backend de Classificação Fiscal (FastAPI + Gemini RAG)

Este projeto implementa um **backend em FastAPI** que recebe arquivos **PDF** com descrições de componentes eletrônicos, extrai **PartNumbers e descrições reduzidas**, utiliza um modelo **Gemini (Google AI)** combinado com **RAG (Retrieval-Augmented Generation)** sobre uma base de **NCM em CSV** para sugerir a classificação fiscal, e retorna ao usuário um arquivo **Excel** contendo os resultados.

---

## 🚀 Funcionalidades

- Upload de arquivos PDF pelo frontend ou via API.
- Extração automática de PartNumbers e descrições.
- Busca inteligente na base de NCM (`ncm.csv`) via **TF-IDF + Similaridade de Cosseno**.
- Uso do **Gemini** para sugerir NCM e gerar descrição fiscal detalhada.
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
│   │   └── llm_service.py      # Integração com Gemini
│   └── models/                # Futuro uso para persistência
│── requirements.txt
│── .env
│── README.md
```

---

## ⚙️ Pré-requisitos

- Python 3.10+
- Conta no [Google AI Studio](https://aistudio.google.com/) e chave da API Gemini

---

## 📥 Instalação

1. Clone este repositório:

```bash
git clone https://github.com/seuusuario/backend-classificacao.git
cd backend
```

2. Crie e ative um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate    # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure o arquivo `.env`:

```ini
GEMINI_API_KEY=suachaveaqui
NCM_CSV_PATH=C:/csv/ncm.csv
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

Documentação automática:

- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📌 Endpoints Principais

### Upload de PDF e Download de Excel
```http
POST /api/process_pdf
Content-Type: multipart/form-data
Body: file=<seu_arquivo.pdf>
Response: Excel (.xlsx)
```

### Status da API
```http
GET /status
Response: { "status": "ok", "gemini": true, "ncm_carregado": true }
```

---

## 💻 Frontend (Opcional)

Existe um frontend simples em React que permite enviar o PDF e baixar o Excel resultante.  
Consulte a pasta `frontend/` para mais detalhes.

---

## 📜 Licença

Projeto desenvolvido para uso interno. Personalize conforme necessário.
