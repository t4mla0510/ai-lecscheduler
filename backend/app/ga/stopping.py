import time
from typing import Tuple


class StoppingCondition:
    def __init__(
        self,
        max_generations: int = 1000,
        target_fitness: float = None,
        max_time_seconds: int = 30,
        max_stall_generations: int = 50,
        base_mutation_rate: float = 0.05,
        max_mutation_rate: float = 1.0,
    ):
        self.max_generations = max_generations
        self.target_fitness = target_fitness
        self.max_time_seconds = max_time_seconds

        self.max_stall_generations = max_stall_generations
        self.base_mutation_rate = base_mutation_rate
        self.max_mutation_rate = max_mutation_rate

        # State tracking
        self.start_time = None
        self.best_fitness_ever = None
        self.stall_count = 0
        self.current_mutation_rate = base_mutation_rate

    def reset(self):
        self.start_time = time.time()
        self.best_fitness_ever = None
        self.stall_count = 0
        self.current_mutation_rate = self.base_mutation_rate

    def check_stop_and_adapt(
        self, current_generation: int, current_best_fitness: float
    ) -> Tuple[bool, str]:
        if self.start_time is None:
            self.start_time = time.time()

        # Số thế hệ đạt giới hạn
        if current_generation >= self.max_generations:
            return True, f"Đã đạt số thế hệ tối đa ({self.max_generations})."

        # Vượt quá thời gian thực thi cho phép
        elapsed_time = time.time() - self.start_time
        if elapsed_time >= self.max_time_seconds:
            return (
                True,
                f"Vượt quá thời gian thực thi tối đa ({self.max_time_seconds}s).",
            )

        # Theo dõi sự cải thiện của Fitness
        improved = (
            self.best_fitness_ever is None
            or current_best_fitness > self.best_fitness_ever
        )
        if improved:
            self.best_fitness_ever = current_best_fitness
            self.stall_count = 0
            # Reset lại tỷ lệ đột biến khi thoát khỏi vùng cực trị địa phương
            self.current_mutation_rate = self.base_mutation_rate
        else:
            self.stall_count += 1

        # Best fitness đạt ngưỡng mong muốn
        if (
            self.target_fitness is not None
            and self.best_fitness_ever is not None
            and not isinstance(self.best_fitness_ever, tuple)
            and self.best_fitness_ever >= self.target_fitness
        ):
            return (
                True,
                f"Đã đạt hoặc vượt ngưỡng Fitness mục tiêu ({self.best_fitness_ever} >= {self.target_fitness}).",
            )

        # Cơ chế chống bão hòa (Đột biến thích nghi) / Dừng khi bão hoà quá lâu
        if self.stall_count >= self.max_stall_generations:
            # Tăng đột biến để nhảy khỏi Local Optima thay vì dừng ngay (bước nhảy ~ 2%)
            # Lưu ý: rate này giờ được áp dụng ở cấp độ nhiễm sắc thể (chromosome) trong mutation.py
            if self.current_mutation_rate < self.max_mutation_rate:
                self.current_mutation_rate = min(
                    self.max_mutation_rate, self.current_mutation_rate + 0.02
                )
                # Đặt lại stall_count về nửa ngưỡng
                self.stall_count = self.max_stall_generations // 2
            else:
                # Nếu đã max đột biến mà vẫn dậm chân tại chỗ quá lâu (max_stall * 2), hệ thống cho dừng.
                if self.stall_count >= self.max_stall_generations * 2:
                    return (
                        True,
                        f"Quần thể đã bão hoà, không có sự cải thiện sau {self.stall_count} thế hệ dù đã tối đa tỷ lệ đột biến.",
                    )

        return False, "Tiếp tục chạy"
