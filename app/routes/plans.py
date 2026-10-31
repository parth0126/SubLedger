from fastapi import APIRouter, Query, status

from app.models import Plan, PlanStatus
from app.routes.dependencies import PlanServiceDep
from app.schemas.common import ErrorResponse
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.post(
    "",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": ErrorResponse}},
)
def create_plan(payload: PlanCreate, service: PlanServiceDep) -> Plan:
    return service.create_plan(payload)


@router.get("", response_model=list[PlanResponse])
def list_plans(
    service: PlanServiceDep,
    status_filter: PlanStatus | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[Plan]:
    return service.list_plans(status=status_filter, skip=skip, limit=limit)


@router.patch(
    "/{plan_id}",
    response_model=PlanResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def update_plan(plan_id: int, payload: PlanUpdate, service: PlanServiceDep) -> Plan:
    """Update plan fields, or activate/deactivate it with `{"status": "active" | "inactive"}`."""
    return service.update_plan(plan_id, payload)
