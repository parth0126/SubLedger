from sqlalchemy import exists, select

from app.models import Subscription, SubscriptionStatus
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription

    def has_active(self, customer_id: int, plan_id: int) -> bool:
        stmt = select(
            exists().where(
                Subscription.customer_id == customer_id,
                Subscription.plan_id == plan_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        )
        return bool(self.session.scalar(stmt))

    def list(
        self,
        customer_id: int | None = None,
        status: SubscriptionStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Subscription]:
        stmt = select(Subscription).order_by(Subscription.id).offset(skip).limit(limit)
        if customer_id is not None:
            stmt = stmt.where(Subscription.customer_id == customer_id)
        if status is not None:
            stmt = stmt.where(Subscription.status == status)
        return list(self.session.scalars(stmt))
