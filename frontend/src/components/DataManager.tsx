// Data Manager: tabbed CRUD for lecturers, courses, rooms
import { useState } from "react";
import { useAppState } from "../data/store";
import type { Lecturer, Course, Room } from "../data/types";
import { DAYS, ROOM_TYPES } from "../data/types";
import { lecturerApi } from "../api/lecturerApi";
import { courseApi } from "../api/courseApi";
import { roomApi } from "../api/roomApi";

type Tab = "lecturers" | "courses" | "rooms";

export function DataManager() {
  const { state } = useAppState();
  const [activeTab, setActiveTab] = useState<Tab>("lecturers");

  const tabs: { id: Tab; label: string; count: number }[] = [
    { id: "lecturers", label: "Lecturers", count: state.lecturers.length },
    { id: "courses", label: "Courses", count: state.courses.length },
    { id: "rooms", label: "Rooms", count: state.rooms.length },
  ];

  return (
    <div className="data-manager">
      <div className="page-header">
        <h2 className="page-title">Data Manager</h2>
        <p className="page-description">Manage lecturers, courses, and rooms</p>
      </div>

      <div className="tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
            <span className="tab-badge">{tab.count}</span>
          </button>
        ))}
      </div>

      <div className="tab-content">
        {activeTab === "lecturers" && <LecturersTab />}
        {activeTab === "courses" && <CoursesTab />}
        {activeTab === "rooms" && <RoomsTab />}
      </div>
    </div>
  );
}

// ── Lecturers ──────────────────────────────────────────────

function LecturersTab() {
  const { state, dispatch } = useAppState();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [maxUnits, setMaxUnits] = useState(12);
  const [days, setDays] = useState<number[]>([1, 2, 3]);

  const resetForm = () => {
    setName("");
    setMaxUnits(12);
    setDays([1, 2, 3]);
    setEditingId(null);
    setShowForm(false);
  };

  const openAdd = () => {
    resetForm();
    setShowForm(true);
  };

  const openEdit = (lec: Lecturer) => {
    setEditingId(lec.id);
    setName(lec.name);
    setMaxUnits(lec.maxUnitPerWeek);
    setDays(lec.preferenceDay);
    setShowForm(true);
  };

  const handleSubmit = async () => {
    if (!name.trim()) return;

    const payload: Lecturer = {
      id: editingId ?? Date.now(),
      name: name.trim(),
      maxUnitPerWeek: maxUnits,
      preferenceDay: days,
    };

    try {
      if (editingId !== null) {
        await lecturerApi.update(editingId, payload);
      } else {
        await lecturerApi.create(payload);
      }
      const allRes = await lecturerApi.getAll();
      dispatch({ type: "SET_LECTURERS", payload: allRes.data });
      resetForm();
    } catch (err) {
      console.error("Save lecturer error", err);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await lecturerApi.delete(id);
      const allRes = await lecturerApi.getAll();
      dispatch({ type: "SET_LECTURERS", payload: allRes.data });
    } catch (err) {
      console.error("Delete lecturer error", err);
    }
  };

  const toggleDay = (dayNum: number) => {
    setDays((prev) =>
      prev.includes(dayNum) ? prev.filter((d) => d !== dayNum) : [...prev, dayNum]
    );
  };

  return (
    <div>
      <div className="toolbar">
        <button className="btn-add" onClick={showForm && editingId === null ? resetForm : openAdd}>
          {showForm && editingId === null ? "✕ Cancel" : "+ Add Lecturer"}
        </button>
      </div>

      {showForm && (
        <div className="form-card">
          <div className="form-group">
            <label>Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. PhD. Nguyen Van A"
              className="input"
            />
          </div>
          <div className="form-group">
            <label>Max Units/Week</label>
            <input
              type="number"
              value={maxUnits}
              onChange={(e) => setMaxUnits(Number(e.target.value))}
              min={1}
              max={40}
              className="input"
            />
          </div>
          <div className="form-group">
            <label>Preferred Days</label>
            <div className="day-selector">
              {DAYS.map((day, i) => {
                const dayNum = i + 1;
                return (
                  <button
                    key={dayNum}
                    className={`day-chip ${days.includes(dayNum) ? "selected" : ""}`}
                    onClick={() => toggleDay(dayNum)}
                  >
                    {day.slice(0, 3)}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="form-actions">
            <button className="btn-submit" onClick={handleSubmit}>
              {editingId !== null ? "Update Lecturer" : "Add Lecturer"}
            </button>
            {editingId !== null && (
              <button className="btn-cancel" onClick={resetForm} style={{marginLeft: 5}}>Cancel</button>
            )}
          </div>
        </div>
      )}

      <div className="items-list">
        {(state.lecturers ?? []).map((lec) => (
          <div key={lec.id} className="item-card">
            <div className="item-info">
              <span className="item-name">{lec.name}</span>
              <span className="item-detail">
                Max {lec.maxUnitPerWeek} units/week · Prefers:{" "}
                {lec.preferenceDay.map((d: number) => DAYS[d - 1]?.slice(0, 3)).join(", ")}
              </span>
            </div>
            <div className="item-actions">
              <button className="btn-edit" onClick={() => openEdit(lec)}>✏️</button>
              <button className="btn-delete" onClick={() => handleDelete(lec.id)}>🗑️</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Courses ────────────────────────────────────────────────

function CoursesTab() {
  const { state, dispatch } = useAppState();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [courseCode, setCourseCode] = useState("");
  const [name, setName] = useState("");
  const [unitsPerWeek, setUnitsPerWeek] = useState(9);
  const [maxUnitsPerDay, setMaxUnitsPerDay] = useState(3);
  const [lecturerId, setLecturerId] = useState<number>(state.lecturers[0]?.id || 0);
  const [students, setStudents] = useState(40);
  const [roomTypes, setRoomTypes] = useState<string[]>(["Lecture"]);

  const resetForm = () => {
    setCourseCode("");
    setName("");
    setUnitsPerWeek(9);
    setMaxUnitsPerDay(3);
    setStudents(40);
    setRoomTypes(["Lecture"]);
    setLecturerId(state.lecturers[0]?.id || 0);
    setEditingId(null);
    setShowForm(false);
  };

  const openAdd = () => {
    resetForm();
    setShowForm(true);
  };

  const openEdit = (course: Course) => {
    setEditingId(course.id);
    setCourseCode(course.courseCode);
    setName(course.name);
    setUnitsPerWeek(course.unitsPerWeek);
    setMaxUnitsPerDay(course.maxUnitsPerDay);
    setStudents(course.studentsCount);
    setRoomTypes(course.roomType);
    setLecturerId(course.lecturerId);
    setShowForm(true);
  };

  const handleSubmit = async () => {
    if (!name.trim() || !courseCode.trim()) return;

    const payload: Course = {
      id: editingId ?? Date.now(),
      courseCode: courseCode.trim(),
      name: name.trim(),
      unitsPerWeek,
      studentsCount: students,
      roomType: roomTypes,
      lecturerId,
      maxUnitsPerDay,
    };

    try {
      if (editingId !== null) {
        await courseApi.update(editingId, payload);
      } else {
        await courseApi.create(payload);
      }
      const allRes = await courseApi.getAll();
      dispatch({ type: "SET_COURSES", payload: allRes.data });
      resetForm();
    } catch (err) {
      console.error("Save course error", err);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await courseApi.delete(id);
      const allRes = await courseApi.getAll();
      dispatch({ type: "SET_COURSES", payload: allRes.data });
    } catch (err) {
      console.error("Delete course error", err);
    }
  };

  const toggleRoomType = (t: string) => {
    setRoomTypes((prev) =>
      prev.includes(t) ? prev.filter((r) => r !== t) : [...prev, t]
    );
  };

  const getLecturerName = (id: number) =>
    state.lecturers.find((l) => l.id === id)?.name || "Unknown";

  return (
    <div>
      <div className="toolbar">
        <button className="btn-add" onClick={showForm && editingId === null ? resetForm : openAdd}>
          {showForm && editingId === null ? "✕ Cancel" : "+ Add Course"}
        </button>
      </div>

      {showForm && (
        <div className="form-card">
          <div className="form-row">
            <div className="form-group">
              <label>Course Code</label>
              <input
                type="text"
                value={courseCode}
                onChange={(e) => setCourseCode(e.target.value)}
                placeholder="e.g. CT175"
                className="input"
              />
            </div>
            <div className="form-group">
              <label>Course Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Cấu trúc dữ liệu"
                className="input"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Units/Week</label>
              <input
                type="number"
                value={unitsPerWeek}
                onChange={(e) => setUnitsPerWeek(Number(e.target.value))}
                min={1}
                max={20}
                className="input"
              />
            </div>
            <div className="form-group">
              <label>Max Units/Day</label>
              <input
                type="number"
                value={maxUnitsPerDay}
                onChange={(e) => setMaxUnitsPerDay(Number(e.target.value))}
                min={1}
                max={5}
                className="input"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Students</label>
              <input
                type="number"
                value={students}
                onChange={(e) => setStudents(Number(e.target.value))}
                min={1}
                className="input"
              />
            </div>
            <div className="form-group">
              <label>Lecturer</label>
              <select
                value={lecturerId}
                onChange={(e) => setLecturerId(Number(e.target.value))}
                className="input"
              >
                {state.lecturers.map((l) => (
                  <option key={l.id} value={l.id}>{l.name}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label>Room Types</label>
            <div className="day-selector">
              {ROOM_TYPES.map((t) => (
                <button
                  key={t}
                  className={`day-chip ${roomTypes.includes(t) ? "selected" : ""}`}
                  onClick={() => toggleRoomType(t)}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
          <div className="form-actions">
            <button className="btn-submit" onClick={handleSubmit}>
              {editingId !== null ? "Update Course" : "Add Course"}
            </button>
            {editingId !== null && (
              <button className="btn-cancel" onClick={resetForm} style={{marginLeft: 5}}>Cancel</button>
            )}
          </div>
        </div>
      )}

      <div className="items-list">
        {state.courses.map((course) => (
          <div key={course.id} className="item-card">
            <div className="item-color" style={{ backgroundColor: "#666" }}></div>
            <div className="item-info">
              <span className="item-name">{course.courseCode} – {course.name}</span>
              <span className="item-detail">
                {getLecturerName(course.lecturerId)} · {course.unitsPerWeek} units/wk ·{" "}
                {course.maxUnitsPerDay}p/session · {course.studentsCount} students ·{" "}
                {course.roomType.join(", ")}
              </span>
            </div>
            <div className="item-actions">
              <button className="btn-edit" onClick={() => openEdit(course)}>✏️</button>
              <button className="btn-delete" onClick={() => handleDelete(course.id)}>🗑️</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Rooms ──────────────────────────────────────────────────

function RoomsTab() {
  const { state, dispatch } = useAppState();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [capacity, setCapacity] = useState(50);
  const [type, setType] = useState("Lecture");

  const resetForm = () => {
    setName("");
    setCapacity(50);
    setType("Lecture");
    setEditingId(null);
    setShowForm(false);
  };

  const openAdd = () => {
    resetForm();
    setShowForm(true);
  };

  const openEdit = (room: Room) => {
    setEditingId(room.id);
    setName(room.name);
    setCapacity(room.capacity);
    setType(room.type);
    setShowForm(true);
  };

  const handleSubmit = async () => {
    if (!name.trim()) return;

    const payload: Room = {
      id: editingId ?? Date.now(),
      name: name.trim(),
      capacity,
      type,
    };

    try {
      if (editingId !== null) {
        await roomApi.update(editingId, payload);
      } else {
        await roomApi.create(payload);
      }
      const allRes = await roomApi.getAll();
      dispatch({ type: "SET_ROOMS", payload: allRes.data });
      resetForm();
    } catch (err) {
      console.error("Save room error", err);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await roomApi.delete(id);
      const allRes = await roomApi.getAll();
      dispatch({ type: "SET_ROOMS", payload: allRes.data });
    } catch (err) {
      console.error("Delete room error", err);
    }
  };

  const typeIcons: Record<string, string> = { Lecture: "🏛️", Lab: "🔬" };

  return (
    <div>
      <div className="toolbar">
        <button className="btn-add" onClick={showForm && editingId === null ? resetForm : openAdd}>
          {showForm && editingId === null ? "✕ Cancel" : "+ Add Room"}
        </button>
      </div>

      {showForm && (
        <div className="form-card">
          <div className="form-row">
            <div className="form-group">
              <label>Room Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. 101/C1"
                className="input"
              />
            </div>
            <div className="form-group">
              <label>Capacity</label>
              <input
                type="number"
                value={capacity}
                onChange={(e) => setCapacity(Number(e.target.value))}
                min={1}
                className="input"
              />
            </div>
          </div>
          <div className="form-group">
            <label>Room Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="input"
            >
              {ROOM_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div className="form-actions">
            <button className="btn-submit" onClick={handleSubmit}>
              {editingId !== null ? "Update Room" : "Add Room"}
            </button>
            {editingId !== null && (
              <button className="btn-cancel" onClick={resetForm} style={{marginLeft: 5}}>Cancel</button>
            )}
          </div>
        </div>
      )}

      <div className="items-list">
        {state.rooms.map((room) => (
          <div key={room.id} className="item-card">
            <div className="item-icon">{typeIcons[room.type] || "🏠"}</div>
            <div className="item-info">
              <span className="item-name">{room.name}</span>
              <span className="item-detail">
                Capacity: {room.capacity} · Type: {room.type}
              </span>
            </div>
            <div className="item-actions">
              <button className="btn-edit" onClick={() => openEdit(room)}>✏️</button>
              <button className="btn-delete" onClick={() => handleDelete(room.id)}>🗑️</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}