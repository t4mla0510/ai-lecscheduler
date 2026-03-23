/* eslint-disable react-refresh/only-export-components */
// Application state management with React Context + useReducer
import {
  createContext,
  useContext,
  useReducer,
  type ReactNode,
} from "react";
import type {
  Lecturer,
  Course,
  Room,
  Chromosome,
  TimeSlot,
  HardConstraints,
  SoftConstraints,
  ScheduleRequest,
} from "./types";

export const defaultGAConfig: ScheduleRequest = {
  fitness: {
    method: "weighted",
    base_score: 1000,
    hard_penalty: 100,
    soft_bonus: 5,
    alpha: 1000,
    beta: 10,
  },
  selection: {
    method: "tournament",
    tournament_k: 3,
  },
  crossover: {
    method: "single_point",
    rate: 0.8,
    n_points: 3,
  },
  mutation: {
    method: "random",
    rate: 0.1,
  },
  ga: {
    pop_size: 100,
    elitism_rate: 0.05,
    max_generations: 500,
    max_time_seconds: 30,
    target_fitness: null,
  },
};

export interface AppState {
  lecturers: Lecturer[];
  courses: Course[];
  rooms: Room[];
  timetable: Chromosome | null;
  gaStatus: "idle" | "running" | "completed";
  fitnessHistory: number[];
  currentGeneration: number;
  bestFitness: number;
  currentPage: string;
  timeslots: TimeSlot[];
  hardConstraints: HardConstraints | null;
  softConstraints: SoftConstraints | null;
  gaConfig: ScheduleRequest;
}

type Action =
  | { type: "SET_LECTURERS"; payload: Lecturer[] }
  | { type: "SET_COURSES"; payload: Course[] }
  | { type: "SET_ROOMS"; payload: Room[] }
  | { type: "SET_TIMETABLE"; payload: Chromosome | null }
  | { type: "SET_GA_STATUS"; payload: "idle" | "running" | "completed" }
  | { type: "SET_FITNESS_HISTORY"; payload: number[] }
  | { type: "SET_CURRENT_GENERATION"; payload: number }
  | { type: "SET_BEST_FITNESS"; payload: number }
  | { type: "SET_PAGE"; payload: string }
  | { type: "ADD_LECTURER"; payload: Lecturer }
  | { type: "UPDATE_LECTURER"; payload: Lecturer }
  | { type: "REMOVE_LECTURER"; payload: number }
  | { type: "ADD_COURSE"; payload: Course }
  | { type: "UPDATE_COURSE"; payload: Course }
  | { type: "REMOVE_COURSE"; payload: number }
  | { type: "ADD_ROOM"; payload: Room }
  | { type: "UPDATE_ROOM"; payload: Room }
  | { type: "REMOVE_ROOM"; payload: number }
  | { type: "RESET_GA" }
  | { type: "LOAD_STATE"; payload: Partial<AppState> }
  | { type: "SET_TIMESLOTS"; payload: TimeSlot[] }
  | { type: "SET_HARD_CONSTRAINTS"; payload: HardConstraints | null }
  | { type: "SET_SOFT_CONSTRAINTS"; payload: SoftConstraints | null }
  | { type: "SET_GA_CONFIG"; payload: ScheduleRequest }

const initialState: AppState = {
  lecturers: [],
  courses: [],
  rooms: [],
  timetable: null,
  gaStatus: "idle",
  fitnessHistory: [],
  currentGeneration: 0,
  bestFitness: 0,
  currentPage: "dashboard",
  timeslots: [],
  hardConstraints: null,
  softConstraints: null,
  gaConfig: defaultGAConfig,
};

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {

    case "SET_LECTURERS":
      return { ...state, lecturers: action.payload };

    case "SET_COURSES":
      return { ...state, courses: action.payload };

    case "SET_ROOMS":
      return { ...state, rooms: action.payload };

    case "SET_TIMESLOTS":
      return { ...state, timeslots: action.payload };

    case "SET_TIMETABLE":
      return { ...state, timetable: action.payload };

    case "SET_GA_STATUS":
      return { ...state, gaStatus: action.payload };

    case "SET_FITNESS_HISTORY":
      return { ...state, fitnessHistory: action.payload };

    case "SET_CURRENT_GENERATION":
      return { ...state, currentGeneration: action.payload };

    case "SET_BEST_FITNESS":
      return { ...state, bestFitness: action.payload };

    case "SET_PAGE":
      return { ...state, currentPage: action.payload };

    case "ADD_LECTURER":
      return {
        ...state,
        lecturers: [...state.lecturers, action.payload]
      };

    case "UPDATE_LECTURER":
      return {
        ...state,
        lecturers: state.lecturers.map(l => l.id === action.payload.id ? action.payload : l)
      };

    case "REMOVE_LECTURER":
      return {
        ...state,
        lecturers: state.lecturers.filter(l => l.id !== action.payload)
      };

    case "ADD_COURSE":
      return {
        ...state,
        courses: [...state.courses, action.payload]
      };

    case "UPDATE_COURSE":
      return {
        ...state,
        courses: state.courses.map(c => c.id === action.payload.id ? action.payload : c)
      };

    case "REMOVE_COURSE":
      return {
        ...state,
        courses: state.courses.filter(c => c.id !== action.payload)
      };

    case "ADD_ROOM":
      return {
        ...state,
        rooms: [...state.rooms, action.payload]
      };

    case "UPDATE_ROOM":
      return {
        ...state,
        rooms: state.rooms.map(r => r.id === action.payload.id ? action.payload : r)
      };

    case "REMOVE_ROOM":
      return {
        ...state,
        rooms: state.rooms.filter(r => r.id !== action.payload)
      };

    case "RESET_GA":
      return {
        ...state,
        timetable: null,
        gaStatus: "idle",
        fitnessHistory: [],
        currentGeneration: 0,
        bestFitness: 0,
        hardConstraints: null,
        softConstraints: null,
        gaConfig: defaultGAConfig,
      };

    case "SET_HARD_CONSTRAINTS":
      return { ...state, hardConstraints: action.payload };

    case "SET_SOFT_CONSTRAINTS":
      return { ...state, softConstraints: action.payload };

    case "SET_GA_CONFIG":
      return { ...state, gaConfig: action.payload };

    case "LOAD_STATE":
      return { ...state, ...action.payload };

    default:
      return state;
  }
}

const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<Action>;
} | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppState() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppState must be used within AppProvider");
  return ctx;
}
