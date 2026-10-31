from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Common persistence operations. Repositories flush but never commit:
    transaction boundaries belong to the service layer."""

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, entity_id: int) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def get_for_update(self, entity_id: int) -> ModelT | None:
        """Fetch a row with a row-level lock (SELECT ... FOR UPDATE) for safe read-modify-write."""
        stmt = (
            select(self.model)
            .where(self.model.id == entity_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return self.session.scalars(stmt).first()

    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        self.session.flush()
        return entity
