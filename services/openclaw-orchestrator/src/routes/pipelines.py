"""Pipeline management routes for OpenClaw Orchestrator"""

from fastapi import APIRouter, Depends, HTTPException, status

from ...models.requests import PipelineExecuteRequest
from ...models.responses import PipelineExecuteResponse, PipelineStatus
from ...core.pipeline_executor import PipelineExecutor

router = APIRouter()


async def get_pipeline_executor() -> PipelineExecutor:
    """Dependency to get pipeline executor instance."""
    from ....main import pipeline_executor
    return pipeline_executor  # type: ignore


@router.post("/execute", response_model=PipelineExecuteResponse)
async def execute_pipeline(
    request: PipelineExecuteRequest,
    pipeline_executor: PipelineExecutor = Depends(get_pipeline_executor)
) -> PipelineExecuteResponse:
    """
    Execute a pipeline.

    Executes a pipeline of skills, either from a pre-defined pipeline ID
    or from an ad-hoc set of steps.
    """
    try:
        response = await pipeline_executor.execute(
            pipeline_id=request.pipeline_id,
            steps=request.steps,
            input_data=request.input,
            config=request.config,
            parallel=request.parallel,
            timeout_ms=request.timeout_ms,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Pipeline execution timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {str(e)}"
        )


@router.get("/status/{pipeline_id}", response_model=PipelineStatus)
async def get_pipeline_status(
    pipeline_id: str,
    pipeline_executor: PipelineExecutor = Depends(get_pipeline_executor)
) -> PipelineStatus:
    """
    Get the status of a running pipeline.

    Returns the current status of a pipeline execution.
    """
    try:
        status = await pipeline_executor.get_status(pipeline_id)
        return status
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline not found: {pipeline_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline status: {str(e)}"
        )


@router.post("/define", status_code=status.HTTP_201_CREATED)
async def define_pipeline(
    pipeline_id: str,
    steps: list,
    pipeline_executor: PipelineExecutor = Depends(get_pipeline_executor)
) -> dict:
    """
    Define a new pipeline.

    Creates a new pipeline definition that can be executed later.
    """
    try:
        await pipeline_executor.define_pipeline(pipeline_id, steps)
        return {"pipeline_id": pipeline_id, "status": "defined"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to define pipeline: {str(e)}"
        )


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: str,
    pipeline_executor: PipelineExecutor = Depends(get_pipeline_executor)
) -> None:
    """Delete a pipeline definition."""
    try:
        await pipeline_executor.delete_pipeline(pipeline_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline not found: {pipeline_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete pipeline: {str(e)}"
        )
