from dataclasses import dataclass


@dataclass(slots=True)
class Gene:
    room_id: int
    course_id: int
    timeslot_id: int
    units: int
    session_id: int
