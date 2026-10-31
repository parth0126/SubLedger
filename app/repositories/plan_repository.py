from sqlalchemy import select

from app.models import Plan, PlanStatus
from app.repositories.base import BaseRepository


class PlanRepository(BaseRepository[Plan]):
    model = Plan

    def list(self, status: PlanStatus | None = None, skip: int = 0, limit: int = 50) -> list[Plan]:
        stmt = select(Plan).order_by(Plan.id).offset(skip).limit(limit)
        if status is not None:
            stmt = stmt.where(Plan.status == status)
        return list(self.session.scalars(stmt))
