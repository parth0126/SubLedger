"""Dependency-injection wiring: each request gets one session shared by all its services."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.repositories import (
    CustomerRepository,
    InvoiceRepository,
    LedgerRepository,
    PaymentAttemptRepository,
    PlanRepository,
    SubscriptionRepository,
)
from app.services import (
    CustomerService,
    InvoiceService,
    LedgerService,
    PaymentService,
    PlanService,
    SubscriptionService,
)

DbSession = Annotated[Session, Depends(get_db)]


def get_plan_service(session: DbSession) -> PlanService:
    return PlanService(session, PlanRepository(session))


def get_customer_service(session: DbSession) -> CustomerService:
    return CustomerService(session, CustomerRepository(session))


def get_subscription_service(session: DbSession) -> SubscriptionService:
    return SubscriptionService(
        session,
        SubscriptionRepository(session),
        CustomerRepository(session),
        PlanRepository(session),
    )


def get_ledger_service(session: DbSession) -> LedgerService:
    return LedgerService(LedgerRepository(session), CustomerRepository(session))


def get_invoice_service(
    session: DbSession, ledger: Annotated[LedgerService, Depends(get_ledger_service)]
) -> InvoiceService:
    return InvoiceService(
        session,
        InvoiceRepository(session),
        SubscriptionRepository(session),
        ledger,
        due_days=get_settings().invoice_due_days,
    )


def get_payment_service(
    session: DbSession, ledger: Annotated[LedgerService, Depends(get_ledger_service)]
) -> PaymentService:
    return PaymentService(session, InvoiceRepository(session), PaymentAttemptRepository(session), ledger)


PlanServiceDep = Annotated[PlanService, Depends(get_plan_service)]
CustomerServiceDep = Annotated[CustomerService, Depends(get_customer_service)]
SubscriptionServiceDep = Annotated[SubscriptionService, Depends(get_subscription_service)]
LedgerServiceDep = Annotated[LedgerService, Depends(get_ledger_service)]
InvoiceServiceDep = Annotated[InvoiceService, Depends(get_invoice_service)]
PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
