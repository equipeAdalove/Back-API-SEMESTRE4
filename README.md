# Backend de Classificação Fiscal (FastAPI + Qwen3 RAG)

Este projeto implementa um **backend em FastAPI** que recebe arquivos **PDF** com descrições de componentes eletrônicos, extrai **PartNumbers e descrições reduzidas**, utiliza o modelo **Qwen3** via **Ollama** combinado com **RAG (Retrieval-Augmented Generation)** sobre uma base de **NCM em CSV** para sugerir a classificação fiscal, e retorna ao usuário um arquivo **Excel** contendo os resultados.

---

## 🚀 Funcionalidades

- Upload de arquivos PDF via API ou frontend.
- Extração automática de PartNumbers e descrições.
- Busca inteligente na base de NCM (`ncm.csv`) usando **TF-IDF + Similaridade de Cosseno**.
- Sugestão de NCM via **Qwen3 (Ollama)** e geração de descrição fiscal detalhada.
- Retorno de arquivo **Excel (.xlsx)** com colunas:
  - `PartNumber`
  - `Descrição Reduzida`
  - `Descrição Fiscal`
  - `NCM Sugerido`

---

## 📂 Estrutura do Projeto

```
├── app
│   ├── core
│   │   └── config.py
│   └── main.py
├── auth
├── database
│   └── database.py
├── models
│   └── models.py
├── routes
│   ├── pdf_routes.py
│   └── test_routes.py
├── schemas
├── services
│   ├── extract_service.py
│   ├── format_service.py
│   ├── normalize_service.py
│   ├── pdf_service.py
│   ├── rag_service.py
│   └── scraper_service.py
├── .env-example
├── .gitignore
├── README.md
├── config.py
├── fabricantes.txt
└── requirements.txt
```

---

## ⚙️ Pré-requisitos

- Python 3.10+
- [Ollama](https://ollama.com/) instalado com modelo **qwen3**
- PostgreSQL instalado (ou outro banco compatível)

---

## 📥 Instalação

1. Clone o repositório:

```bash
git clone https://github.com/equipeAdalove/Back-API-SEMESTRE4.git
cd Back-API-SEMESTRE4/backend
```

2. Crie e ative o ambiente virtual:

```bash
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate ou source venv/Scripts/activate
```
Obs: No Windows, esse comando pode variar de uma CLI para outra, saiba apenas que deve ser ativado o script 'activate' que fica dentro de venv/Scripts

3. Instale dependências (já dentro do ambiente virtual):

```bash
pip install -r requirements.txt
```

4. Configure o arquivo `.env` (copie de `.env-example`):

```ini
DB_URL=postgresql://usuario:senha@localhost:5432/api4ads
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen3:1.7b
NCM_CSV_PATH=C:/csv/ncm.csv
TOP_K=5
```

⚠️ Observações:

- **Banco de dados:** crie o banco **antes** de rodar o backend. Por padrão, usamos `api4ads`, mas você pode escolher outro nome.
- **CSV de NCM:** deve conter colunas `ncm` e `descricao`, codificação **latin1**, separador `,`.
- **Migrations ainda não implementadas:** como ainda não implementamos as migrations, caso exista qualquer modificação no banco (adição de coluna, mudança de tipo, etc.), devemos excluir o banco de dados atual (ou todas as tabelas - caso exclua o banco, lembre-se de recriá-lo), e rodar novamente o projeto para criação automática das novas tabelas. 

---

## ▶️ Executando

1. Certifique-se de que o banco existe e o `.env` está configurado.
2. Inicie o servidor FastAPI:

```bash
uvicorn app.main:app --reload
```

3. As tabelas serão criadas automaticamente na primeira execução.

**API disponível em:**

```
http://localhost:8000
```

---

## 📄 Documentação da API

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Redoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 💡 Dicas

- Sempre configure `.env` antes de rodar o backend.
- Para mudar o banco, atualize `DB_URL` e crie o banco correspondente.
- Certifique-se de que o Ollama está rodando e o modelo `qwen3` está disponível.