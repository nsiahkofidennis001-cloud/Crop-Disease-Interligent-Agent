"""
Simulated agricultural environment for the Crop Disease Agent.

Provides a `CropField` with multiple plots that generate percepts
(new images, disease spread events, weather changes) so the agent
can demonstrate reactive and proactive behaviour in a controlled
setting.
"""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ------------------------------------------------------------------ #
#  Data types                                                         #
# ------------------------------------------------------------------ #

class CropType(Enum):
    TOMATO = "Tomato"
    POTATO = "Potato"
    CORN = "Corn"
    APPLE = "Apple"
    GRAPE = "Grape"


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DISEASED = "diseased"
    UNKNOWN = "unknown"


class PerceptType(Enum):
    IMAGE_RECEIVED = "image_received"
    WEATHER_UPDATE = "weather_update"
    DISEASE_SPREAD = "disease_spread"
    MONITORING_REQUESTED = "monitoring_requested"


# Possible diseases per crop type (matching the TREATMENT_DB keys)
CROP_DISEASES: dict[str, list[str]] = {
    "Tomato": [
        "Tomato___Bacterial_spot",
        "Tomato___Early_blight",
        "Tomato___Late_blight",
        "Tomato___Leaf_Mold",
        "Tomato___Septoria_leaf_spot",
        "Tomato___Target_Spot",
        "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
        "Tomato___Tomato_mosaic_virus",
        "Tomato___healthy",
    ],
    "Potato": [
        "Potato___Early_blight",
        "Potato___Late_blight",
        "Potato___healthy",
    ],
    "Corn": [
        "Corn_(maize)___Cercospora_leaf_spot_Gray_leaf_spot",
        "Corn_(maize)___Common_rust_",
        "Corn_(maize)___Northern_Leaf_Blight",
        "Corn_(maize)___healthy",
    ],
    "Apple": [
        "Apple___Apple_scab",
        "Apple___Black_rot",
        "Apple___Cedar_apple_rust",
        "Apple___healthy",
    ],
    "Grape": [
        "Grape___Black_rot",
        "Grape___Esca_(Black_Measles)",
        "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
        "Grape___healthy",
    ],
}


@dataclass
class CropPlot:
    """A single crop plot in the simulated field."""
    plot_id: str
    crop_type: CropType
    health_status: HealthStatus = HealthStatus.HEALTHY
    disease: Optional[str] = None
    image_path: Optional[str] = None    # path to a sample image (if available)
    days_infected: int = 0

    @property
    def disease_display(self) -> str:
        if self.disease:
            return self.disease.replace("___", " — ").replace("_", " ")
        return "Healthy"


@dataclass
class Percept:
    """An event or data item perceived from the environment."""
    percept_type: PerceptType
    data: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        return f"[{self.percept_type.value}] {self.data}"


# ------------------------------------------------------------------ #
#  CropField — the simulated environment                              #
# ------------------------------------------------------------------ #

class CropField:
    """Simulated agricultural environment with multiple crop plots.

    Usage
    -----
    >>> env = CropField(num_plots=6, seed=42)
    >>> percepts = env.generate_percepts()
    >>> env.apply_action("treat_crop", {"plot_id": "plot_1"})
    >>> env.advance_time_step()
    """

    WEATHER_CONDITIONS = ["sunny", "rainy", "humid", "dry", "overcast"]

    def __init__(
        self,
        num_plots: int = 6,
        disease_probability: float = 0.3,
        seed: int | None = None,
        dataset_dir: str | None = None,
    ):
        if seed is not None:
            random.seed(seed)

        self.time_step = 0
        self.weather = random.choice(self.WEATHER_CONDITIONS)
        self.dataset_dir = dataset_dir
        self.action_log: list[dict] = []

        # Create plots with random crops and initial disease states
        self.plots: list[CropPlot] = []
        crop_types = list(CropType)
        for i in range(num_plots):
            crop = random.choice(crop_types)
            is_diseased = random.random() < disease_probability

            if is_diseased:
                diseases = CROP_DISEASES[crop.value]
                # Exclude healthy from random disease selection
                disease_options = [d for d in diseases if "healthy" not in d]
                disease = random.choice(disease_options) if disease_options else None
                status = HealthStatus.DISEASED if disease else HealthStatus.HEALTHY
            else:
                disease = None
                status = HealthStatus.HEALTHY

            plot = CropPlot(
                plot_id=f"plot_{i + 1}",
                crop_type=crop,
                health_status=status,
                disease=disease,
                image_path=self._find_sample_image(disease or f"{crop.value}___healthy"),
            )
            self.plots.append(plot)

    def _find_sample_image(self, class_name: str) -> str | None:
        """Try to find a sample image from the dataset directory."""
        if not self.dataset_dir:
            return None
        # Look in both train and test directories
        for split in ["train", "test"]:
            class_dir = os.path.join(self.dataset_dir, split, class_name)
            if os.path.isdir(class_dir):
                images = [f for f in os.listdir(class_dir)
                          if f.lower().endswith((".jpg", ".jpeg", ".png"))]
                if images:
                    return os.path.join(class_dir, random.choice(images))
        return None

    # ------------------------------------------------------------------ #
    #  Percept generation                                                 #
    # ------------------------------------------------------------------ #

    def generate_percepts(self) -> list[Percept]:
        """Generate percepts for the current time step.

        Returns a list of Percept objects that the agent should process.
        """
        percepts: list[Percept] = []

        # 1. Generate image percepts from each plot
        for plot in self.plots:
            percepts.append(Percept(
                percept_type=PerceptType.IMAGE_RECEIVED,
                data={
                    "plot_id": plot.plot_id,
                    "crop_type": plot.crop_type.value,
                    "image_path": plot.image_path,
                    "actual_disease": plot.disease,
                    "actual_status": plot.health_status.value,
                },
            ))

        # 2. Weather update
        percepts.append(Percept(
            percept_type=PerceptType.WEATHER_UPDATE,
            data={"condition": self.weather, "time_step": self.time_step},
        ))

        # 3. Disease spread events (if any plot has been infected for > 2 steps)
        for plot in self.plots:
            if plot.health_status == HealthStatus.DISEASED and plot.days_infected > 2:
                percepts.append(Percept(
                    percept_type=PerceptType.DISEASE_SPREAD,
                    data={
                        "source_plot": plot.plot_id,
                        "disease": plot.disease,
                        "days_infected": plot.days_infected,
                    },
                ))

        return percepts

    # ------------------------------------------------------------------ #
    #  Action handling                                                    #
    # ------------------------------------------------------------------ #

    def apply_action(self, action_type: str, params: dict) -> dict:
        """Apply an agent action to the environment.

        Parameters
        ----------
        action_type : one of 'treat_crop', 'alert_farmer', 'request_inspection', 'no_action'
        params      : action-specific parameters (e.g. plot_id)

        Returns
        -------
        dict with 'success' boolean and 'message' string
        """
        result = {"action": action_type, "params": params, "time_step": self.time_step}

        if action_type == "treat_crop":
            plot_id = params.get("plot_id")
            plot = self._get_plot(plot_id)
            if plot and plot.health_status == HealthStatus.DISEASED:
                # Treatment has a chance of curing the crop
                cure_chance = 0.8 if plot.days_infected <= 3 else 0.5
                if random.random() < cure_chance:
                    plot.health_status = HealthStatus.HEALTHY
                    plot.disease = None
                    plot.days_infected = 0
                    result["success"] = True
                    result["message"] = f"{plot_id} treated successfully — crop recovering."
                else:
                    result["success"] = False
                    result["message"] = f"{plot_id} treatment applied but disease persists. Re-treat recommended."
            else:
                result["success"] = True
                result["message"] = f"{plot_id} is already healthy. No treatment needed."

        elif action_type == "alert_farmer":
            result["success"] = True
            result["message"] = f"Alert sent to farmer regarding {params.get('plot_id', 'field')}."

        elif action_type == "request_inspection":
            result["success"] = True
            result["message"] = f"Expert inspection requested for {params.get('plot_id', 'unknown plot')}."

        elif action_type == "no_action":
            result["success"] = True
            result["message"] = "No action required."

        else:
            result["success"] = False
            result["message"] = f"Unknown action type: {action_type}"

        self.action_log.append(result)
        return result

    # ------------------------------------------------------------------ #
    #  Time progression                                                   #
    # ------------------------------------------------------------------ #

    def advance_time_step(self):
        """Move the simulation forward by one time step.

        - Weather may change
        - Diseased plots get worse
        - Disease may spread to adjacent healthy plots
        """
        self.time_step += 1

        # Weather change (30% chance)
        if random.random() < 0.3:
            self.weather = random.choice(self.WEATHER_CONDITIONS)

        # Disease progression
        for plot in self.plots:
            if plot.health_status == HealthStatus.DISEASED:
                plot.days_infected += 1

        # Disease spread (10% chance per diseased plot to infect a random healthy one)
        diseased_plots = [p for p in self.plots if p.health_status == HealthStatus.DISEASED]
        healthy_plots = [p for p in self.plots if p.health_status == HealthStatus.HEALTHY]

        for d_plot in diseased_plots:
            if healthy_plots and random.random() < 0.10:
                target = random.choice(healthy_plots)
                # Spread same disease if same crop type, otherwise random
                if target.crop_type == d_plot.crop_type and d_plot.disease:
                    target.disease = d_plot.disease
                else:
                    diseases = CROP_DISEASES.get(target.crop_type.value, [])
                    disease_options = [d for d in diseases if "healthy" not in d]
                    target.disease = random.choice(disease_options) if disease_options else None
                if target.disease:
                    target.health_status = HealthStatus.DISEASED
                    healthy_plots.remove(target)

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _get_plot(self, plot_id: str) -> CropPlot | None:
        """Look up a plot by ID."""
        for plot in self.plots:
            if plot.plot_id == plot_id:
                return plot
        return None

    def get_field_summary(self) -> dict:
        """Return a summary of the current field state."""
        healthy = sum(1 for p in self.plots if p.health_status == HealthStatus.HEALTHY)
        diseased = sum(1 for p in self.plots if p.health_status == HealthStatus.DISEASED)
        return {
            "time_step": self.time_step,
            "total_plots": len(self.plots),
            "healthy": healthy,
            "diseased": diseased,
            "weather": self.weather,
            "plots": [
                {
                    "id": p.plot_id,
                    "crop": p.crop_type.value,
                    "status": p.health_status.value,
                    "disease": p.disease_display,
                    "days_infected": p.days_infected,
                }
                for p in self.plots
            ],
        }

    def __repr__(self) -> str:
        summary = self.get_field_summary()
        return (
            f"CropField(step={summary['time_step']}, "
            f"plots={summary['total_plots']}, "
            f"healthy={summary['healthy']}, "
            f"diseased={summary['diseased']}, "
            f"weather={summary['weather']})"
        )
