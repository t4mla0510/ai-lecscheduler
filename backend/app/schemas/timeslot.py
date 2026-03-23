from dataclasses import dataclass


@dataclass(slots=True)
class TimeSlot:
    id: int
    day: int
    start_period: int
