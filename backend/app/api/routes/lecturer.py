import dataclasses
from fastapi import APIRouter, HTTPException
from app.schemas import Lecturer
from app.db import db

router = APIRouter()


@router.get("/")
def list_lecturers():
    return db.get_collection("lecturers")


@router.get("/{lecturer_id}")
def get_lecturer(lecturer_id: int):
    for l in db.get_collection("lecturers"):
        if l.get("id") == lecturer_id:
            return l
    raise HTTPException(status_code=404, detail="Lecturer not found")


@router.post("/", status_code=201)
def create_lecturer(lecturer: Lecturer):
    items = db.get_collection("lecturers")
    new_item = dataclasses.asdict(lecturer)
    new_item["id"] = db.next_id("lecturers")
    items.append(new_item)
    db.set_collection("lecturers", items)
    return new_item


@router.put("/{lecturer_id}")
def update_lecturer(lecturer_id: int, lecturer: Lecturer):
    items = db.get_collection("lecturers")
    for i, l in enumerate(items):
        if l.get("id") == lecturer_id:
            updated = dataclasses.asdict(lecturer)
            updated["id"] = lecturer_id
            items[i] = updated
            db.set_collection("lecturers", items)
            return updated
    raise HTTPException(status_code=404, detail="Lecturer not found")


@router.delete("/{lecturer_id}")
def delete_lecturer(lecturer_id: int):
    items = db.get_collection("lecturers")
    new_items = [l for l in items if l.get("id") != lecturer_id]
    if len(new_items) == len(items):
        raise HTTPException(status_code=404, detail="Lecturer not found")
    db.set_collection("lecturers", new_items)
    return {"message": "Deleted", "id": lecturer_id}
