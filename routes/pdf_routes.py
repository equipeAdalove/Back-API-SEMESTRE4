import logging
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse
from services.pdf_service import PDFService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/process_pdf", status_code=status.HTTP_200_OK)
async def process_pdf(request: Request, file: UploadFile = File(...)):
    try:
        stream, filename = await PDFService.process_pdf(request, file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Erro inesperado no processamento do PDF")
        raise HTTPException(status_code=500, detail="Erro interno no servidor")

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
