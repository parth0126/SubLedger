from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.db.session import transaction
from app.models import Customer
from app.repositories import CustomerRepository
from app.schemas.customer import CustomerCreate


class CustomerService:
    """Manages customers and guarantees email uniqueness (case-insensitive)."""

    def __init__(self, session: Session, customers: CustomerRepository) -> None:
        self.session = session
        self.customers = customers

    def create_customer(self, data: CustomerCreate) -> Customer:
        email = data.email.lower()
        if self.customers.get_by_email(email) is not None:
            raise self._duplicate_email(email)

        customer = Customer(
            name=data.name,
            email=email,
            company=data.company,
            contact_details=data.contact_details,
        )
        try:
            with transaction(self.session):
                self.customers.add(customer)
        except IntegrityError as exc:  # concurrent insert won the race on the unique index
            raise self._duplicate_email(email) from exc
        return customer

    def list_customers(self, skip: int = 0, limit: int = 50) -> list[Customer]:
        return self.customers.list(skip=skip, limit=limit)

    def get_customer(self, customer_id: int) -> Customer:
        customer = self.customers.get(customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} not found.")
        return customer

    @staticmethod
    def _duplicate_email(email: str) -> ConflictError:
        return ConflictError(f"A customer with email '{email}' already exists.")
