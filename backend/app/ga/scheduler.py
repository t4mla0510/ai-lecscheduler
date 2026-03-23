import dataclasses
import random
from typing import List, Dict, Any, Optional, cast
from app.schemas import Course, Lecturer, Room, TimeSlot
from app.db import cache, db

from app.schemas.chromosome import Chromosome
from app.ga.initializer import initialize_population
from app.ga.fitness import pick_fitness_method, analyze_solution
from app.ga.selection import pick_selection_method
from app.ga.elitism import get_elites
from app.ga.mutation import (
    random_reassignment_mutation,
    swap_mutation,
    creep_mutation,
)
from app.ga.stopping import StoppingCondition


class TraceGene:
    def __init__(self, course_id: int, timeslot_id: int, room_id: int):
        self.course_id = course_id
        self.timeslot_id = timeslot_id
        self.room_id = room_id


class TraceChromosome:
    def __init__(
        self, chrom_id: str, fitness: float, role: str, genes: List[TraceGene]
    ):
        self.id = chrom_id
        self.fitness = fitness
        self.role = role  # "elite" | "survivor" | "offspring" | "normal"
        self.genes = genes


class CrossoverEvent:
    def __init__(
        self,
        parent_a: str,
        parent_b: str,
        child_a: str,
        child_b: str,
        method: str,
        points: Optional[List[int]] = None,
    ):
        self.kind = "crossover"
        self.parent_a = parent_a
        self.parent_b = parent_b
        self.child_a = child_a
        self.child_b = child_b
        self.method = method
        self.points = points


class MutationEvent:
    def __init__(
        self,
        chrom_id: str,
        mutation_type: str,
        gene_idx: Optional[int] = None,
        gene_idx_a: Optional[int] = None,
        gene_idx_b: Optional[int] = None,
        field: Optional[str] = None,
        old_value: Optional[int] = None,
        new_value: Optional[int] = None,
    ):
        self.kind = "mutate"
        self.chrom_id = chrom_id
        self.type = mutation_type
        self.gene_idx = gene_idx
        self.gene_idx_a = gene_idx_a
        self.gene_idx_b = gene_idx_b
        self.field = field
        self.old_value = old_value
        self.new_value = new_value


class TrackedChromosome(Chromosome):
    _id_counter = 0

    def __init__(self, genes: list, fitness: Any = 0.0, chrom_id: Optional[str] = None):
        super().__init__(genes, fitness)
        if chrom_id is None:
            TrackedChromosome._id_counter += 1
            self.id = f"C{TrackedChromosome._id_counter:03d}"
        else:
            self.id = chrom_id

    @classmethod
    def reset_counter(cls):
        cls._id_counter = 0


class GAScheduler:
    def __init__(self, request_data: Any):
        self.ga_cfg = request_data.ga
        self.fit_cfg = request_data.fitness
        self.sel_cfg = request_data.selection
        self.cross_cfg = request_data.crossover
        self.mut_cfg = request_data.mutation

        self._load_data()

        self.population: List[TrackedChromosome] = []
        self.best_chromosome: Optional[TrackedChromosome] = None
        self.best_fitness = None
        self.stopping = None
        self.generation_trace: List[Dict] = []

    def _load_data(self):
        courses = [Course.from_dict(c) for c in db.get_collection("courses")]
        lecturers = [Lecturer(**l) for l in db.get_collection("lecturers")]
        rooms = [Room(**r) for r in db.get_collection("rooms")]
        timeslots = [TimeSlot(**t) for t in db.get_collection("timeslots")]

        self.courses_dict = {c.id: c for c in courses}
        self.lecturers_dict = {l.id: l for l in lecturers}
        self.rooms_dict = {r.id: r for r in rooms}
        self.timeslots_dict = {t.id: t for t in timeslots}

        self.valid_slots_by_units = {}
        for units in range(1, 11):
            self.valid_slots_by_units[units] = [
                s
                for s in timeslots
                if s.start_period + units - 1 <= 9
                and not (s.start_period <= 5 and s.start_period + units - 1 >= 6)
            ]

        self.valid_rooms_by_course_id = {}
        for course in courses:
            self.valid_rooms_by_course_id[course.id] = [
                r
                for r in rooms
                if r.capacity >= course.studentsCount and r.type in course.roomType
            ]
            if not self.valid_rooms_by_course_id[course.id]:
                self.valid_rooms_by_course_id[course.id] = [
                    r for r in rooms if r.capacity >= course.studentsCount
                ]
            if not self.valid_rooms_by_course_id[course.id]:
                self.valid_rooms_by_course_id[course.id] = rooms

    def initialize(self):
        raw_pop, new_courses_dict = initialize_population(
            pop_size=self.ga_cfg.pop_size,
            courses=list(self.courses_dict.values()),
            rooms=list(self.rooms_dict.values()),
            timeslots=list(self.timeslots_dict.values()),
            valid_slots_by_units=self.valid_slots_by_units,
            valid_rooms_by_course_id=self.valid_rooms_by_course_id,
        )
        self.courses_dict = new_courses_dict
        self.population = [TrackedChromosome(genes=chrom.genes) for chrom in raw_pop]

    def evaluate(self, pop: List[TrackedChromosome]):
        extra_kwargs: Dict[str, Any] = {}
        if self.fit_cfg.method == "penalty":
            extra_kwargs = {
                "base_score": self.fit_cfg.base_score,
                "hard_penalty": self.fit_cfg.hard_penalty,
                "soft_bonus": self.fit_cfg.soft_bonus,
            }
        elif self.fit_cfg.method == "alpha_beta":
            extra_kwargs = {
                "alpha": self.fit_cfg.alpha,
                "beta": self.fit_cfg.beta,
            }

        for chrom in pop:
            pick_fitness_method(
                chromosome=chrom,
                courses_dict=self.courses_dict,
                lecturers_dict=self.lecturers_dict,
                rooms_dict=self.rooms_dict,
                timeslots_dict=self.timeslots_dict,
                method=self.fit_cfg.method,
                cache=cache,
                **extra_kwargs,
            )

    def _get_scalar_fitness(self, fitness: Any) -> float:
        if isinstance(fitness, tuple):
            return fitness[0] * 10000 + fitness[1]
        return float(fitness)

    def _chrom_to_trace_chrom(
        self, chrom: TrackedChromosome, role: str = "normal"
    ) -> TraceChromosome:
        genes = [TraceGene(g.course_id, g.timeslot_id, g.room_id) for g in chrom.genes]
        return TraceChromosome(
            chrom.id, self._get_scalar_fitness(chrom.fitness), role, genes
        )

    def _should_sample_generation(self, generation: int) -> bool:
        max_gens = self.ga_cfg.max_generations
        if generation == 0:
            return True
        if generation == max_gens - 1:
            return True
        if max_gens <= 20:
            return True
        sample_rate = max(1, max_gens // 10)
        return generation % sample_rate == 0

    def _record_trace_generation(
        self,
        generation: int,
        elites: List[Chromosome],
        selected: List[Chromosome],
        crossover_events: List[CrossoverEvent],
        mutation_events: List[MutationEvent],
    ):
        if not self._should_sample_generation(generation):
            return

        fit_values = [self._get_scalar_fitness(c.fitness) for c in self.population]

        chrom_traces = []
        for chrom in self.population:
            role = "elite" if chrom in elites else "normal"
            if chrom in selected:
                role = "survivor"
            if chrom in self.population[len(elites) :]:
                role = "offspring"
            chrom_traces.append(self._chrom_to_trace_chrom(chrom, role))

        trace = {
            "generation": generation,
            "best_fitness": max(fit_values),
            "avg_fitness": sum(fit_values) / len(fit_values),
            "worst_fitness": min(fit_values),
            "elite_ids": [cast(TrackedChromosome, e).id for e in elites],
            "selected_ids": [cast(TrackedChromosome, s).id for s in selected],
            "chromosomes": [
                {
                    "id": ct.id,
                    "fitness": ct.fitness,
                    "role": ct.role,
                    "genes": [
                        {
                            "course_id": g.course_id,
                            "timeslot_id": g.timeslot_id,
                            "room_id": g.room_id,
                        }
                        for g in ct.genes
                    ],
                }
                for ct in chrom_traces
            ],
            "crossover_events": [
                {
                    "kind": e.kind,
                    "parent_a": e.parent_a,
                    "parent_b": e.parent_b,
                    "child_a": e.child_a,
                    "child_b": e.child_b,
                    "method": e.method,
                    "points": e.points,
                }
                for e in crossover_events
            ],
            "mutation_events": [
                {
                    "kind": e.kind,
                    "chrom_id": e.chrom_id,
                    "type": e.type,
                    "gene_idx": e.gene_idx,
                    "gene_idx_a": e.gene_idx_a,
                    "gene_idx_b": e.gene_idx_b,
                    "field": e.field,
                    "old_value": e.old_value,
                    "new_value": e.new_value,
                }
                for e in mutation_events
            ],
        }
        self.generation_trace.append(trace)

    def run_generator(self):
        TrackedChromosome.reset_counter()
        self.initialize()

        max_stall = max(5, int(self.ga_cfg.max_generations * 0.05))
        self.stopping = StoppingCondition(
            max_generations=self.ga_cfg.max_generations,
            target_fitness=self.ga_cfg.target_fitness,
            max_time_seconds=self.ga_cfg.max_time_seconds,
            max_stall_generations=max_stall,
            base_mutation_rate=self.mut_cfg.rate,
            max_mutation_rate=min(0.3, self.mut_cfg.rate * 3),
        )
        self.stopping.reset()

        self.evaluate(self.population)

        stop_reason = "Completed max generations"
        generation_run = 0

        for generation in range(self.ga_cfg.max_generations):
            generation_run = generation

            current_best = max(self.population, key=lambda ind: ind.fitness)
            current_best_fitness = current_best.fitness

            fits = []
            for ind in self.population:
                f = ind.fitness
                fits.append(float(f[0]) if isinstance(f, tuple) else float(f))

            yield {
                "type": "progress",
                "generation": generation,
                "best": max(fits),
                "avg": sum(fits) / len(fits),
                "worst": min(fits),
            }

            scalar_fitness = self._get_scalar_fitness(current_best_fitness)

            best_scalar = (
                self._get_scalar_fitness(self.best_fitness)
                if self.best_fitness is not None
                else float("-inf")
            )
            if self.best_chromosome is None or scalar_fitness > best_scalar:
                self.best_fitness = current_best_fitness
                self.best_chromosome = TrackedChromosome(
                    genes=[dataclasses.replace(g) for g in current_best.genes],
                    fitness=current_best_fitness,
                    chrom_id=current_best.id,
                )

            should_stop, stop_reason = self.stopping.check_stop_and_adapt(
                generation, float(scalar_fitness)
            )
            if should_stop:
                break

            elites = get_elites(
                cast(List[Chromosome], self.population), self.ga_cfg.elitism_rate
            )
            elite_chroms: List[TrackedChromosome] = [
                c for c in self.population if c in elites
            ]
            if not elite_chroms:
                sorted_pop = sorted(
                    self.population, key=lambda x: x.fitness, reverse=True
                )
                elite_chroms = sorted_pop[: self.ga_cfg.elitism_rate]

            num_offspring_needed = self.ga_cfg.pop_size - len(elite_chroms)
            parents: List[TrackedChromosome] = pick_selection_method(
                population=cast(List[Chromosome], self.population),
                num_parents=num_offspring_needed,
                method=self.sel_cfg.method,
                tournament_k=self.sel_cfg.tournament_k,
            )

            crossover_events = self._perform_crossover_with_trace(list(parents))
            mutation_events = self._perform_mutation_with_trace(
                list(self.population), self.stopping.current_mutation_rate
            )

            offspring = []
            for i in range(0, len(parents), 2):
                if i + 1 < len(parents):
                    child_a = TrackedChromosome(
                        genes=[dataclasses.replace(g) for g in parents[i].genes]
                    )
                    child_b = TrackedChromosome(
                        genes=[dataclasses.replace(g) for g in parents[i + 1].genes]
                    )
                    offspring.extend([child_a, child_b])
                else:
                    offspring.append(
                        TrackedChromosome(
                            genes=[dataclasses.replace(g) for g in parents[i].genes]
                        )
                    )

            for event in crossover_events:
                for j, chrom in enumerate(offspring):
                    if chrom.id == event.child_a or chrom.id == event.child_b:
                        crossover_events[j].child_a = event.child_a
                        crossover_events[j].child_b = event.child_b

            self._record_trace_generation(
                generation,
                elite_chroms,
                list(parents),
                crossover_events,
                mutation_events,
            )  # type: ignore

            self.evaluate(offspring)
            self.population = elite_chroms + offspring[: len(elite_chroms)]

        sorted_pop = sorted(self.population, key=lambda x: x.fitness, reverse=True)
        if self.best_chromosome is None and sorted_pop:
            self.best_chromosome = sorted_pop[0]

        analysis = analyze_solution(
            self.best_chromosome,
            self.courses_dict,
            self.lecturers_dict,
            self.rooms_dict,
            self.timeslots_dict,
        )

        yield {
            "type": "final",
            "best_chromosome": self.best_chromosome,
            "best_fitness": self.best_fitness,
            "generations_run": generation_run + 1,
            "stop_reason": stop_reason,
            "hard_constraints": analysis["hard_constraints"],
            "soft_constraints": analysis["soft_constraints"],
            "courses_dict": self.courses_dict,
            "lecturers_dict": self.lecturers_dict,
            "rooms_dict": self.rooms_dict,
            "trace": self.generation_trace,
        }

    def _perform_crossover_with_trace(
        self, parents: List[TrackedChromosome]
    ) -> List[CrossoverEvent]:
        events = []
        pop_size = len(parents)
        cross_rate = self.cross_cfg.rate
        method = self.cross_cfg.method

        for i in range(0, pop_size, 2):
            parent1 = parents[i]
            parent2 = parents[i + 1] if i + 1 < pop_size else random.choice(parents)

            if random.random() < cross_rate:
                p1_copy = TrackedChromosome(
                    genes=[dataclasses.replace(g) for g in parent1.genes],
                    chrom_id=f"{parent1.id}-P",
                )
                p2_copy = TrackedChromosome(
                    genes=[dataclasses.replace(g) for g in parent2.genes],
                    chrom_id=f"{parent2.id}-P",
                )

                if method == "single_point":
                    c1, c2, points = self._do_single_point(p1_copy, p2_copy)
                elif method == "two_point":
                    c1, c2, points = self._do_two_point(p1_copy, p2_copy)
                elif method == "multi_point":
                    c1, c2, points = self._do_multi_point(
                        p1_copy, p2_copy, self.cross_cfg.n_points
                    )
                elif method == "uniform":
                    c1, c2, points = self._do_uniform(p1_copy, p2_copy)
                else:
                    c1, c2, points = self._do_single_point(p1_copy, p2_copy)

                events.append(
                    CrossoverEvent(
                        parent_a=parent1.id,
                        parent_b=parent2.id,
                        child_a=c1.id,
                        child_b=c2.id,
                        method=method,
                        points=points,
                    )
                )

        return events

    def _do_single_point(self, p1: TrackedChromosome, p2: TrackedChromosome):
        length = len(p1.genes)
        if length <= 1:
            return p1, p2, None
        point = random.randint(1, length - 1)
        c1 = TrackedChromosome(
            genes=[dataclasses.replace(g) for g in p1.genes[:point]]
            + [dataclasses.replace(g) for g in p2.genes[point:]]
        )
        c2 = TrackedChromosome(
            genes=[dataclasses.replace(g) for g in p2.genes[:point]]
            + [dataclasses.replace(g) for g in p1.genes[point:]]
        )
        return c1, c2, [point]

    def _do_two_point(self, p1: TrackedChromosome, p2: TrackedChromosome):
        length = len(p1.genes)
        if length < 3:
            return self._do_single_point(p1, p2)
        point1 = random.randint(1, length - 2)
        point2 = random.randint(point1 + 1, length - 1)
        c1_genes = (
            [dataclasses.replace(g) for g in p1.genes[:point1]]
            + [dataclasses.replace(g) for g in p2.genes[point1:point2]]
            + [dataclasses.replace(g) for g in p1.genes[point2:]]
        )
        c2_genes = (
            [dataclasses.replace(g) for g in p2.genes[:point1]]
            + [dataclasses.replace(g) for g in p1.genes[point1:point2]]
            + [dataclasses.replace(g) for g in p2.genes[point2:]]
        )
        return (
            TrackedChromosome(genes=c1_genes),
            TrackedChromosome(genes=c2_genes),
            [point1, point2],
        )

    def _do_multi_point(self, p1: TrackedChromosome, p2: TrackedChromosome, n: int):
        length = len(p1.genes)
        if length <= n:
            return self._do_single_point(p1, p2)
        points = sorted(random.sample(range(1, length), n))
        c1_genes, c2_genes = [], []
        curr_p1, curr_p2 = p1.genes, p2.genes
        last_point = 0
        for pt in points:
            c1_genes.extend([dataclasses.replace(g) for g in curr_p1[last_point:pt]])
            c2_genes.extend([dataclasses.replace(g) for g in curr_p2[last_point:pt]])
            curr_p1, curr_p2 = curr_p2, curr_p1
            last_point = pt
        c1_genes.extend([dataclasses.replace(g) for g in curr_p1[last_point:]])
        c2_genes.extend([dataclasses.replace(g) for g in curr_p2[last_point:]])
        return (
            TrackedChromosome(genes=c1_genes),
            TrackedChromosome(genes=c2_genes),
            points,
        )

    def _do_uniform(self, p1: TrackedChromosome, p2: TrackedChromosome):
        c1_genes, c2_genes = [], []
        for g1, g2 in zip(p1.genes, p2.genes):
            if random.random() < 0.5:
                c1_genes.append(dataclasses.replace(g1))
                c2_genes.append(dataclasses.replace(g2))
            else:
                c1_genes.append(dataclasses.replace(g2))
                c2_genes.append(dataclasses.replace(g1))
        return (
            TrackedChromosome(genes=c1_genes),
            TrackedChromosome(genes=c2_genes),
            None,
        )

    def _perform_mutation_with_trace(
        self, population: List[TrackedChromosome], mutation_rate: float
    ) -> List[MutationEvent]:
        events = []
        method = self.mut_cfg.method

        for chromosome in population:
            if random.random() < mutation_rate:
                actual_method = method
                if random.random() < 0.1:
                    actual_method = random.choice(
                        ["swap", "heuristic", "creep", "random"]
                    )

                if actual_method == "swap":
                    old_genes = [(g.timeslot_id, g.room_id) for g in chromosome.genes]
                    swap_mutation(chromosome)
                    new_genes = [(g.timeslot_id, g.room_id) for g in chromosome.genes]
                    for idx, (old, new) in enumerate(zip(old_genes, new_genes)):
                        if old != new:
                            events.append(
                                MutationEvent(
                                    chrom_id=chromosome.id,
                                    mutation_type="swap",
                                    gene_idx_a=idx,
                                    gene_idx_b=next(
                                        (
                                            j
                                            for j, (o, n) in enumerate(
                                                zip(old_genes, new_genes)
                                            )
                                            if j != idx
                                            and o == new_genes[idx]
                                            and n == old_genes[idx]
                                        ),
                                        None,
                                    ),
                                )
                            )
                            break

                elif actual_method == "creep":
                    if chromosome.genes:
                        gene_idx = random.randint(0, len(chromosome.genes) - 1)
                        old_timeslot = chromosome.genes[gene_idx].timeslot_id
                        creep_mutation(
                            chromosome.genes[gene_idx],
                            list(self.timeslots_dict.values()),
                            valid_slots_by_units=self.valid_slots_by_units,
                        )
                        new_timeslot = chromosome.genes[gene_idx].timeslot_id
                        if old_timeslot != new_timeslot:
                            events.append(
                                MutationEvent(
                                    chrom_id=chromosome.id,
                                    mutation_type="creep",
                                    gene_idx=gene_idx,
                                    field="timeslot_id",
                                    old_value=old_timeslot,
                                    new_value=new_timeslot,
                                )
                            )

                else:
                    num_to_mutate = max(1, len(chromosome.genes) // 20)
                    if len(chromosome.genes) >= num_to_mutate:
                        indices = random.sample(
                            range(len(chromosome.genes)), num_to_mutate
                        )
                        for gene_idx in indices:
                            old_timeslot = chromosome.genes[gene_idx].timeslot_id
                            old_room = chromosome.genes[gene_idx].room_id
                            random_reassignment_mutation(
                                chromosome.genes[gene_idx],
                                list(self.rooms_dict.values()),
                                list(self.timeslots_dict.values()),
                                self.courses_dict,
                                valid_slots_by_units=self.valid_slots_by_units,
                                valid_rooms_by_course_id=self.valid_rooms_by_course_id,
                            )
                            new_timeslot = chromosome.genes[gene_idx].timeslot_id
                            new_room = chromosome.genes[gene_idx].room_id
                            if old_timeslot != new_timeslot:
                                events.append(
                                    MutationEvent(
                                        chrom_id=chromosome.id,
                                        mutation_type="random",
                                        gene_idx=gene_idx,
                                        field="timeslot_id",
                                        old_value=old_timeslot,
                                        new_value=new_timeslot,
                                    )
                                )
                            elif old_room != new_room:
                                events.append(
                                    MutationEvent(
                                        chrom_id=chromosome.id,
                                        mutation_type="random",
                                        gene_idx=gene_idx,
                                        field="room_id",
                                        old_value=old_room,
                                        new_value=new_room,
                                    )
                                )

        return events
