from typing import Any
from dataclasses import dataclass
from app.schemas.gene import Gene


@dataclass(slots=True)
class Chromosome:
    genes: list[Gene]
    fitness: Any = 0.0
