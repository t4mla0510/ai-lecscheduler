import axiosClient from "./axiosClient";
import type { Course } from "../data/types";

export const courseApi = {
  getAll: () => axiosClient.get<Course[]>("/courses/"),

  getById: (id: number) =>
    axiosClient.get<Course>(`/courses/${id}`),

  create: (data: Course) =>
    axiosClient.post<Course>("/courses/", data),

  update: (id: number, data: Course) =>
    axiosClient.put<Course>(`/courses/${id}`, data),

  delete: (id: number) =>
    axiosClient.delete(`/courses/${id}`),
};