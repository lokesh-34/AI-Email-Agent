# ============================================================
# TASK ROUTES
# ============================================================

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from database import (
    get_all_tasks,
    get_task_by_message_id,
    update_task_status,
    get_pending_tasks,
    get_high_priority_tasks
)

router = APIRouter()


def clean_task_for_api(task):
    """Remove MongoDB _id and embedding from task."""
    if task is None:
        return None

    task.pop("_id", None)
    task.pop("embedding", None)
    return task


@router.get("/api/tasks")
async def list_tasks(
    status: Optional[str] = Query(
        None,
        description="Filter by status: pending, completed"
    )
):
    """Get all tasks, optionally filtered by status."""

    try:
        tasks = get_all_tasks(status=status)
        return [
            clean_task_for_api(task)
            for task in tasks
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch tasks: {str(e)}"
        )


@router.get("/api/tasks/{message_id}")
async def get_task(message_id: str):
    """Get a single task by message_id."""

    try:
        task = get_task_by_message_id(message_id)

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found."
            )

        return clean_task_for_api(task)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch task: {str(e)}"
        )


@router.post("/api/tasks/{message_id}/complete")
async def complete_task(message_id: str):
    """Mark a task as completed."""

    try:
        task = get_task_by_message_id(message_id)

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found."
            )

        if task.get("status") == "completed":
            return {
                "message": "Task is already completed.",
                "success": True
            }

        count = update_task_status(
            message_id,
            "completed"
        )

        if count > 0:
            return {
                "message": "Task marked as completed.",
                "success": True
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update task status."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete task: {str(e)}"
        )
