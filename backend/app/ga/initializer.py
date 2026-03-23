import random
from app.schemas import Chromosome, Gene
from app.utils import expand_courses_to_sessions

TOP_K = 3


def initialize_population(
    pop_size,
    courses,
    rooms,
    timeslots,
    valid_slots_by_units=None,
    valid_rooms_by_course_id=None,
):
    courses = sort_courses(courses)
    sessions, new_courses_dict = expand_courses_to_sessions(courses, rooms)

    greedy_size = int(pop_size * 0.3)
    random_size = int(pop_size * 0.4)
    semi_size = pop_size - greedy_size - random_size

    population = [
        Chromosome(genes=generate_greedy_chromosome(
            sessions, rooms, timeslots, valid_slots_by_units, valid_rooms_by_course_id))
        for _ in range(greedy_size)
    ] + [
        Chromosome(genes=generate_random_chromosome(
            sessions, rooms, timeslots, valid_slots_by_units, valid_rooms_by_course_id))
        for _ in range(random_size)
    ] + [
        Chromosome(genes=generate_semi_greedy_chromosome(
            sessions, rooms, timeslots, valid_slots_by_units, valid_rooms_by_course_id))
        for _ in range(semi_size)
    ]

    random.shuffle(population)
    return population, new_courses_dict


def get_valid_slots(units, course_days, course_id, valid_slots_by_units, timeslots):
    if valid_slots_by_units:
        base_slots = valid_slots_by_units.get(units, [])
        valid_slots = [s for s in base_slots if s.day not in course_days.get(course_id, set())]
        if not valid_slots:
            valid_slots = base_slots
    else:
        valid_slots = [
            s for s in timeslots
            if s.start_period + units - 1 <= 9
            and not (s.start_period <= 5 and s.start_period + units - 1 >= 6)
            and s.day not in course_days.get(course_id, set())
        ]
        if not valid_slots:
            valid_slots = [
                s for s in timeslots
                if s.start_period + units - 1 <= 9
                and not (s.start_period <= 5 and s.start_period + units - 1 >= 6)
            ]
    return valid_slots


def get_valid_rooms(course, valid_rooms_by_course_id, rooms):
    return valid_rooms_by_course_id.get(course.id, rooms) if valid_rooms_by_course_id else rooms


def create_gene(room, course, slot, units, session_id):
    return Gene(
        room_id=room.id,
        course_id=course.id,
        timeslot_id=slot.id,
        units=units,
        session_id=session_id,
    )


def evaluate_option(course, room):
    score = 0
    if room.capacity >= course.studentsCount:
        score += 5
    if room.type in course.roomType:
        score += 5
    return score


def sort_courses(courses):
    return sorted(
        courses,
        key=lambda c: (c.studentsCount, c.unitsPerWeek, len(c.roomType)),
        reverse=True,
    )


def generate_random_chromosome(sessions, rooms, timeslots, valid_slots_by_units=None, valid_rooms_by_course_id=None):
    genes = []
    course_days = {}

    for session in sessions:
        course = session["course"]
        units = session["units"]
        session_id = session["session_id"]

        course_days.setdefault(course.id, set())
        available_rooms = get_valid_rooms(course, valid_rooms_by_course_id, rooms)
        room = random.choice(available_rooms)

        valid_slots = get_valid_slots(units, course_days, course.id, valid_slots_by_units, timeslots)
        if not valid_slots:
            continue

        slot = random.choice(valid_slots)
        course_days[course.id].add(slot.day)
        genes.append(create_gene(room, course, slot, units, session_id))

    return genes


def generate_greedy_chromosome(sessions, rooms, timeslots, valid_slots_by_units=None, valid_rooms_by_course_id=None):
    genes = []
    lecturer_occupied = {}
    room_occupied = {}
    course_days = {}

    for session in sessions:
        course = session["course"]
        units = session["units"]
        session_id = session["session_id"]
        lecturer_id = course.lecturer_id

        best_score = -1
        best_option = None
        course_days.setdefault(course.id, set())

        available_rooms = get_valid_rooms(course, valid_rooms_by_course_id, rooms)
        shuffled_rooms = list(available_rooms)
        random.shuffle(shuffled_rooms)

        available_slots = valid_slots_by_units.get(units, timeslots) if valid_slots_by_units else timeslots
        shuffled_slots = list(available_slots)
        random.shuffle(shuffled_slots)

        for room in shuffled_rooms:
            for slot in shuffled_slots:
                if not valid_slots_by_units and (slot.start_period + units - 1 > 9 or
                    (slot.start_period <= 5 and slot.start_period + units - 1 >= 6)):
                    continue
                if slot.day in course_days[course.id]:
                    continue

                start, end = slot.start_period, slot.start_period + units - 1
                occupied_periods = set(range(start, end + 1))

                lec_key = (lecturer_id, slot.day)
                if lec_key in lecturer_occupied and lecturer_occupied[lec_key] & occupied_periods:
                    continue

                room_key = (room.id, slot.day)
                if room_key in room_occupied and room_occupied[room_key] & occupied_periods:
                    continue

                score = evaluate_option(course, room)
                if score > best_score:
                    best_score = score
                    best_option = (room, slot, occupied_periods, lec_key, room_key)

        if best_option is None:
            valid_slots = get_valid_slots(units, course_days, course.id, valid_slots_by_units, timeslots)
            room = random.choice(available_rooms)
            slot = random.choice(valid_slots) if valid_slots else timeslots[0]
            start, end = slot.start_period, slot.start_period + units - 1
            occupied_periods = set(range(start, end + 1))
            lec_key = (lecturer_id, slot.day)
            room_key = (room.id, slot.day)
            best_option = (room, slot, occupied_periods, lec_key, room_key)

        room, slot, occupied_periods, lec_key, room_key = best_option
        course_days[course.id].add(slot.day)
        lecturer_occupied.setdefault(lec_key, set()).update(occupied_periods)
        room_occupied.setdefault(room_key, set()).update(occupied_periods)
        genes.append(create_gene(room, course, slot, units, session_id))

    return genes


def generate_semi_greedy_chromosome(sessions, rooms, timeslots, valid_slots_by_units=None, valid_rooms_by_course_id=None):
    genes = []
    lecturer_occupied = {}
    room_occupied = {}
    course_days = {}

    for session in sessions:
        course = session["course"]
        units = session["units"]
        session_id = session["session_id"]
        lecturer_id = course.lecturer_id

        candidates = []
        course_days.setdefault(course.id, set())

        available_rooms = get_valid_rooms(course, valid_rooms_by_course_id, rooms)
        shuffled_rooms = list(available_rooms)
        random.shuffle(shuffled_rooms)

        available_slots = valid_slots_by_units.get(units, timeslots) if valid_slots_by_units else timeslots
        shuffled_slots = list(available_slots)
        random.shuffle(shuffled_slots)

        for room in shuffled_rooms:
            for slot in shuffled_slots:
                if not valid_slots_by_units and (slot.start_period + units - 1 > 9 or
                    (slot.start_period <= 5 and slot.start_period + units - 1 >= 6)):
                    continue
                if slot.day in course_days[course.id]:
                    continue

                start, end = slot.start_period, slot.start_period + units - 1
                occupied_periods = set(range(start, end + 1))

                lec_key = (lecturer_id, slot.day)
                if lec_key in lecturer_occupied and lecturer_occupied[lec_key] & occupied_periods:
                    continue

                room_key = (room.id, slot.day)
                if room_key in room_occupied and room_occupied[room_key] & occupied_periods:
                    continue

                score = evaluate_option(course, room)
                candidates.append((score, room, slot, occupied_periods, lec_key, room_key))

        if not candidates:
            valid_slots = get_valid_slots(units, course_days, course.id, valid_slots_by_units, timeslots)
            room = random.choice(available_rooms)
            slot = random.choice(valid_slots) if valid_slots else timeslots[0]
            start, end = slot.start_period, slot.start_period + units - 1
            occupied_periods = set(range(start, end + 1))
            lec_key = (lecturer_id, slot.day)
            room_key = (room.id, slot.day)
            candidates.append((0, room, slot, occupied_periods, lec_key, room_key))

        candidates.sort(key=lambda x: x[0], reverse=True)
        _, room, slot, occupied_periods, lec_key, room_key = random.choice(candidates[:TOP_K])
        course_days[course.id].add(slot.day)
        lecturer_occupied.setdefault(lec_key, set()).update(occupied_periods)
        room_occupied.setdefault(room_key, set()).update(occupied_periods)
        genes.append(create_gene(room, course, slot, units, session_id))

    return genes
