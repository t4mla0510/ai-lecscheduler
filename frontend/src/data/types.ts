/* eslint-disable @typescript-eslint/no-explicit-any */
// Core data types for the timetable management application

export interface Lecturer {
    id: number;
    name: string;
    maxUnitPerWeek: number;
    preferenceDay: number[]; // 1=Mon ... 5=Fri
}

export interface Course {
    id: number;
    courseCode: string;
    name: string;
    unitsPerWeek: number;
    studentsCount: number;
    roomType: string[]; // ["Lecture","Lab"]
    lecturerId: number;
    maxUnitsPerDay: number;
}

export interface Room {
    id: number;
    name: string;
    capacity: number;
    type: string; // "Lecture" | "Lab"
}

export interface TimeSlot {
    id: number;
    day: number;          // 0-4 (Mon-Fri)
    start_period: number; // starting period (1-9)
}

export interface Gene {
    courseId: number;
    courseName?: string;
    lecturerId: number;
    lecturerName?: string;
    roomId: number;
    roomName?: string;
    timeslotId: number;
    units: number;
}

export type Chromosome = Gene[];

export interface HardConstraints {
    total_violations: number;
    by_type: Record<string, number>;
    details: string[];
}

export interface SoftConstraints {
    total_score: number;
    by_type: Record<string, number>;
    details: string[];
}

export interface GAResult {
    status: string;
    schedule: any[];
    generations: number;
    stop_reason: string;
    best_fitness: any;
    hard_constraints: HardConstraints;
    soft_constraints: SoftConstraints;
}

// --- GA configuration types matching backend ScheduleRequest ---

export interface FitnessConfig {
    method: string;       // "weighted" | "penalty" | "alpha_beta" | "lexicographic" | "traditional"
    base_score: number;
    hard_penalty: number;
    soft_bonus: number;
    alpha: number;
    beta: number;
}

export interface SelectionConfig {
    method: string;       // "roulette" | "tournament" | "rank" | "elimination"
    tournament_k: number;
}

export interface CrossoverConfig {
    method: string;       // "single_point" | "two_point" | "multi_point" | "uniform"
    rate: number;
    n_points: number;
}

export interface MutationConfig {
    method: string;       // "random" | "swap" | "creep" | "heuristic"
    rate: number;
}

export interface GARunConfig {
    pop_size: number;
    elitism_rate: number;
    max_generations: number;
    max_time_seconds: number;
    target_fitness: number | null;
}

export interface ScheduleRequest {
    fitness: FitnessConfig;
    selection: SelectionConfig;
    crossover: CrossoverConfig;
    mutation: MutationConfig;
    ga: GARunConfig;
}

export const ROOM_TYPES = ["Lecture", "Lab"];

export const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

// 9 periods/day × 5 days = 45 slots  →  backend timeslot IDs go up to 45
// Periods 1-5 = Morning, 6-9 = Afternoon
export const PERIODS_PER_DAY = 9;

export const PERIOD_TIME = [
    { start: "07:00", end: "07:50" },
    { start: "07:50", end: "08:40" },
    { start: "08:50", end: "09:40" },
    { start: "09:50", end: "10:40" },
    { start: "10:40", end: "11:30" },
    { start: "13:30", end: "14:20" },
    { start: "14:20", end: "15:10" },
    { start: "15:20", end: "16:10" },
    { start: "16:10", end: "17:00" },
];


