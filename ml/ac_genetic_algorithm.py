import numpy as np
import random
import json
import logging
from deap import base, creator, tools, algorithms

logger = logging.getLogger("ACGeneticOptimizer")


class ACGeneticOptimizer:
    def __init__(self):
        self.current_temp = 25.0
        self.current_humidity = 60.0
        self.occupancy = False
        self.person_count = 0
        self.POP_SIZE = 50
        self.NGEN = 30
        self.CXPB = 0.7
        self.MUTPB = 0.2
        self.COMFORT_TEMP_MIN = 22.0
        self.COMFORT_TEMP_MAX = 26.0
        self.COMFORT_HUM_MIN = 40.0
        self.COMFORT_HUM_MAX = 60.0
        self._setup_ga()

    def _setup_ga(self):
        if not hasattr(creator, "FitnessMulti"):
            creator.create("FitnessMulti", base.Fitness, weights=(-1.0, 1.0))
            creator.create("Individual", list, fitness=creator.FitnessMulti)
        self.toolbox = base.Toolbox()
        self.toolbox.register("ac_temp", random.randint, 16, 30)
        self.toolbox.register("fan_speed", random.randint, 1, 3)
        self.toolbox.register("duty_cycle", random.uniform, 0.0, 1.0)
        self.toolbox.register("individual", tools.initCycle, creator.Individual,
                              (self.toolbox.ac_temp, self.toolbox.fan_speed,
                               self.toolbox.duty_cycle), n=1)
        self.toolbox.register("population", tools.initRepeat, list,
                              self.toolbox.individual)
        self.toolbox.register("evaluate", self._fitness)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.2)
        self.toolbox.register("select", tools.selNSGA2)

    def _fitness(self, individual):
        ac_temp = int(np.clip(individual[0], 16, 30))
        fan_speed = int(np.clip(individual[1], 1, 3))
        duty_cycle = np.clip(individual[2], 0.0, 1.0)
        temp_diff = abs(self.current_temp - ac_temp)
        energy = (temp_diff * 0.1 + fan_speed * 0.15) * duty_cycle
        if not self.occupancy:
            energy += duty_cycle * 5.0
        comfort = 0.0
        if self.occupancy:
            predicted_temp = self.current_temp - (self.current_temp - ac_temp) * duty_cycle * 0.5
            if self.COMFORT_TEMP_MIN <= predicted_temp <= self.COMFORT_TEMP_MAX:
                comfort += 1.0
            else:
                comfort -= abs(predicted_temp - 24.0) * 0.1
            if self.COMFORT_HUM_MIN <= self.current_humidity <= self.COMFORT_HUM_MAX:
                comfort += 0.5
            if self.person_count > 2:
                optimal_temp = 24.0 - (self.person_count - 2) * 0.5
                comfort -= abs(predicted_temp - optimal_temp) * 0.05
        else:
            comfort = 1.0 if duty_cycle < 0.1 else 0.0
        return (energy, comfort)

    def optimize(self, current_temp, current_humidity, occupancy, person_count=1):
        self.current_temp = current_temp
        self.current_humidity = current_humidity
        self.occupancy = occupancy
        self.person_count = person_count
        pop = self.toolbox.population(n=self.POP_SIZE)
        algorithms.eaMuPlusLambda(
            pop, self.toolbox,
            mu=self.POP_SIZE, lambda_=self.POP_SIZE,
            cxpb=self.CXPB, mutpb=self.MUTPB,
            ngen=self.NGEN, verbose=False
        )
        pareto = tools.sortNondominated(pop, len(pop), first_front_only=True)[0]
        best = max(pareto, key=lambda ind: ind.fitness.values[1] - ind.fitness.values[0])
        result = {
            "ac_temperature": int(np.clip(best[0], 16, 30)),
            "fan_speed": int(np.clip(best[1], 1, 3)),
            "duty_cycle": round(float(np.clip(best[2], 0, 1)), 2),
            "should_turn_on": bool(self.occupancy and best[2] > 0.1),
            "energy_score": round(best.fitness.values[0], 3),
            "comfort_score": round(best.fitness.values[1], 3)
        }
        logger.info(f"GA Result: {result}")
        return result

    def publish_control(self, result, mqtt_client):
        if result["should_turn_on"]:
            payload = json.dumps({
                "action": "set_temp",
                "temperature": result["ac_temperature"],
                "fan_speed": result["fan_speed"]
            })
        else:
            payload = json.dumps({"action": "turn_off"})
        mqtt_client.publish("smartroom/ac/control", payload)