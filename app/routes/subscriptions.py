from fastapi import APIRouter, Query, status

from app.models import Subscription, SubscriptionStatus
from app.routes.dependencies import SubscriptionServiceDep
from app.schemas.common import ErrorResponse
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post(
    "",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
def create_subscription(payload: SubscriptionCreate, service: SubscriptionServiceDep) -> Subscription:
    return service.create_subscription(payload)


@router.get("", response_model=list[SubscriptionResponse])
def list_subscriptions(
    service: SubscriptionServiceDep,
    customer_id: int | None = Query(default=None, gt=0),
    status_filter: SubscriptionStatus | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[Subscription]:
    return service.list_subscriptions(
        customer_id=customer_id, status=status_filter, skip=skip, limit=limit
    )


@router.get(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_subscription(subscription_id: int, service: SubscriptionServiceDep) -> Subscription:
    return service.get_subscription(subscription_id)


@router.post(
    "/{subscription_id}/cancel",
    response_model=SubscriptionResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def cancel_subscription(subscription_id: int, service: SubscriptionServiceDep) -> Subscription:
    return service.cancel_subscription(subscription_id)
