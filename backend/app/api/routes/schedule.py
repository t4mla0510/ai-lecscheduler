import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.schedule_request import ScheduleRequest
from app.ga.scheduler import GAScheduler
from app.utils import format_genes

router = APIRouter()


@router.post("/")
async def generate_schedule(request: ScheduleRequest):
    try:
        scheduler = GAScheduler(request)

        async def event_generator():
            for result in scheduler.run_generator():
                if result["type"] == "progress":
                    data = {
                        "type": "progress",
                        "generation": result["generation"],
                        "best": result["best"],
                        "avg": result["avg"],
                        "worst": result["worst"],
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                elif result["type"] == "final":
                    fitness = result["best_fitness"]
                    if isinstance(fitness, tuple):
                        fitness = {"hard_score": fitness[0], "soft_score": fitness[1]}

                    final_data = {
                        "type": "final",
                        "status": "success",
                        "generations": result["generations_run"],
                        "stop_reason": result["stop_reason"],
                        "best_fitness": fitness,
                        "hard_constraints": result["hard_constraints"],
                        "soft_constraints": result["soft_constraints"],
                        "schedule": format_genes(
                            result["best_chromosome"],
                            result["courses_dict"],
                            result["lecturers_dict"],
                            result["rooms_dict"],
                        ),
                        "trace": result.get("trace", []),
                    }
                    yield f"data: {json.dumps(final_data)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
