"""Lighting cue execution routes."""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from ..models.request import CueRequest
from ..models.response import CueResponse

router = APIRouter()


def _get_handler():
    """Get the lighting handler instance."""
    from ....main import handler
    return handler


@router.post("/v1/cues/execute", response_model=CueResponse)
async def execute_cue(request: CueRequest) -> CueResponse:
    """Execute a lighting cue.

    Args:
        request: Cue execution request

    Returns:
        Cue execution response
    """
    handler = _get_handler()

    # Get preset values if specified
    preset_values = None
    if request.preset_name:
        preset_values = await handler.fixture_manager.apply_preset(
            request.preset_name,
            request.fade_time
        )
        if not preset_values:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preset '{request.preset_name}' not found"
            )

    response = await handler.cue_executor.execute_cue(request, preset_values)

    return response


@router.post("/v1/cues/{cue_list}/go")
async def go_cue(cue_list: str = "main", cue_number: str = "next") -> Dict[str, Any]:
    """Execute the next or specified cue in a cue list.

    Args:
        cue_list: Cue list identifier
        cue_number: Specific cue number or 'next'

    Returns:
        Execution result
    """
    handler = _get_handler()

    list_obj = handler.cue_executor.get_cue_list(cue_list)
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cue list '{cue_list}' not found"
        )

    if cue_number == "next":
        current = handler.cue_executor.get_current_cue()
        if current:
            cue = list_obj.get_next_cue(current)
            if cue:
                cue_number = cue.cue_number
            else:
                return {"status": "no_next_cue", "current": current}
        else:
            # Start from beginning
            if list_obj.execution_order:
                cue_number = list_obj.execution_order[0]
            else:
                return {"status": "empty_cue_list"}

    request = CueRequest(
        cue_number=cue_number,
        cue_list=cue_list
    )

    response = await handler.cue_executor.execute_cue(request)

    return {
        "status": response.status,
        "executed": response.executed,
        "cue_number": response.cue_number,
        "timing": response.timing
    }


@router.post("/v1/cues/{cue_list}/stop")
async def stop_cues(cue_list: str = "main") -> Dict[str, str]:
    """Stop all cue executions in a cue list.

    Args:
        cue_list: Cue list identifier (or 'all' for all lists)

    Returns:
        Stop confirmation
    """
    handler = _get_handler()

    if cue_list == "all":
        await handler.cue_executor.stop_all()
        return {"status": "stopped_all_cues"}
    else:
        # Stop specific list - would need list-specific tracking
        await handler.cue_executor.stop_all()
        return {"status": f"stopped_cues_in_{cue_list}"}


@router.get("/v1/cues/{cue_list}", response_model=Dict[str, Any])
async def get_cue_list(cue_list: str = "main") -> Dict[str, Any]:
    """Get all cues in a cue list.

    Args:
        cue_list: Cue list identifier

    Returns:
        Dictionary of cues
    """
    handler = _get_handler()

    list_obj = handler.cue_executor.get_cue_list(cue_list)
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cue list '{cue_list}' not found"
        )

    cues = {}
    for cue_number, cue in list_obj.get_all_cues().items():
        cues[cue_number] = {
            "cue_number": cue.cue_number,
            "preset_name": cue.preset_name,
            "fade_time": cue.fade_time,
            "delay_secs": cue.delay_secs,
            "follow_on": cue.follow_on,
            "description": cue.description
        }

    return {
        "cue_list": cue_list,
        "cues": cues,
        "current": handler.cue_executor.get_current_cue()
    }


@router.get("/v1/cues/{cue_list}/{cue_number}", response_model=Dict[str, Any])
async def get_cue(cue_list: str, cue_number: str) -> Dict[str, Any]:
    """Get a specific cue definition.

    Args:
        cue_list: Cue list identifier
        cue_number: Cue identifier

    Returns:
        Cue definition
    """
    handler = _get_handler()

    list_obj = handler.cue_executor.get_cue_list(cue_list)
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cue list '{cue_list}' not found"
        )

    cue = list_obj.get_cue(cue_number)
    if not cue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cue '{cue_number}' not found in list '{cue_list}'"
        )

    return {
        "cue_number": cue.cue_number,
        "cue_list": cue.cue_list,
        "preset_name": cue.preset_name,
        "values": cue.values,
        "fade_time": cue.fade_time,
        "delay_secs": cue.delay_secs,
        "follow_on": cue.follow_on,
        "description": cue.description,
        "auto_follow": cue.auto_follow
    }


@router.get("/v1/cues/statistics", response_model=Dict[str, Any])
async def get_cue_statistics() -> Dict[str, Any]:
    """Get cue execution statistics.

    Returns:
        Execution statistics
    """
    handler = _get_handler()
    return handler.cue_executor.get_statistics()


@router.post("/v1/cues/lists", response_model=Dict[str, str])
async def create_cue_list(name: str) -> Dict[str, str]:
    """Create a new cue list.

    Args:
        name: Cue list name

    Returns:
        Creation confirmation
    """
    handler = _get_handler()

    if handler.cue_executor.get_cue_list(name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cue list '{name}' already exists"
        )

    handler.cue_executor.create_cue_list(name)
    return {"status": "created", "name": name}


@router.get("/v1/cues/lists", response_model=List[str])
async def list_cue_lists() -> List[str]:
    """List all cue lists.

    Returns:
        List of cue list names
    """
    handler = _get_handler()
    stats = handler.cue_executor.get_statistics()
    return stats.get("cue_lists", [])
