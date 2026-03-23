from dataclasses import dataclass


@dataclass(slots=True)
class Lecturer:
    id: int
    name: str
    maxUnitPerWeek: int
    preferenceDay: list[int]
