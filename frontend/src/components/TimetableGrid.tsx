/* eslint-disable @typescript-eslint/no-unused-vars */
// Multi-Room Timetable Grid with day tabs
import { useState } from "react";
import { useAppState } from "../data/store";
import { DAYS, PERIODS_PER_DAY, PERIOD_TIME } from "../data/types";
import { ConflictPanel } from "./ConflictPanel";
import type { Gene } from "../data/types";

interface PopupInfo {
  courseName: string;
  roomName: string;
  lecturerName: string;
  timeRange: string;
  units: number;
  x: number;
  y: number;
}

export function TimetableGrid() {
  const { state } = useAppState();
  const [popup, setPopup] = useState<PopupInfo | null>(null);
  const [activeDay, setActiveDay] = useState(0);

  if (!state.timetable || state.timetable.length === 0) {
    return (
      <div className="timetable-page">
        <div className="page-header">
          <h2 className="page-title">Timetable</h2>
          <p className="page-description">
            Run the GA scheduler first to generate a timetable
          </p>
        </div>
        <div className="empty-state">
          <div className="empty-icon">📅</div>
          <h3>No Timetable Generated</h3>
          <p>
            Go to the GA Scheduler page and run the algorithm to generate an
            optimized timetable.
          </p>
        </div>
      </div>
    );
  }

  // Build lookup maps
  const courseMap = new Map(state.courses.map((c) => [c.id, c]));
  const lecturerMap = new Map(state.lecturers.map((l) => [l.id, l]));
  const roomMap = new Map(state.rooms.map((r) => [r.id, r]));

  // Get sorted room list
  const rooms = [...state.rooms].sort((a, b) => a.id - b.id);

  // For each gene, compute day and start period
  function getGenePosition(gene: Gene) {
    const dayIndex = Math.floor((gene.timeslotId - 1) / PERIODS_PER_DAY);
    const slotIndex = (gene.timeslotId - 1) % PERIODS_PER_DAY;
    return { dayIndex, slotIndex, duration: gene.units };
  }

  // Build a grid: grid[roomId][periodIndex] = Gene or null, for the active day
  type CellInfo =
    | { type: "empty" }
    | { type: "covered" }
    | { type: "start"; gene: Gene; rowSpan: number };

  const roomGrids = new Map<number, CellInfo[]>();

  for (const room of rooms) {
    roomGrids.set(
      room.id,
      Array.from({ length: PERIODS_PER_DAY }, () => ({ type: "empty" as const }))
    );
  }

  // Filter genes for the active day and place them
  const dayGenes = state.timetable.filter((g) => {
    const pos = getGenePosition(g);
    return pos.dayIndex === activeDay;
  });

  // Track conflicts (same room+period or same lecturer+period)
  const conflictCells = new Set<string>(); // "roomId-period"
  const lecturerPeriods = new Map<string, string[]>(); // "lecturerId-period" -> courseIds

  for (const gene of dayGenes) {
    const pos = getGenePosition(gene);
    const grid = roomGrids.get(gene.roomId);
    if (!grid) continue;

    let duration = pos.duration;
    if (pos.slotIndex + duration > PERIODS_PER_DAY) {
      duration = PERIODS_PER_DAY - pos.slotIndex;
    }

    // Check room conflict
    for (let i = 0; i < duration; i++) {
      const pIdx = pos.slotIndex + i;
      if (grid[pIdx].type !== "empty") {
        conflictCells.add(`${gene.roomId}-${pIdx}`);
      }
    }

    // Check lecturer conflict
    for (let i = 0; i < duration; i++) {
      const pIdx = pos.slotIndex + i;
      const lecKey = `${gene.lecturerId}-${pIdx}`;
      if (!lecturerPeriods.has(lecKey)) {
        lecturerPeriods.set(lecKey, []);
      }
      lecturerPeriods.get(lecKey)!.push(`${gene.roomId}-${pIdx}`);
    }

    // Place the gene
    if (grid[pos.slotIndex].type === "empty") {
      grid[pos.slotIndex] = { type: "start", gene, rowSpan: duration };
      for (let i = 1; i < duration; i++) {
        if (grid[pos.slotIndex + i].type === "empty") {
          grid[pos.slotIndex + i] = { type: "covered" };
        }
      }
    }
  }

  // Mark lecturer conflicts
  for (const [, cells] of lecturerPeriods) {
    if (cells.length > 1) {
      cells.forEach((c) => conflictCells.add(c));
    }
  }

  // Color palette for lecturers
  const lecturerColors = [
    "#1f5ca9", "#2e7d32", "#c62828", "#6a1b9a",
    "#e65100", "#00838f", "#4527a0", "#ad1457",
    "#00695c", "#ef6c00", "#283593", "#558b2f",
  ];

  function getLecturerColor(lecturerId: number) {
    return lecturerColors[lecturerId % lecturerColors.length];
  }

  const handleCardClick = (gene: Gene, e: React.MouseEvent) => {
    e.stopPropagation();
    const course = courseMap.get(gene.courseId);
    const lecturer = lecturerMap.get(gene.lecturerId);
    const room = roomMap.get(gene.roomId);
    const pos = getGenePosition(gene);

    const startIdx = pos.slotIndex;
    const endIdx = startIdx + gene.units - 1;
    const startTime = PERIOD_TIME[startIdx]?.start ?? `P${startIdx + 1}`;
    const endTime = PERIOD_TIME[endIdx]?.end ?? `P${endIdx + 1}`;

    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();

    setPopup({
      courseName: gene.courseName || (course ? `${course.courseCode} – ${course.name}` : `Course ${gene.courseId}`),
      roomName: gene.roomName || room?.name || `Room ${gene.roomId}`,
      lecturerName: gene.lecturerName || lecturer?.name || `Lecturer ${gene.lecturerId}`,
      timeRange: `${startTime} – ${endTime}`,
      units: gene.units,
      x: rect.left + rect.width / 2,
      y: rect.top,
    });
  };

  const closePopup = () => setPopup(null);

  return (
    <div className="timetable-page" onClick={closePopup}>
      <div className="page-header">
        <h2 className="page-title">Timetable</h2>
        <p className="page-description">
          Generated schedule · Fitness:{" "}
          <strong>{state.bestFitness?.toFixed(2) ?? "-"}</strong> · Generation:{" "}
          {state.currentGeneration}
        </p>
      </div>

      {/* Day Tabs */}
      <div className="day-tabs">
        {DAYS.map((day, idx) => (
          <button
            key={idx}
            className={`day-tab ${activeDay === idx ? "active" : ""}`}
            onClick={(e) => { e.stopPropagation(); setActiveDay(idx); }}
          >
            <span className="day-tab-full">{day}</span>
            <span className="day-tab-short">{day.slice(0, 3)}</span>
          </button>
        ))}
      </div>

      <div className="timetable-wrapper">
        <table className="timetable-table room-view">
          <colgroup>
            <col style={{ width: "40px" }} />
            <col className="period-col" />
            <col className="time-col" />
            {rooms.map((r) => (
              <col key={r.id} />
            ))}
          </colgroup>
          <thead>
            <tr>
              <th className="corner-header session-col">Session</th>
              <th className="corner-header period-col">Period</th>
              <th className="corner-header time-col">Time</th>
              {rooms.map((room) => (
                <th key={room.id} className="day-header-cell room-header">
                  <span className="room-header-name">{room.name}</span>
                  <span className="room-header-cap">{room.capacity} seats</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: PERIODS_PER_DAY }).map((_, slotIdx) => {
              const isFirstMorning = slotIdx === 0;
              const isFirstAfternoon = slotIdx === 5;
              const time = PERIOD_TIME[slotIdx];

              return (
                <tr
                  key={slotIdx}
                  className={slotIdx < 5 ? "morning-row" : "afternoon-row"}
                >
                  {isFirstMorning && (
                    <td className="session-cell morning-cell" rowSpan={5}>
                      <span className="session-label">MORNING</span>
                    </td>
                  )}
                  {isFirstAfternoon && (
                    <td className="session-cell afternoon-cell" rowSpan={4}>
                      <span className="session-label">AFTERNOON</span>
                    </td>
                  )}

                  <td className="period-cell">
                    <span className="period-num">{slotIdx + 1}</span>
                  </td>

                  <td className="time-cell">
                    <span className="time-range">
                      {time ? `${time.start}–${time.end}` : `P${slotIdx + 1}`}
                    </span>
                  </td>

                  {rooms.map((room) => {
                    const grid = roomGrids.get(room.id)!;
                    const cell = grid[slotIdx];
                    const cellKey = `${room.id}-${slotIdx}`;
                    const hasConflict = conflictCells.has(cellKey);

                    if (cell.type === "covered") return null;

                    if (cell.type === "start") {
                      const { gene, rowSpan } = cell;
                      const course = courseMap.get(gene.courseId);
                      const lecturer = lecturerMap.get(gene.lecturerId);
                      const color = getLecturerColor(gene.lecturerId);

                      return (
                        <td
                          key={room.id}
                          className={`grid-td occupied ${hasConflict ? "conflict" : ""}`}
                          rowSpan={rowSpan}
                        >
                          <div
                            className="cell-content spanning"
                            style={{
                              backgroundColor: color,
                              borderColor: color,
                            }}
                            onClick={(e) => handleCardClick(gene, e)}
                          >
                            <span className="cell-name">
                              {gene.courseName || (course ? `${course.courseCode} – ${course.name}` : `Môn ${gene.courseId}`)}
                            </span>
                            <span className="cell-room">
                              {gene.roomName || (room?.name || `Phòng ${gene.roomId}`)}
                            </span>
                            <span className="cell-lecturer">
                              {gene.lecturerName || (lecturer?.name || `GV ${gene.lecturerId}`)}
                            </span>
                          </div>
                        </td>
                      );
                    }

                    return (
                      <td
                        key={room.id}
                        className={`grid-td empty ${hasConflict ? "conflict" : ""}`}
                      ></td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Detail popup */}
      {popup && (
        <div className="detail-overlay" onClick={closePopup}>
          <div
            className="detail-popup"
            style={{
              left: `${popup.x}px`,
              top: `${popup.y}px`,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="detail-row">
              <svg className="detail-icon" viewBox="0 0 24 24" fill="none" stroke="#1f5ca9" strokeWidth="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
              </svg>
              <span className="detail-text">{popup.courseName}</span>
            </div>
            <div className="detail-row">
              <svg className="detail-icon" viewBox="0 0 24 24" fill="none" stroke="#1f5ca9" strokeWidth="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                <circle cx="12" cy="10" r="3" />
              </svg>
              <span className="detail-text">{popup.roomName}</span>
            </div>
            <div className="detail-row">
              <svg className="detail-icon" viewBox="0 0 24 24" fill="none" stroke="#1f5ca9" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
              <span className="detail-text">{popup.lecturerName}</span>
            </div>
            <div className="detail-row">
              <svg className="detail-icon" viewBox="0 0 24 24" fill="none" stroke="#1f5ca9" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
              <span className="detail-text">{popup.timeRange} ({popup.units} tiết)</span>
            </div>
          </div>
        </div>
      )}

      <ConflictPanel />
    </div>
  );
}
