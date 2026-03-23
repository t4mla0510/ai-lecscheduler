from app.schemas.chromosome import Chromosome


def get_elites(
    population: list[Chromosome], elitism_rate: float = 0.1
) -> list[Chromosome]:
    if not population:
        return []

    # Tính toán số lượng Elite cần giữ lại
    elite_size = max(1, int(len(population) * elitism_rate))

    # Sắp xếp quần thể giảm dần theo fitness
    sorted_population = sorted(population, key=lambda ind: ind.fitness, reverse=True)

    # Lấy ra nhóm các cá thể xuất sắc nhất
    return sorted_population[:elite_size]
