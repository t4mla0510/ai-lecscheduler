import axiosClient from "./axiosClient";
import type { GAResult, ScheduleRequest } from "../data/types";

export const scheduleApi = {
  generate: (config: ScheduleRequest) => {
    return axiosClient.post<GAResult>("/schedule/", config);
  },
};