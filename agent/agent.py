"""
Crop Disease Agent — BDI (Belief-Desire-Intention) orchestrator.

Implements the core intelligent agent loop:
    perceive() → decide() → act()

The agent maintains:
  - Beliefs  : a structured knowledge base (BeliefBase)
  - Goals    : a prioritised list of AgentGoal values
  - Plans    : methods that map goals+context to concrete actions

Usage
-----
>>> agent = CropDiseaseAgent("models/crop_disease_model.pth",
...                          "models/class_names.json")
>>> result = agent.diagnose("leaf_photo.jpg")        # convenience wrapper
>>> agent.run_cycle(percept)                          # BDI loop
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .perception import ImagePreprocessor, FeatureExtractor
from .decision import DecisionEngine, DiagnosisResult


# ------------------------------------------------------------------ #
#  BDI Primitives                                                     #
# ------------------------------------------------------------------ #

class AgentGoal(Enum):
    """Goals the agent can pursue."""
    DIAGNOSE_DISEASE      = "diagnose_disease"
    RECOMMEND_TREATMENT   = "recommend_treatment"
    MONITOR_CROPS         = "monitor_crops"
    ESCALATE_TO_EXPERT    = "escalate_to_expert"
    HANDLE_UNKNOWN        = "handle_unknown"


class AgentPlan(Enum):
    """Plans the agent can execute."""
    DIAGNOSE_SINGLE       = "diagnose_single"
    HANDLE_LOW_CONFIDENCE = "handle_low_confidence"
    HANDLE_UNKNOWN        = "handle_unknown_disease"
    BATCH_MONITOR         = "batch_monitor"
    WEATHER_UPDATE        = "update_weather_belief"


@dataclass
class DiagnosisRecord:
    """A historical record stored in the belief base."""
    disease: str
    confidence: float
    severity: str
    plot_id: Optional[str]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "disease": self.disease,
            "confidence": round(self.confidence, 4),
            "severity": self.severity,
            "plot_id": self.plot_id,
            "timestamp": self.timestamp,
        }


@dataclass
class BeliefBase:
    """The agent's current world model — updated after every perception cycle."""

    # ── Current perception state ──────────────────────────────────── #
    current_image: Any = None               # raw image being processed
    current_plot_id: Optional[str] = None   # which plot the image came from

    # ── Classification thresholds ─────────────────────────────────── #
    confidence_threshold: float = 0.70      # minimum for a reliable diagnosis
    unknown_threshold: float = 0.25         # below this → unknown disease

    # ── Latest classification result ──────────────────────────────── #
    latest_result: Optional[DiagnosisResult] = None
    is_confident: bool = False

    # ── Historical knowledge ───────────────────────────────────────── #
    disease_history: list[DiagnosisRecord] = field(default_factory=list)
    plot_health_map: dict[str, str] = field(default_factory=dict)   # plot_id → status

    # ── Environment model ─────────────────────────────────────────── #
    weather: str = "unknown"
    num_plots: int = 0
    time_step: int = 0

    def update_from_result(self, result: DiagnosisResult, plot_id: Optional[str] = None):
        """Update beliefs after a diagnosis has been obtained."""
        self.latest_result = result
        self.is_confident = result.confidence >= self.confidence_threshold
        severity = _assess_severity(result.disease, result.confidence)

        record = DiagnosisRecord(
            disease=result.disease,
            confidence=result.confidence,
            severity=severity,
            plot_id=plot_id,
        )
        self.disease_history.append(record)

        if plot_id:
            self.plot_health_map[plot_id] = (
                "healthy" if "healthy" in result.disease.lower() else "diseased"
            )


def _assess_severity(disease: str, confidence: float) -> str:
    """Return a severity classification based on the disease name and confidence."""
    if "healthy" in disease.lower():
        return "none"
    # Critical diseases require immediate action
    critical_terms = ["Late_blight", "Mosaic_Virus", "Yellow_Leaf_Curl"]
    high_terms     = ["Early_blight", "Bacterial_spot", "Black_rot", "Northern_Leaf_Blight"]

    for term in critical_terms:
        if term.lower() in disease.lower().replace(" ", "_"):
            return "critical" if confidence >= 0.70 else "high"
    for term in high_terms:
        if term.lower() in disease.lower().replace(" ", "_"):
            return "high" if confidence >= 0.70 else "medium"
    if confidence >= 0.70:
        return "medium"
    return "low"


# ------------------------------------------------------------------ #
#  AgentAction — structured output from act()                        #
# ------------------------------------------------------------------ #

@dataclass
class AgentAction:
    """A concrete action chosen by the agent after planning."""
    action_type: str                        # e.g. 'recommend_treatment', 'escalate'
    diagnosis: Optional[DiagnosisResult]    # the associated diagnosis (may be None)
    severity: str = "none"
    message: str = ""
    environment_command: Optional[dict] = None  # sent back to the environment

    def summary(self) -> str:
        lines = [f"  Action : {self.action_type.upper()}"]
        if self.diagnosis:
            lines.append(f"  Disease: {self.diagnosis.disease}")
            lines.append(f"  Conf.  : {self.diagnosis.confidence:.1%}")
            lines.append(f"  Severity: {self.severity}")
        lines.append(f"  Msg    : {self.message}")
        return "\n".join(lines)


# ------------------------------------------------------------------ #
#  CropDiseaseAgent — BDI agent                                      #
# ------------------------------------------------------------------ #

class CropDiseaseAgent:
    """Intelligent BDI agent for crop disease diagnosis.

    Core loop
    ---------
    percept → perceive() updates beliefs
            → decide()  selects a plan
            → act()     executes the plan and returns an AgentAction

    Convenience wrapper
    -------------------
    agent.diagnose(image) runs the full pipeline in one call.
    """

    def __init__(
        self,
        model_path: str,
        class_names_path: str,
        device: str | None = None,
        confidence_threshold: float = 0.70,
        unknown_threshold: float = 0.25,
    ):
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Model checkpoint not found: {model_path}")
        if not os.path.isfile(class_names_path):
            raise FileNotFoundError(f"Class names file not found: {class_names_path}")

        with open(class_names_path, "r") as f:
            self.class_names: list[str] = json.load(f)

        self.preprocessor    = ImagePreprocessor()
        self.feature_extractor = FeatureExtractor(
            model_path=model_path,
            num_classes=len(self.class_names),
            device=device,
        )
        self.decision_engine = DecisionEngine(self.class_names)

        # ── BDI structures ──────────────────────────────────────── #
        self.beliefs = BeliefBase(
            confidence_threshold=confidence_threshold,
            unknown_threshold=unknown_threshold,
        )
        self.goals: list[AgentGoal] = [
            AgentGoal.DIAGNOSE_DISEASE,
            AgentGoal.RECOMMEND_TREATMENT,
            AgentGoal.MONITOR_CROPS,
        ]
        self.current_plan: Optional[AgentPlan] = None
        self._cycle_count: int = 0

    # ------------------------------------------------------------------ #
    #  BDI Loop                                                          #
    # ------------------------------------------------------------------ #

    def run_cycle(self, percept: dict) -> AgentAction:
        """Execute one full perceive → decide → act cycle.

        Parameters
        ----------
        percept : dict with keys:
            percept_type  : str  — e.g. 'image_received', 'weather_update'
            data          : dict — percept-specific payload

        Returns
        -------
        AgentAction
        """
        self._cycle_count += 1

        # ── PERCEIVE ────────────────────────────────────────────── #
        self.perceive(percept)

        # ── DECIDE ──────────────────────────────────────────────── #
        plan = self.decide(percept.get("percept_type", ""))

        # ── ACT ─────────────────────────────────────────────────── #
        action = self.act(plan)

        return action

    def perceive(self, percept: dict):
        """Process a percept and update the agent's beliefs.

        Handles:
          - image_received  : preprocess+classify the image
          - weather_update  : update weather belief
          - disease_spread  : log the spread event
          - monitoring_requested : set monitoring goal active
        """
        ptype = percept.get("percept_type", "")
        data  = percept.get("data", {})

        if ptype == "image_received":
            image = data.get("image_path") or data.get("image")
            self.beliefs.current_image   = image
            self.beliefs.current_plot_id = data.get("plot_id")

            if image is not None:
                # Run the CNN pipeline
                tensor = self.preprocessor(image)
                logits = self.feature_extractor.extract(tensor)
                result = self.decision_engine.decide(logits)
                self.beliefs.update_from_result(result, data.get("plot_id"))

        elif ptype == "weather_update":
            self.beliefs.weather    = data.get("condition", "unknown")
            self.beliefs.time_step  = data.get("time_step", self.beliefs.time_step)

        elif ptype == "disease_spread":
            # Log the spread event in history with a synthetic record
            record = DiagnosisRecord(
                disease=f"[SPREAD] {data.get('disease', 'unknown')}",
                confidence=1.0,
                severity="high",
                plot_id=data.get("source_plot"),
            )
            self.beliefs.disease_history.append(record)

        elif ptype == "monitoring_requested":
            # Ensure monitoring goal is prioritised
            if AgentGoal.MONITOR_CROPS not in self.goals:
                self.goals.insert(0, AgentGoal.MONITOR_CROPS)

    def decide(self, percept_type: str) -> AgentPlan:
        """Select the best plan based on beliefs and current percept.

        Decision rules (in priority order):
          1. If percept is monitoring_requested → BatchMonitor
          2. If no image available → WeatherUpdate
          3. If latest result confidence < unknown_threshold → HandleUnknown
          4. If latest result confidence < confidence_threshold → HandleLowConfidence
          5. Otherwise → DiagnoseSingle
        """
        if percept_type == "monitoring_requested":
            self.current_plan = AgentPlan.BATCH_MONITOR

        elif percept_type == "weather_update":
            self.current_plan = AgentPlan.WEATHER_UPDATE

        elif self.beliefs.latest_result is None:
            # No result yet (image path may have been None)
            self.current_plan = AgentPlan.WEATHER_UPDATE

        elif self.beliefs.latest_result.confidence < self.beliefs.unknown_threshold:
            self.current_plan = AgentPlan.HANDLE_UNKNOWN

        elif not self.beliefs.is_confident:
            self.current_plan = AgentPlan.HANDLE_LOW_CONFIDENCE

        else:
            self.current_plan = AgentPlan.DIAGNOSE_SINGLE

        return self.current_plan

    def act(self, plan: AgentPlan) -> AgentAction:
        """Execute the selected plan and return an AgentAction."""
        plan_dispatch = {
            AgentPlan.DIAGNOSE_SINGLE:       self._plan_diagnose_single,
            AgentPlan.HANDLE_LOW_CONFIDENCE:  self._plan_handle_low_confidence,
            AgentPlan.HANDLE_UNKNOWN:         self._plan_handle_unknown,
            AgentPlan.BATCH_MONITOR:          self._plan_batch_monitor,
            AgentPlan.WEATHER_UPDATE:         self._plan_weather_update,
        }
        plan_fn = plan_dispatch.get(plan, self._plan_weather_update)
        return plan_fn()

    # ------------------------------------------------------------------ #
    #  Plans                                                             #
    # ------------------------------------------------------------------ #

    def _plan_diagnose_single(self) -> AgentAction:
        """Plan: diagnose a single image with high confidence."""
        result   = self.beliefs.latest_result
        severity = _assess_severity(result.disease, result.confidence)
        plot_id  = self.beliefs.current_plot_id or "N/A"

        env_command = None
        if severity == "critical":
            env_command = {"action": "alert_farmer",  "params": {"plot_id": plot_id}}
        elif severity in ("high", "medium"):
            env_command = {"action": "treat_crop",    "params": {"plot_id": plot_id}}
        else:
            env_command = {"action": "no_action",     "params": {"plot_id": plot_id}}

        return AgentAction(
            action_type="recommend_treatment",
            diagnosis=result,
            severity=severity,
            message=(
                f"Diagnosis complete for {plot_id}. "
                f"Disease: {result.disease} ({result.confidence:.1%}). "
                f"Severity: {severity.upper()}. "
                f"Treatment: {result.treatment}"
            ),
            environment_command=env_command,
        )

    def _plan_handle_low_confidence(self) -> AgentAction:
        """Plan: confidence is below threshold — alert but don't commit to diagnosis."""
        result  = self.beliefs.latest_result
        plot_id = self.beliefs.current_plot_id or "N/A"

        return AgentAction(
            action_type="low_confidence_alert",
            diagnosis=result,
            severity="low",
            message=(
                f"[{plot_id}] Confidence ({result.confidence:.1%}) is below "
                f"threshold ({self.beliefs.confidence_threshold:.0%}). "
                f"Top guess: {result.disease}. "
                "Recommend requesting a physical inspection or expert review."
            ),
            environment_command={"action": "request_inspection", "params": {"plot_id": plot_id}},
        )

    def _plan_handle_unknown(self) -> AgentAction:
        """Plan: no class exceeds the unknown threshold — genuinely unrecognised disease."""
        result  = self.beliefs.latest_result
        plot_id = self.beliefs.current_plot_id or "N/A"

        return AgentAction(
            action_type="escalate_to_expert",
            diagnosis=result,
            severity="unknown",
            message=(
                f"[{plot_id}] Disease pattern is unknown (max confidence "
                f"{result.confidence:.1%}). "
                "Please collect a leaf sample and submit to a plant pathology laboratory."
            ),
            environment_command={"action": "request_inspection", "params": {"plot_id": plot_id}},
        )

    def _plan_batch_monitor(self) -> AgentAction:
        """Plan: summarise results for batch/monitoring mode."""
        history   = self.beliefs.disease_history
        plot_map  = self.beliefs.plot_health_map
        diseased  = [pid for pid, st in plot_map.items() if st == "diseased"]
        healthy   = [pid for pid, st in plot_map.items() if st == "healthy"]

        critical = [
            r for r in history
            if r.severity == "critical" and r.plot_id
        ]
        msg = (
            f"Field Health Report — "
            f"{len(healthy)} healthy / {len(diseased)} diseased plots. "
        )
        if critical:
            ids = ", ".join({r.plot_id for r in critical})
            msg += f"CRITICAL ALERT: Plots {ids} need immediate treatment."

        return AgentAction(
            action_type="field_health_report",
            diagnosis=None,
            severity="summary",
            message=msg,
        )

    def _plan_weather_update(self) -> AgentAction:
        """Plan: acknowledge weather update in the belief base."""
        return AgentAction(
            action_type="belief_update",
            diagnosis=None,
            severity="none",
            message=f"Weather belief updated: {self.beliefs.weather}.",
        )

    # ------------------------------------------------------------------ #
    #  Convenience API (unchanged from original)                         #
    # ------------------------------------------------------------------ #

    def diagnose(self, image) -> DiagnosisResult:
        """Run the full perception → decision pipeline on a single image.

        Parameters
        ----------
        image : str (file path), PIL.Image, or numpy array

        Returns
        -------
        DiagnosisResult with disease, confidence, treatment, top_predictions
        """
        tensor = self.preprocessor(image)
        logits = self.feature_extractor.extract(tensor)
        result = self.decision_engine.decide(logits)
        self.beliefs.update_from_result(result)
        return result

    # ------------------------------------------------------------------ #
    #  State inspection                                                  #
    # ------------------------------------------------------------------ #

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    def get_belief_summary(self) -> dict:
        """Return a snapshot of the agent's current beliefs."""
        return {
            "cycle": self._cycle_count,
            "active_goals": [g.value for g in self.goals],
            "current_plan": self.current_plan.value if self.current_plan else None,
            "confidence_threshold": self.beliefs.confidence_threshold,
            "is_confident": self.beliefs.is_confident,
            "weather": self.beliefs.weather,
            "history_length": len(self.beliefs.disease_history),
            "plot_health_map": dict(self.beliefs.plot_health_map),
        }
