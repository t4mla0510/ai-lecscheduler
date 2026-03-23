from typing import Dict, Any
from app.ga.scheduler import GAScheduler
from app.schemas import ScheduleRequest

class SchedulerService:
    @staticmethod
    def run_genetic_algorithm(request: ScheduleRequest) -> Dict[str, Any]:
        scheduler = GAScheduler(request)
        result = scheduler.run()
        
        return {
            "best_chromosome": result["best_chromosome"],
            "best_fitness": result["best_fitness"],
            "generations_run": result["generations_run"],
            "stop_reason": result["stop_reason"],
            "hard_constraints": result["hard_constraints"],
            "soft_constraints": result["soft_constraints"]
        }
