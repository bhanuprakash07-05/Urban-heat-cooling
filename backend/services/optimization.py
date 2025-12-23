import numpy as np
from scipy.optimize import differential_evolution
import random

class InterventionOptimizer:
    """Genetic Algorithm optimizer for intervention selection"""
    
    def __init__(self):
        self.population_size = 50
        self.generations = 100
        self.mutation_rate = 0.1
        self.crossover_rate = 0.8
    
    def optimize_interventions(self, interventions, constraints):
        """Multi-objective optimization using Genetic Algorithm"""
        
        # Define fitness function
        def fitness_function(allocation):
            total_cost = sum(allocation[i] * interventions[i]['cost'] 
                           for i in range(len(interventions)))
            
            if total_cost > constraints['max_budget']:
                return -1000  # Penalty for budget violation
            
            # Multi-criteria fitness
            temperature_reduction = sum(allocation[i] * interventions[i]['cooling_effect'] 
                                      for i in range(len(interventions)))
            
            feasibility_score = sum(allocation[i] * interventions[i]['feasibility'] 
                                  for i in range(len(interventions)))
            
            community_impact = sum(allocation[i] * interventions[i]['community_benefit'] 
                                 for i in range(len(interventions)))
            
            # Weighted fitness (matching criteria weights)
            fitness = (
                temperature_reduction * 0.40 +
                feasibility_score * 0.20 +
                community_impact * 0.15 +
                (constraints['max_budget'] - total_cost) / constraints['max_budget'] * 0.25
            )
            
            return fitness
        
        # Define bounds for allocation (0 to 1 for each intervention)
        bounds = [(0, 1) for _ in interventions]
        
        # Run differential evolution optimization
        result = differential_evolution(
            lambda x: -fitness_function(x),  # Minimize negative fitness
            bounds,
            maxiter=self.generations,
            popsize=15,
            seed=42
        )
        
        optimal_allocation = result.x
        
        # Convert to interpretable results
        selected_interventions = []
        total_budget_used = 0
        total_cooling = 0
        
        for i, allocation in enumerate(optimal_allocation):
            if allocation > 0.1:  # Threshold for inclusion
                selected_interventions.append({
                    'intervention_id': interventions[i]['id'],
                    'allocation_percentage': round(allocation * 100, 1),
                    'estimated_cost': interventions[i]['cost'] * allocation,
                    'expected_cooling': interventions[i]['cooling_effect'] * allocation
                })
                total_budget_used += interventions[i]['cost'] * allocation
                total_cooling += interventions[i]['cooling_effect'] * allocation
        
        return {
            'optimal_interventions': selected_interventions,
            'optimization_summary': {
                'total_budget_utilized': round(total_budget_used, 0),
                'expected_cooling_effect': round(total_cooling, 2),
                'fitness_score': round(-result.fun, 3),
                'convergence_achieved': result.success,
                'optimization_iterations': result.nit
            },
            'algorithm_params': {
                'population_size': self.population_size,
                'generations_run': result.nit,
                'mutation_rate': self.mutation_rate,
                'crossover_rate': self.crossover_rate
            }
        }
    
    def multi_criteria_decision_analysis(self, alternatives, criteria_weights):
        """MCDA using TOPSIS method"""
        
        # Normalize decision matrix
        decision_matrix = np.array([[alt[criterion] for criterion in criteria_weights.keys()] 
                                  for alt in alternatives])
        
        # Normalize columns
        normalized_matrix = decision_matrix / np.sqrt(np.sum(decision_matrix**2, axis=0))
        
        # Apply weights
        weighted_matrix = normalized_matrix * list(criteria_weights.values())
        
        # Determine ideal solutions
        ideal_best = np.max(weighted_matrix, axis=0)
        ideal_worst = np.min(weighted_matrix, axis=0)
        
        # Calculate distances
        distances_to_best = np.sqrt(np.sum((weighted_matrix - ideal_best)**2, axis=1))
        distances_to_worst = np.sqrt(np.sum((weighted_matrix - ideal_worst)**2, axis=1))
        
        # Calculate TOPSIS scores
        topsis_scores = distances_to_worst / (distances_to_best + distances_to_worst)
        
        # Rank alternatives
        ranked_alternatives = []
        for i, score in enumerate(topsis_scores):
            ranked_alternatives.append({
                'alternative_index': i,
                'topsis_score': round(score, 3),
                'rank': len(topsis_scores) - np.argsort(topsis_scores).tolist().index(i)
            })
        
        return sorted(ranked_alternatives, key=lambda x: x['topsis_score'], reverse=True)