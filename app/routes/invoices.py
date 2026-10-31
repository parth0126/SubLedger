from fastapi import APIRouter, status

from app.models import Invoice
from app.routes.dependencies import InvoiceServiceDep
from app.schemas.common import ErrorResponse
from app.schemas.invoice import InvoiceDetailResponse, InvoiceGenerate, InvoiceResponse

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post(
    "/generate",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
def generate_invoice(payload: InvoiceGenerate, service: InvoiceServiceDep) -> Invoice:
    return service.generate_invoice(payload)


@router.get(
    "/{invoice_id}", response_model=InvoiceDetailResponse, responses={404: {"model": ErrorResponse}}
)
def get_invoice(invoice_id: int, service: InvoiceServiceDep) -> Invoice:
    return service.get_invoice(invoice_id)
