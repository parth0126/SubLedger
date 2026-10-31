from sqlalchemy import select

from app.models import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    model = Customer

    def get_by_email(self, email: str) -> Customer | None:
        return self.session.scalars(select(Customer).where(Customer.email == email)).first()

    def list(self, skip: int = 0, limit: int = 50) -> list[Customer]:
        stmt = select(Customer).order_by(Customer.id).offset(skip).limit(limit)
        return list(self.session.scalars(stmt))
