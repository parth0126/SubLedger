from fastapi import APIRouter, status

from app.routes.dependencies import PaymentServiceDep
from app.schemas.common import ErrorResponse
from app.schemas.payment import PaymentRecord, PaymentRecordResponse
from app.services import PaymentResult

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/record",
    response_model=PaymentRecordResponse,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def record_payment(payload: PaymentRecord, service: PaymentServiceDep) -> PaymentResult:
    """Record a successful or failed payment attempt. Both outcomes are persisted and
    ledgered; only successful attempts change the invoice balance."""
    return service.record_payment(payload)
