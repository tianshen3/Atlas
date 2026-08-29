"""
Task status polling REST Router.
"""

from typing import Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from celery.result import AsyncResult
from app.workers.celery_app import celery_app

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Poll status of a background Celery ingestion task.

    Args:
        task_id: Celery task UUID string.

    Returns:
        TaskStatusResponse containing status (PENDING, STARTED, SUCCESS, FAILURE) and result details.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    status_str = task_result.status

    result_data = None
    if task_result.ready():
        if task_result.successful():
            result_data = task_result.result
        else:
            result_data = str(task_result.result)

    return TaskStatusResponse(
        task_id=task_id,
        status=status_str,
        result=result_data,
    )
