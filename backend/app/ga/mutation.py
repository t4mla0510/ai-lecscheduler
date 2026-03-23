import random


def random_reassignment_mutation(gene, rooms, timeslots, courses_dict=None, valid_slots_by_units=None, valid_rooms_by_course_id=None):
    mutate_type = random.choice(["timeslot", "room"])

    if mutate_type == "timeslot":
        if valid_slots_by_units:
            valid_slots = [
                s
                for s in valid_slots_by_units.get(gene.units, [])
                if s.id != gene.timeslot_id
            ]
        else:
            valid_slots = [
                s
                for s in timeslots
                if s.start_period + gene.units - 1 <= 9
                and s.id != gene.timeslot_id
                and not (s.start_period <= 5 and s.start_period + gene.units - 1 >= 6)
            ]
        if valid_slots:
            gene.timeslot_id = random.choice(valid_slots).id
            return True

    elif mutate_type == "room":
        if valid_rooms_by_course_id:
            valid_rooms = [r for r in valid_rooms_by_course_id.get(gene.course_id, []) if r.id != gene.room_id]
        else:
            valid_rooms = [r for r in rooms if r.id != gene.room_id]
            if courses_dict:
                course = courses_dict[gene.course_id]
                valid_rooms = [r for r in valid_rooms if r.capacity >= course.studentsCount]

        if valid_rooms:
            gene.room_id = random.choice(valid_rooms).id
            return True

    return False


def swap_mutation(chromosome):
    unit_groups = {}
    for i, gene in enumerate(chromosome.genes):
        unit_groups.setdefault(gene.units, []).append(i)

    valid_groups = {k: v for k, v in unit_groups.items() if len(v) >= 2}
    if not valid_groups:
        return False

    chosen_units = random.choice(list(valid_groups.keys()))
    idx1, idx2 = random.sample(valid_groups[chosen_units], 2)

    gene1, gene2 = chromosome.genes[idx1], chromosome.genes[idx2]
    gene1.timeslot_id, gene2.timeslot_id = gene2.timeslot_id, gene1.timeslot_id
    gene1.room_id, gene2.room_id = gene2.room_id, gene1.room_id
    return True


def creep_mutation(gene, timeslots, valid_slots_by_units=None):
    current_slot = next((s for s in timeslots if s.id == gene.timeslot_id), None)
    if not current_slot:
        return False

    if valid_slots_by_units:
        base_slots = valid_slots_by_units.get(gene.units, [])
        valid_creeps = [
            s
            for s in base_slots
            if s.day == current_slot.day
            and s.id != current_slot.id
            and abs(s.start_period - current_slot.start_period) <= 2
        ]
    else:
        valid_creeps = [
            s
            for s in timeslots
            if s.day == current_slot.day
            and s.start_period + gene.units - 1 <= 9
            and s.id != current_slot.id
            and abs(s.start_period - current_slot.start_period) <= 2
            and not (s.start_period <= 5 and s.start_period + gene.units - 1 >= 6)
        ]

    if valid_creeps:
        gene.timeslot_id = random.choice(valid_creeps).id
        return True
    return False


def heuristic_mutation(
    chromosome,
    rooms,
    timeslots,
    courses_dict,
    lecturers_dict,
    rooms_dict,
    timeslots_dict,
    valid_slots_by_units=None,
    valid_rooms_by_course_id=None,
):
    faulty_genes = []

    lecturer_masks = {}
    room_masks = {}

    for gene in chromosome.genes:
        is_faulty = False
        course = courses_dict[gene.course_id]
        room = rooms_dict[gene.room_id]
        timeslot = timeslots_dict[gene.timeslot_id]

        start = timeslot.start_period
        end = start + gene.units - 1
        day = timeslot.day

        if (
            end > 9
            or (start <= 5 and end >= 6)
            or room.capacity < course.studentsCount
            or room.type not in course.roomType
        ):
            is_faulty = True

        period_mask = ((1 << gene.units) - 1) << (start - 1)

        lec_key = (course.lecturer_id, day)
        if lec_key not in lecturer_masks:
            lecturer_masks[lec_key] = 0
        if lecturer_masks[lec_key] & period_mask:
            is_faulty = True
        lecturer_masks[lec_key] |= period_mask

        room_key = (gene.room_id, day)
        if room_key not in room_masks:
            room_masks[room_key] = 0
        if room_masks[room_key] & period_mask:
            is_faulty = True
        room_masks[room_key] |= period_mask

        if is_faulty:
            faulty_genes.append(gene)

    mutations_done = 0
    if faulty_genes:
        num_to_fix = min(len(faulty_genes), max(1, len(chromosome.genes) // 10))
        target_genes = random.sample(faulty_genes, num_to_fix)

        for gene in target_genes:
            random_reassignment_mutation(
                gene, rooms, timeslots, courses_dict,
                valid_slots_by_units=valid_slots_by_units,
                valid_rooms_by_course_id=valid_rooms_by_course_id
            )
            mutations_done += 1

    return mutations_done


def mutate_population(
    population,
    lecturers,
    rooms,
    timeslots,
    method="random",
    mutation_rate=0.05,
    **kwargs,
):
    valid_slots_by_units = kwargs.get("valid_slots_by_units")
    valid_rooms_by_course_id = kwargs.get("valid_rooms_by_course_id")
    courses_dict = kwargs.get("courses_dict")

    for chromosome in population:
        if method == "swap":
            if random.random() < mutation_rate:
                swap_mutation(chromosome)

        elif method == "heuristic":
            if random.random() < mutation_rate:
                heuristic_mutation(
                    chromosome,
                    rooms,
                    timeslots,
                    courses_dict,
                    kwargs.get("lecturers_dict"),
                    kwargs.get("rooms_dict"),
                    kwargs.get("timeslots_dict"),
                    valid_slots_by_units=valid_slots_by_units,
                    valid_rooms_by_course_id=valid_rooms_by_course_id,
                )
        else:
            for gene in chromosome.genes:
                if random.random() < mutation_rate:
                    if method == "random":
                        random_reassignment_mutation(
                            gene, rooms, timeslots, courses_dict,
                            valid_slots_by_units=valid_slots_by_units,
                            valid_rooms_by_course_id=valid_rooms_by_course_id
                        )
                    elif method == "creep":
                        creep_mutation(gene, timeslots, valid_slots_by_units=valid_slots_by_units)
    return population
