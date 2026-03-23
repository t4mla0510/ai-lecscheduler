from dataclasses import dataclass


@dataclass(slots=True)
class Room:
    id: int
    name: str
    capacity: int
    type: str
