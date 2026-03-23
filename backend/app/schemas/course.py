from dataclasses import dataclass


@dataclass(slots=True)
class Course:
    id: int
    courseCode: str
    name: str
    unitsPerWeek: int
    studentsCount: int
    roomType: list[str]
    lecturer_id: int
    maxUnitsPerDay: int

    @classmethod
    def from_dict(cls, data: dict) -> "Course":
        normalized = {}
        for k, v in data.items():
            if k == "lecturerId":
                normalized["lecturer_id"] = v
            else:
                normalized[k] = v
        return cls(**normalized)
