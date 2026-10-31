from fastapi import APIRouter, Query, status

from app.models import Customer, LedgerEntry
from app.routes.dependencies import CustomerServiceDep, LedgerServiceDep
from app.schemas.common import ErrorResponse
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.schemas.ledger import LedgerEntryResponse

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
def create_customer(payload: CustomerCreate, service: CustomerServiceDep) -> Customer:
    return service.create_customer(payload)


@router.get("", response_model=list[CustomerResponse])
def list_customers(
    service: CustomerServiceDep,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[Customer]:
    return service.list_customers(skip=skip, limit=limit)


@router.get(
    "/{customer_id}", response_model=CustomerResponse, responses={404: {"model": ErrorResponse}}
)
def get_customer(customer_id: int, service: CustomerServiceDep) -> Customer:
    return service.get_customer(customer_id)


@router.get(
    "/{customer_id}/ledger",
    response_model=list[LedgerEntryResponse],
    tags=["Ledger"],
    responses={404: {"model": ErrorResponse}},
)
def get_customer_ledger(
    customer_id: int,
    service: LedgerServiceDep,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[LedgerEntry]:
    """Chronological, append-only ledger history for a customer."""
    return service.get_customer_ledger(customer_id, skip=skip, limit=limit)
