import math
from typing import Any
from app.schemas import Chromosome, Course, Lecturer, Room, TimeSlot
from app.db import cache


def calculate_fitness_fast(
    chromosome: Chromosome,
    courses_dict: dict[int, Course],
    lecturers_dict: dict[int, Lecturer],
    rooms_dict: dict[int, Room],
    timeslots_dict: dict[int, TimeSlot],
    cache: Any = None,
) -> tuple[dict[str, int], dict[str, int]]:
    cache_key = None
    if cache is not None:
        cache_key = cache.make_gene_key(chromosome.genes)
        cached = cache.get_cached_fitness(cache_key)
        if cached is not None:
            return cached["hard"], cached["soft"]

    hard_counts = {
        "overlap_violations": 0,
        "time_violations": 0,
        "room_suitability_violations": 0,
        "daily_limit_violations": 0,
    }
    soft_scores = {
        "preference_score": 0,
        "workload_score": 0,
        "idle_time_score": 0,
        "movement_score": 0,
    }

    lecturer_masks = {}
    room_masks = {}
    lecturer_schedule_blocks = {}
    course_days = {}

    for gene in chromosome.genes:
        course = courses_dict[gene.course_id]
        lecturer = lecturers_dict[course.lecturer_id]
        room = rooms_dict[gene.room_id]
        timeslot = timeslots_dict[gene.timeslot_id]

        start_period = timeslot.start_period
        end_period = start_period + gene.units - 1
        day = timeslot.day

        if end_period > 9:
            hard_counts["time_violations"] += 1
        if start_period <= 5 and end_period >= 6:
            hard_counts["time_violations"] += 1

        if room.type not in course.roomType:
            hard_counts["room_suitability_violations"] += 1
        if room.capacity < course.studentsCount:
            hard_counts["room_suitability_violations"] += 1

        c_id = gene.course_id
        if c_id not in course_days:
            course_days[c_id] = 0
        
        day_bit = 1 << day
        if course_days[c_id] & day_bit:
            hard_counts["daily_limit_violations"] += 1
        course_days[c_id] |= day_bit

        if day in lecturer.preferenceDay:
            soft_scores["preference_score"] += 1

        period_mask = ((1 << gene.units) - 1) << (start_period - 1)
        
        lec_key = (course.lecturer_id, day)
        if lec_key not in lecturer_masks:
            lecturer_masks[lec_key] = 0
            lecturer_schedule_blocks[lec_key] = []
        
        if lecturer_masks[lec_key] & period_mask:
            hard_counts["overlap_violations"] += 1
        lecturer_masks[lec_key] |= period_mask
        lecturer_schedule_blocks[lec_key].append((start_period, end_period, gene.room_id))

        room_key = (gene.room_id, day)
        if room_key not in room_masks:
            room_masks[room_key] = 0
        if room_masks[room_key] & period_mask:
            hard_counts["overlap_violations"] += 1
        room_masks[room_key] |= period_mask

    for lec_key, schedule in lecturer_schedule_blocks.items():
        schedule.sort(key=lambda x: x[0])
        
        total_periods = 0
        last_e = -1
        last_r = -1
        consecutive_p = 0

        for idx, (s, e, r_id) in enumerate(schedule):
            dur = e - s + 1
            total_periods += dur
            
            if idx > 0:
                gap = s - last_e - 1
                if gap == 0:
                    consecutive_p += dur
                    if last_r == r_id:
                        soft_scores["movement_score"] += 1
                else:
                    if gap == 1:
                        soft_scores["idle_time_score"] -= 1
                    else:
                        soft_scores["idle_time_score"] -= gap
                    consecutive_p = dur
            else:
                consecutive_p = dur

            if consecutive_p > 5:
                soft_scores["workload_score"] -= 1
            
            last_e = e
            last_r = r_id

        if total_periods <= 8:
            soft_scores["workload_score"] += 1
        else:
            soft_scores["workload_score"] -= 1

    if cache is not None and cache_key is not None:
        cache.set_cached_fitness(cache_key, {"hard": hard_counts, "soft": soft_scores})

    return hard_counts, soft_scores


def evaluate_details(
    chromosome: Chromosome,
    courses_dict: dict[int, Course],
    lecturers_dict: dict[int, Lecturer],
    rooms_dict: dict[int, Room],
    timeslots_dict: dict[int, TimeSlot],
) -> tuple[dict[str, int], list[str], dict[str, int], list[str]]:
    hard_counts = {"overlap_violations": 0, "time_violations": 0, "room_suitability_violations": 0, "daily_limit_violations": 0}
    soft_scores = {"preference_score": 0, "workload_score": 0, "idle_time_score": 0, "movement_score": 0}
    hard_details = []
    soft_details = []

    lecturer_masks = {}
    room_masks = {}
    lecturer_schedule_blocks = {}
    course_days = {}

    for gene in chromosome.genes:
        course = courses_dict[gene.course_id]
        lecturer = lecturers_dict[course.lecturer_id]
        room = rooms_dict[gene.room_id]
        timeslot = timeslots_dict[gene.timeslot_id]

        start_p = timeslot.start_period
        end_p = start_p + gene.units - 1
        day = timeslot.day

        if end_p > 9:
            hard_counts["time_violations"] += 1
            hard_details.append(f"Vượt thời gian: Môn {course.name} kết thúc quá tiết 9 (Tiết {end_p})")
        if start_p <= 5 and end_p >= 6:
            hard_counts["time_violations"] += 1
            hard_details.append(f"Vắt ngang ca: Môn {course.name} bị kẹp giữa ca Sáng/Chiều")

        if room.type not in course.roomType:
            hard_counts["room_suitability_violations"] += 1
            hard_details.append(f"Loại phòng: Môn {course.name} cần {course.roomType}, xếp vào P.{room.id} ({room.type})")
        if room.capacity < course.studentsCount:
            hard_counts["room_suitability_violations"] += 1
            hard_details.append(f"Sức chứa: Môn {course.name} ({course.studentsCount} sv), xếp vào P.{room.name} (chứa {room.capacity})")

        if course.id not in course_days: course_days[course.id] = set()
        if day in course_days[course.id]:
            hard_counts["daily_limit_violations"] += 1
            hard_details.append(f"Giới hạn ngày: Môn {course.name} có nhiều hơn 1 buổi trên Ngày {day}")
        course_days[course.id].add(day)

        if day in lecturer.preferenceDay:
            soft_scores["preference_score"] += 1
            soft_details.append(f"GV {lecturer.name} dạy đúng ngày sở thích (Ngày {day})")

        period_mask = ((1 << gene.units) - 1) << (start_p - 1)
        l_key = (lecturer.id, day)
        if l_key not in lecturer_masks:
            lecturer_masks[l_key] = 0
            lecturer_schedule_blocks[l_key] = []
        if lecturer_masks[l_key] & period_mask:
            hard_counts["overlap_violations"] += 1
            hard_details.append(f"GV {lecturer.name} kẹt lịch Ngày {day}")
        lecturer_masks[l_key] |= period_mask
        lecturer_schedule_blocks[l_key].append((start_p, end_p, room.id, lecturer.name))

        r_key = (room.id, day)
        if r_key not in room_masks: room_masks[r_key] = 0
        if room_masks[r_key] & period_mask:
            hard_counts["overlap_violations"] += 1
            hard_details.append(f"Phòng {room.name} bị trùng lịch Ngày {day}")
        room_masks[r_key] |= period_mask

    for (l_id, day), schedule in lecturer_schedule_blocks.items():
        schedule.sort(key=lambda x: x[0])
        l_name = schedule[0][3]
        total_p = sum(e - s + 1 for s, e, _, _ in schedule)
        if total_p <= 8:
            soft_scores["workload_score"] += 1
            soft_details.append(f"GV {l_name} Ngày {day}: Tải hợp lý ({total_p} tiết)")
        else:
            soft_scores["workload_score"] -= 1
            soft_details.append(f"GV {l_name} Ngày {day}: Quá tải ({total_p} tiết)")

        last_e, last_r = -1, -1
        consecutive_p = 0
        for idx, (s, e, r_id, _) in enumerate(schedule):
            dur = e - s + 1
            if idx == 0:
                consecutive_p = dur
            else:
                gap = s - last_e - 1
                if gap == 0:
                    consecutive_p += dur
                    if last_r == r_id:
                        soft_scores["movement_score"] += 1
                        soft_details.append(f"GV {l_name} Ngày {day}: Cùng phòng P.{r_id}")
                else:
                    consecutive_p = dur
                    if gap == 1:
                        soft_scores["idle_time_score"] -= 1
                        soft_details.append(f"GV {l_name} Ngày {day}: Chờ 1 tiết")
                    else:
                        soft_scores["idle_time_score"] -= gap
                        soft_details.append(f"GV {l_name} Ngày {day}: Chờ {gap} tiết")
            last_e, last_r = e, r_id
            if consecutive_p > 5:
                soft_scores["workload_score"] -= 1
                soft_details.append(f"GV {l_name} Ngày {day}: Dạy liên tục {consecutive_p} tiết")

    return hard_counts, hard_details, soft_scores, soft_details


def analyze_solution(chromosome, courses_dict, lecturers_dict, rooms_dict, timeslots_dict):
    h_counts, h_details, s_scores, s_details = evaluate_details(
        chromosome, courses_dict, lecturers_dict, rooms_dict, timeslots_dict
    )
    return {
        "hard_constraints": {"total_violations": sum(h_counts.values()), "by_type": h_counts, "details": h_details},
        "soft_constraints": {"total_score": sum(s_scores.values()), "by_type": s_scores, "details": s_details},
    }


def penalty_fitness(chromosome, courses_dict, lecturers_dict, rooms_dict, timeslots_dict, cache=None, **kwargs):
    h_counts, s_scores = calculate_fitness_fast(chromosome, courses_dict, lecturers_dict, rooms_dict, timeslots_dict, cache)
    penalty = sum(h_counts.values()) * kwargs.get("hard_penalty", 100)
    bonus = sum(s_scores.values()) * kwargs.get("soft_bonus", 5)
    chromosome.fitness = kwargs.get("base_score", 1000) - penalty + bonus
    return chromosome.fitness


def alpha_beta_fitness(chromosome, courses_dict, lecturers_dict, rooms_dict, timeslots_dict, cache=None, **kwargs):
    h_counts, s_scores = calculate_fitness_fast(chromosome, courses_dict, lecturers_dict, rooms_dict, timeslots_dict, cache)
    score_hard = kwargs.get("alpha", 1000) * (1 / (1 + sum(h_counts.values())))
    score_soft = kwargs.get("beta", 10) * max(0, sum(s_scores.values()))
    chromosome.fitness = score_hard + score_soft
    return chromosome.fitness


def weighted_fitness(chromosome, courses_dict, lecturers_dict, rooms_dict, timeslots_dict, cache=None, **kwargs):
    h_counts, s_scores = calculate_fitness_fast(chromosome, courses_dict, lecturers_dict, rooms_dict, timeslots_dict, cache)
    
    # Weights
    w_hard = {"overlap": 0.40, "time": 0.10, "room": 0.10, "daily": 0.10}
    w_soft = {"pref": 0.15, "work": 0.07, "idle": 0.05, "move": 0.03}

    score_h = (
        w_hard["overlap"] * (1.0 / (1.0 + h_counts["overlap_violations"])) +
        w_hard["time"] * (1.0 / (1.0 + h_counts["time_violations"])) +
        w_hard["room"] * (1.0 / (1.0 + h_counts["room_suitability_violations"])) +
        w_hard["daily"] * (1.0 / (1.0 + h_counts["daily_limit_violations"]))
    )

    def sig(v): return 1 / (1 + math.exp(-v))
    score_s = (
        w_soft["pref"] * sig(s_scores["preference_score"]) +
        w_soft["work"] * sig(s_scores["workload_score"]) +
        w_soft["idle"] * sig(s_scores["idle_time_score"]) +
        w_soft["move"] * sig(s_scores["movement_score"])
    )

    chromosome.fitness = score_h + score_s
    return chromosome.fitness


def lexicographic_fitness(chromosome, courses_dict, lecturers_dict, rooms_dict, timeslots_dict, cache=None, **kwargs):
    h_counts, s_scores = calculate_fitness_fast(chromosome, courses_dict, lecturers_dict, rooms_dict, timeslots_dict, cache)
    chromosome.fitness = (-sum(h_counts.values()), sum(s_scores.values()))
    return chromosome.fitness


FITNESS_METHODS = {
    "weighted": weighted_fitness,
    "penalty": penalty_fitness,
    "alpha_beta": alpha_beta_fitness,
    "lexicographic": lexicographic_fitness,
}

def pick_fitness_method(chromosome, courses_dict, lecturers_dict, rooms_dict, timeslots_dict, method="weighted", cache=None, **kwargs):
    return FITNESS_METHODS.get(method, weighted_fitness)(
        chromosome, courses_dict, lecturers_dict, rooms_dict, timeslots_dict, cache=cache, **kwargs
    )
