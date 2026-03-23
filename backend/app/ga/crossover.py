import random
import dataclasses
from app.schemas import Chromosome

def single_point_crossover(parent1: Chromosome, parent2: Chromosome):
    length = len(parent1.genes)
    if length <= 1:
        return Chromosome(genes=[dataclasses.replace(g) for g in parent1.genes]), Chromosome(genes=[dataclasses.replace(g) for g in parent2.genes])
    point = random.randint(1, length - 1)
    child1_genes = [dataclasses.replace(g) for g in parent1.genes[:point]] + [dataclasses.replace(g) for g in parent2.genes[point:]]
    child2_genes = [dataclasses.replace(g) for g in parent2.genes[:point]] + [dataclasses.replace(g) for g in parent1.genes[point:]]
    return Chromosome(genes=child1_genes), Chromosome(genes=child2_genes)

def two_point_crossover(parent1: Chromosome, parent2: Chromosome):
    length = len(parent1.genes)
    if length < 3:
        return single_point_crossover(parent1, parent2)
        
    point1 = random.randint(1, length - 2)
    point2 = random.randint(point1 + 1, length - 1)
    
    child1_genes = ([dataclasses.replace(g) for g in parent1.genes[:point1]] + 
                    [dataclasses.replace(g) for g in parent2.genes[point1:point2]] + 
                    [dataclasses.replace(g) for g in parent1.genes[point2:]])
                    
    child2_genes = ([dataclasses.replace(g) for g in parent2.genes[:point1]] + 
                    [dataclasses.replace(g) for g in parent1.genes[point1:point2]] + 
                    [dataclasses.replace(g) for g in parent2.genes[point2:]])
                    
    return Chromosome(genes=child1_genes), Chromosome(genes=child2_genes)

def uniform_crossover(parent1: Chromosome, parent2: Chromosome):
    child1_genes, child2_genes = [], []
    for g1, g2 in zip(parent1.genes, parent2.genes):
        if random.random() < 0.5:
            child1_genes.append(dataclasses.replace(g1))
            child2_genes.append(dataclasses.replace(g2))
        else:
            child1_genes.append(dataclasses.replace(g2))
            child2_genes.append(dataclasses.replace(g1))
    return Chromosome(genes=child1_genes), Chromosome(genes=child2_genes)

def multi_point_crossover(parent1: Chromosome, parent2: Chromosome, n=3):
    length = len(parent1.genes)
    if length <= n:
        return single_point_crossover(parent1, parent2)

    points = sorted(random.sample(range(1, length), n))
    
    child1_genes = []
    child2_genes = []
    
    curr_parent1, curr_parent2 = parent1.genes, parent2.genes
    last_point = 0
    
    for point in points:
        child1_genes.extend([dataclasses.replace(g) for g in curr_parent1[last_point:point]])
        child2_genes.extend([dataclasses.replace(g) for g in curr_parent2[last_point:point]])
        
        curr_parent1, curr_parent2 = curr_parent2, curr_parent1
        last_point = point
        
    child1_genes.extend([dataclasses.replace(g) for g in curr_parent1[last_point:]])
    child2_genes.extend([dataclasses.replace(g) for g in curr_parent2[last_point:]])
    
    return Chromosome(genes=child1_genes), Chromosome(genes=child2_genes)

# Cập nhật hàm điều phối chính
def crossover_population(population, method="single_point", crossover_rate=0.8, n_points=3):
    new_population = []
    pop_size = len(population)
    
    for i in range(0, pop_size, 2):
        parent1 = population[i]
        parent2 = population[i+1] if i+1 < pop_size else random.choice(population)
        
        if random.random() < crossover_rate:
            if method == "single_point":
                c1, c2 = single_point_crossover(parent1, parent2)
            elif method == "two_point":
                c1, c2 = two_point_crossover(parent1, parent2)
            elif method == "multi_point":
                c1, c2 = multi_point_crossover(parent1, parent2, n=n_points)
            elif method == "uniform":
                c1, c2 = uniform_crossover(parent1, parent2)
            else:
                c1, c2 = single_point_crossover(parent1, parent2)
            new_population.extend([c1, c2])
        else:
            new_population.extend([
                Chromosome(genes=[dataclasses.replace(g) for g in parent1.genes]),
                Chromosome(genes=[dataclasses.replace(g) for g in parent2.genes])
            ])
            
    return new_population[:pop_size]