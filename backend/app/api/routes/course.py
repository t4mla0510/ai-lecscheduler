import dataclasses
from fastapi import APIRouter, HTTPException
from app.schemas import Course
from app.db import db

router = APIRouter()


@router.get("/")
def list_courses():
    return db.get_collection("courses")


@router.get("/{course_id}")
def get_course(course_id: int):
    for c in db.get_collection("courses"):
        if c.get("id") == course_id:
            return c
    raise HTTPException(status_code=404, detail="Course not found")


@router.post("/", status_code=201)
def create_course(course: Course):
    items = db.get_collection("courses")
    new_item = dataclasses.asdict(course)
    new_item["id"] = db.next_id("courses")
    items.append(new_item)
    db.set_collection("courses", items)
    return new_item


@router.put("/{course_id}")
def update_course(course_id: int, course: Course):
    items = db.get_collection("courses")
    for i, c in enumerate(items):
        if c.get("id") == course_id:
            updated = dataclasses.asdict(course)
            updated["id"] = course_id
            items[i] = updated
            db.set_collection("courses", items)
            return updated
    raise HTTPException(status_code=404, detail="Course not found")


@router.delete("/{course_id}")
def delete_course(course_id: int):
    items = db.get_collection("courses")
    new_items = [c for c in items if c.get("id") != course_id]
    if len(new_items) == len(items):
        raise HTTPException(status_code=404, detail="Course not found")
    db.set_collection("courses", new_items)
    return {"message": "Deleted", "id": course_id}
