from pydantic import BaseModel, Field
from typing import Optional


class FitnessConfig(BaseModel):
    method: str = Field(
        default="weighted",
        description="weighted | penalty | alpha_beta | lexicographic",
    )
    # penalty_fitness params
    base_score: int = Field(default=1000, description="Điểm cơ sở for penalty_fitness")
    hard_penalty: int = Field(default=50, description="Điểm trừ mỗi vi phạm cứng")
    soft_bonus: int = Field(default=5, description="Điểm cộng mỗi tiêu chí mềm đạt")
    # alpha_beta_fitness params
    alpha: int = Field(
        default=1000, description="Trọng số hard constraint for alpha_beta_fitness"
    )
    beta: int = Field(
        default=10, description="Trọng số soft constraint for alpha_beta_fitness"
    )


class SelectionConfig(BaseModel):
    method: str = Field(
        default="tournament", description="roulette | tournament | rank | elimination"
    )
    tournament_k: int = Field(
        default=3, ge=2, description="Top-k for tournament selection"
    )


class CrossoverConfig(BaseModel):
    method: str = Field(
        default="single_point",
        description="single_point | two_point | multi_point | uniform",
    )
    rate: float = Field(default=0.8, ge=0.0, le=1.0, description="Tỷ lệ lai ghép")
    n_points: int = Field(
        default=3, ge=1, description="Số điểm cắt for multi_point crossover"
    )


class MutationConfig(BaseModel):
    method: str = Field(
        default="random", description="random | swap | creep | heuristic"
    )
    rate: float = Field(default=0.05, ge=0.0, le=1.0, description="Tỷ lệ đột biến")


class GAConfig(BaseModel):
    pop_size: int = Field(
        default=100, ge=10, le=1000, description="Kích thước quần thể"
    )
    elitism_rate: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Tỷ lệ elite giữ lại"
    )
    max_generations: int = Field(
        default=500, ge=1, le=10000, description="Số thế hệ tối đa"
    )
    max_time_seconds: int = Field(
        default=30, ge=1, le=300, description="Thời gian tối đa (giây)"
    )
    target_fitness: Optional[float] = Field(
        default=None, description="Ngưỡng fitness mục tiêu"
    )


class ScheduleRequest(BaseModel):
    fitness: FitnessConfig = FitnessConfig()
    selection: SelectionConfig = SelectionConfig()
    crossover: CrossoverConfig = CrossoverConfig()
    mutation: MutationConfig = MutationConfig()
    ga: GAConfig = GAConfig()
