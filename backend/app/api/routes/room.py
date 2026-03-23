import dataclasses
from fastapi import APIRouter, HTTPException
from app.schemas import Room
from app.db import db

router = APIRouter()


@router.get("/")
def list_rooms():
    return db.get_collection("rooms")


@router.get("/{room_id}")
def get_room(room_id: int):
    for r in db.get_collection("rooms"):
        if r.get("id") == room_id:
            return r
    raise HTTPException(status_code=404, detail="Room not found")


@router.post("/", status_code=201)
def create_room(room: Room):
    items = db.get_collection("rooms")
    new_item = dataclasses.asdict(room)
    new_item["id"] = db.next_id("rooms")
    items.append(new_item)
    db.set_collection("rooms", items)
    return new_item


@router.put("/{room_id}")
def update_room(room_id: int, room: Room):
    items = db.get_collection("rooms")
    for i, r in enumerate(items):
        if r.get("id") == room_id:
            updated = dataclasses.asdict(room)
            updated["id"] = room_id
            items[i] = updated
            db.set_collection("rooms", items)
            return updated
    raise HTTPException(status_code=404, detail="Room not found")


@router.delete("/{room_id}")
def delete_room(room_id: int):
    items = db.get_collection("rooms")
    new_items = [r for r in items if r.get("id") != room_id]
    if len(new_items) == len(items):
        raise HTTPException(status_code=404, detail="Room not found")
    db.set_collection("rooms", new_items)
    return {"message": "Deleted", "id": room_id}
