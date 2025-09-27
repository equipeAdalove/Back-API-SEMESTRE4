import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.post("/test_pdf")
async def test_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um arquivo PDF válido.")

    # Apenas lê os bytes para validar que o arquivo chegou
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")

    # Cria um DataFrame de teste
    df = pd.DataFrame(
        {
            "partnumber": ["TESTE123", "TESTE456"],
            "fabricante": ["Fabricante X", "Fabricante Y"],
            "localizacao": ["Brasil", "EUA"],
            "ncm": ["1234.56.78", "8765.43.21"],
            "descricao": ["Produto fictício 1", "Produto fictício 2"],
        }
    )

    # Gera um Excel em memória
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="resultado_teste")
    stream.seek(0)

    filename = file.filename.rsplit(".", 1)[0] + "_TESTE.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
