from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import utc_now, utc_today
from app.core.exceptions import BusinessRuleViolation, ConflictError, NotFoundError
from app.db.session import transaction
from app.models import PlanStatus, Subscription, SubscriptionStatus
from app.repositories import CustomerRepository, PlanRepository, SubscriptionRepository
from app.schemas.subscription import SubscriptionCreate
from app.services.billing_period import period_end


class SubscriptionService:
    """Creates and cancels subscriptions, enforcing plan availability and uniqueness rules."""

    def __init__(
        self,
        session: Session,
        subscriptions: SubscriptionRepository,
        customers: CustomerRepository,
        plans: PlanRepository,
    ) -> None:
        self.session = session
        self.subscriptions = subscriptions
        self.customers = customers
        self.plans = plans

    def create_subscription(self, data: SubscriptionCreate) -> Subscription:
        if self.customers.get(data.customer_id) is None:
            raise NotFoundError(f"Customer {data.customer_id} not found.")
        plan = self.plans.get(data.plan_id)
        if plan is None:
            raise NotFoundError(f"Plan {data.plan_id} not found.")
        if plan.status != PlanStatus.ACTIVE:
            raise BusinessRuleViolation("Cannot subscribe to an inactive plan.")
        if self.subscriptions.has_active(data.customer_id, data.plan_id):
            raise self._duplicate_active()

        start = data.start_date or utc_today()
        subscription = Subscription(
            customer_id=data.customer_id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE,
            start_date=start,
            current_period_start=start,
            current_period_end=period_end(start, plan.billing_cycle),
        )
        try:
            with transaction(self.session):
                self.subscriptions.add(subscription)
        except IntegrityError as exc:  # partial unique index caught a concurrent duplicate
            raise self._duplicate_active() from exc
        return subscription

    def list_subscriptions(
        self,
        customer_id: int | None = None,
        status: SubscriptionStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Subscription]:
        return self.subscriptions.list(customer_id=customer_id, status=status, skip=skip, limit=limit)

    def get_subscription(self, subscription_id: int) -> Subscription:
        subscription = self.subscriptions.get(subscription_id)
        if subscription is None:
            raise NotFoundError(f"Subscription {subscription_id} not found.")
        return subscription

    def cancel_subscription(self, subscription_id: int) -> Subscription:
        with transaction(self.session):
            subscription = self.subscriptions.get_for_update(subscription_id)
            if subscription is None:
                raise NotFoundError(f"Subscription {subscription_id} not found.")
            if subscription.status == SubscriptionStatus.CANCELLED:
                raise ConflictError(f"Subscription {subscription_id} is already cancelled.")
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = utc_now()
        return subscription

    @staticmethod
    def _duplicate_active() -> ConflictError:
        return ConflictError("Customer already has an active subscription to this plan.")
