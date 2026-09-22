import numpy as np
import json
import logging
import pyswarms as ps

logger = logging.getLogger("LampPSOOptimizer")


class LampPSOOptimizer:
    def __init__(self):
        self.TARGET_LUX_WORK = 400
        self.TARGET_LUX_RELAX = 200
        self.TARGET_LUX_MIN = 100
        self.current_lux = 0
        self.occupancy = False
        self.n_particles = 30
        self.dimensions = 1
        self.options = {'c1': 1.5, 'c2': 1.5, 'w': 0.7}
        self.bounds = (np.array([0]), np.array([255]))

    def _objective_function(self, particles):
        costs = np.zeros(particles.shape[0])
        for i, particle in enumerate(particles):
            brightness = particle[0]
            if not self.occupancy:
                costs[i] = brightness * 10
                continue
            estimated_lamp_lux = (brightness / 255.0) * 500
            estimated_total_lux = self.current_lux + estimated_lamp_lux
            lux_error = abs(estimated_total_lux - self.TARGET_LUX_WORK)
            lux_cost = (lux_error / self.TARGET_LUX_WORK) ** 2
            energy_cost = (brightness / 255.0) ** 1.5
            if estimated_total_lux < self.TARGET_LUX_MIN:
                dark_penalty = ((self.TARGET_LUX_MIN - estimated_total_lux) / self.TARGET_LUX_MIN) * 5
            else:
                dark_penalty = 0
            costs[i] = lux_cost * 3.0 + energy_cost * 1.0 + dark_penalty * 2.0
        return costs

    def optimize(self, current_lux, occupancy, target_mode="work"):
        self.current_lux = current_lux
        self.occupancy = occupancy
        if target_mode == "work":
            self.TARGET_LUX_WORK = 400
        elif target_mode == "relax":
            self.TARGET_LUX_WORK = 200
        elif target_mode == "sleep":
            self.TARGET_LUX_WORK = 50
        if not occupancy:
            return {
                "brightness": 0, "estimated_lux": current_lux,
                "should_turn_on": False, "energy_score": 0, "mode": target_mode
            }
        if current_lux >= self.TARGET_LUX_WORK:
            return {
                "brightness": 0, "estimated_lux": current_lux,
                "should_turn_on": False, "energy_score": 0,
                "mode": target_mode, "note": "Ambient light sufficient"
            }
        optimizer = ps.single.GlobalBestPSO(
            n_particles=self.n_particles,
            dimensions=self.dimensions,
            options=self.options,
            bounds=self.bounds
        )
        best_cost, best_pos = optimizer.optimize(
            self._objective_function, iters=50, verbose=False
        )
        brightness = int(np.clip(best_pos[0], 0, 255))
        estimated_lamp_lux = (brightness / 255.0) * 500
        result = {
            "brightness": brightness,
            "estimated_lux": round(current_lux + estimated_lamp_lux, 1),
            "should_turn_on": brightness > 0,
            "energy_score": round(brightness / 255.0, 3),
            "cost": round(float(best_cost), 4),
            "mode": target_mode
        }
        logger.info(f"PSO Result: {result}")
        return result

    def publish_control(self, result, mqtt_client):
        payload = json.dumps({
            "brightness": result["brightness"],
            "action": "on" if result["should_turn_on"] else "off"
        })
        mqtt_client.publish("smartroom/lamp/control", payload)