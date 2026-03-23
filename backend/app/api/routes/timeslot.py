import dataclasses
from fastapi import APIRouter, HTTPException
from app.schemas import TimeSlot
from app.db import db

router = APIRouter()


@router.get("/")
def list_timeslots():
    return db.get_collection("timeslots")


@router.get("/{timeslot_id}")
def get_timeslot(timeslot_id: int):
    for t in db.get_collection("timeslots"):
        if t.get("id") == timeslot_id:
            return t
    raise HTTPException(status_code=404, detail="Timeslot not found")


@router.post("/", status_code=201)
def create_timeslot(timeslot: TimeSlot):
    items = db.get_collection("timeslots")
    new_item = dataclasses.asdict(timeslot)
    new_item["id"] = db.next_id("timeslots")
    items.append(new_item)
    db.set_collection("timeslots", items)
    return new_item


@router.put("/{timeslot_id}")
def update_timeslot(timeslot_id: int, timeslot: TimeSlot):
    items = db.get_collection("timeslots")
    for i, t in enumerate(items):
        if t.get("id") == timeslot_id:
            updated = dataclasses.asdict(timeslot)
            updated["id"] = timeslot_id
            items[i] = updated
            db.set_collection("timeslots", items)
            return updated
    raise HTTPException(status_code=404, detail="Timeslot not found")


@router.delete("/{timeslot_id}")
def delete_timeslot(timeslot_id: int):
    items = db.get_collection("timeslots")
    new_items = [t for t in items if t.get("id") != timeslot_id]
    if len(new_items) == len(items):
        raise HTTPException(status_code=404, detail="Timeslot not found")
    db.set_collection("timeslots", new_items)
    return {"message": "Deleted", "id": timeslot_id}
