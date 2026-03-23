import axiosClient from "./axiosClient";
import type { Lecturer } from "../data/types";

export const lecturerApi = {
  getAll: () => axiosClient.get<Lecturer[]>("/lecturers/"),

  getById: (id: number) =>
    axiosClient.get<Lecturer>(`/lecturers/${id}`),

  create: (data: Lecturer) =>
    axiosClient.post<Lecturer>("/lecturers/", data),

  update: (id: number, data: Lecturer) =>
    axiosClient.put<Lecturer>(`/lecturers/${id}`, data),

  delete: (id: number) =>
    axiosClient.delete(`/lecturers/${id}`),
};