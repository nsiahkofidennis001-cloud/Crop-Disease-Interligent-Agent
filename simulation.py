"""
Crop Disease Intelligent Agent — Simulation Runner
====================================================

Demonstrates the full Prometheus agent loop across multiple time steps
in two modes:

  --synthetic   Use random predictions (no trained model required)
  --real        Use a trained model + real dataset images

Usage
-----
    # Quick demo (no model needed):
    python simulation.py --synthetic --steps 5

    # Full demo with a trained model:
    python simulation.py --real --steps 3 --model models/crop_disease_model.pth

The simulation displays a step-by-step trace of the agent's BDI cycle:
    Percept → Perceive (belief update) → Decide (plan selection) → Act (action)
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

# ── Colour helpers (cross-platform) ────────────────────────────────────── #
try:
    import colorama
    colorama.init(autoreset=True)
    C_RESET  = colorama.Style.RESET_ALL
    C_BOLD   = colorama.Style.BRIGHT
    C_GREEN  = colorama.Fore.GREEN
    C_YELLOW = colorama.Fore.YELLOW
    C_RED    = colorama.Fore.RED
    C_CYAN   = colorama.Fore.CYAN
    C_MAGENTA= colorama.Fore.MAGENTA
    C_BLUE   = colorama.Fore.BLUE
    HAS_COLOR = True
except ImportError:
    C_RESET = C_BOLD = C_GREEN = C_YELLOW = C_RED = ""
    C_CYAN = C_MAGENTA = C_BLUE = ""
    HAS_COLOR = False


# ── Synthetic agent (no model required) ─────────────────────────────────── #

class SyntheticDecisionEngine:
    """Replaces the CNN pipeline with random predictions for demo purposes."""

    DISEASES = [
        ("Tomato___Late_blight",                        0.91),
        ("Tomato___Early_blight",                       0.85),
        ("Tomato___Bacterial_spot",                     0.76),
        ("Corn_(maize)___Common_rust_",                 0.88),
        ("Corn_(maize)___Northern_Leaf_Blight",         0.72),
        ("Potato___Late_blight",                        0.93),
        ("Apple___Apple_scab",                          0.80),
        ("Grape___Black_rot",                           0.68),
        ("Tomato___healthy",                            0.97),
        ("Corn_(maize)___healthy",                      0.96),
        ("Potato___healthy",                            0.94),
        # low confidence — triggers escalation
        ("Tomato___Spider_mites_Two_spotted_spider_mite", 0.45),
        # extremely low — triggers unknown
        ("Unknown_pathogen",                            0.18),
    ]

    @staticmethod
    def random_diagnosis(plot_id: str | None = None) -> dict:
        disease, conf = random.choice(SyntheticDecisionEngine.DISEASES)
        # Add ±10 % noise
        conf = min(1.0, max(0.05, conf + random.uniform(-0.07, 0.07)))
        top3 = random.sample(SyntheticDecisionEngine.DISEASES, min(3, len(SyntheticDecisionEngine.DISEASES)))
        return {
            "disease":    disease.replace("___", " — ").replace("_", " "),
            "confidence": round(conf, 4),
            "treatment":  _TREATMENT_STUB.get(disease, "Consult a local agricultural extension officer."),
            "top_predictions": [
                {"class": d, "confidence": round(random.uniform(0.05, c), 4)}
                for d, c in top3
            ],
        }


_TREATMENT_STUB = {
    "Tomato___Late_blight": "Apply systemic fungicide immediately. Remove all infected plant material.",
    "Tomato___Early_blight": "Apply fungicide (chlorothalonil or mancozeb). Mulch around plants.",
    "Tomato___Bacterial_spot": "Apply copper-based bactericide. Avoid overhead watering.",
    "Corn_(maize)___Common_rust_": "Apply fungicide if infection is early. Use rust-resistant hybrids.",
    "Corn_(maize)___Northern_Leaf_Blight": "Apply foliar fungicide. Use resistant hybrids.",
    "Potato___Late_blight": "Apply systemic fungicide immediately. Destroy all infected plant material.",
    "Apple___Apple_scab": "Apply fungicide (captan) during spring. Rake and destroy fallen leaves.",
    "Grape___Black_rot": "Apply fungicide early in the season. Remove mummified berries.",
    "Tomato___healthy": "No disease detected. Continue regular care.",
    "Corn_(maize)___healthy": "No disease detected. Continue standard management practices.",
    "Potato___healthy": "No disease detected. Maintain good drainage.",
    "Tomato___Spider_mites_Two_spotted_spider_mite": "Spray with insecticidal soap or neem oil.",
}


# ── Synthetic BDI agent ──────────────────────────────────────────────────── #

class SyntheticCropDiseaseAgent:
    """A BDI agent that uses synthetic (random) predictions, no model needed."""

    CONFIDENCE_THRESHOLD = 0.70
    UNKNOWN_THRESHOLD    = 0.25

    def __init__(self):
        self.beliefs = {
            "disease_history": [],
            "plot_health_map": {},
            "weather": "sunny",
            "confidence_threshold": self.CONFIDENCE_THRESHOLD,
        }
        self.goals = ["diagnose_disease", "recommend_treatment", "monitor_crops"]
        self.current_plan: str | None = None
        self.cycle_count = 0

    # ── BDI loop ──────────────────────────────────── #

    def run_cycle(self, percept: dict) -> dict:
        self.cycle_count += 1
        self.perceive(percept)
        plan = self.decide(percept.get("percept_type", ""))
        return self.act(plan, percept)

    def perceive(self, percept: dict):
        ptype = percept.get("percept_type", "")
        data  = percept.get("data", {})

        if ptype == "image_received":
            plot_id  = data.get("plot_id")
            diag     = SyntheticDecisionEngine.random_diagnosis(plot_id)
            self._last_diag  = diag
            self._last_plot  = plot_id
            self.beliefs["disease_history"].append({
                "plot_id": plot_id,
                "disease": diag["disease"],
                "confidence": diag["confidence"],
            })
            self.beliefs["plot_health_map"][plot_id] = (
                "healthy" if "healthy" in diag["disease"].lower() else "diseased"
            )

        elif ptype == "weather_update":
            self.beliefs["weather"] = data.get("condition", "unknown")

        elif ptype == "disease_spread":
            print(f"  {C_YELLOW}⚠  Disease spread detected: {data}{C_RESET}")

        elif ptype == "monitoring_requested":
            if "monitor_crops" not in self.goals:
                self.goals.insert(0, "monitor_crops")

    def decide(self, percept_type: str) -> str:
        if percept_type == "monitoring_requested":
            plan = "batch_monitor"
        elif percept_type == "weather_update":
            plan = "weather_update"
        elif not hasattr(self, "_last_diag"):
            plan = "weather_update"
        elif self._last_diag["confidence"] < self.UNKNOWN_THRESHOLD:
            plan = "handle_unknown"
        elif self._last_diag["confidence"] < self.CONFIDENCE_THRESHOLD:
            plan = "handle_low_confidence"
        else:
            plan = "diagnose_single"
        self.current_plan = plan
        return plan

    def act(self, plan: str, percept: dict) -> dict:
        plan_map = {
            "diagnose_single":       self._act_diagnose,
            "handle_low_confidence": self._act_low_confidence,
            "handle_unknown":        self._act_unknown,
            "batch_monitor":         self._act_monitor,
            "weather_update":        self._act_weather,
        }
        fn = plan_map.get(plan, self._act_weather)
        return fn()

    def _act_diagnose(self) -> dict:
        d = self._last_diag
        conf = d["confidence"]
        disease = d["disease"]
        is_healthy = "healthy" in disease.lower()
        severity = "none" if is_healthy else ("critical" if conf > 0.88 else "high" if conf > 0.75 else "medium")
        return {
            "action":   "recommend_treatment",
            "disease":  disease,
            "conf":     conf,
            "severity": severity,
            "message":  d["treatment"],
            "plot_id":  self._last_plot,
        }

    def _act_low_confidence(self) -> dict:
        d = self._last_diag
        return {
            "action":   "low_confidence_alert",
            "disease":  d["disease"],
            "conf":     d["confidence"],
            "severity": "low",
            "message":  "Confidence below threshold. Recommend expert inspection.",
            "plot_id":  self._last_plot,
        }

    def _act_unknown(self) -> dict:
        d = self._last_diag
        return {
            "action":   "escalate_to_expert",
            "disease":  d["disease"],
            "conf":     d["confidence"],
            "severity": "unknown",
            "message":  "Unknown disease pattern. Submit sample to a plant pathology lab.",
            "plot_id":  self._last_plot,
        }

    def _act_monitor(self) -> dict:
        pm = self.beliefs["plot_health_map"]
        diseased = [k for k, v in pm.items() if v == "diseased"]
        healthy  = [k for k, v in pm.items() if v == "healthy"]
        return {
            "action":  "field_health_report",
            "disease": None,
            "message": (
                f"Field summary: {len(healthy)} healthy, {len(diseased)} diseased. "
                + (f"Critical plots: {', '.join(diseased[:3])}" if diseased else "All plots healthy.")
            ),
        }

    def _act_weather(self) -> dict:
        return {
            "action":  "belief_update",
            "message": f"Weather updated: {self.beliefs['weather']}",
        }


# ── Display helpers ──────────────────────────────────────────────────────── #

def _sep(char="-", width=65):
    print(C_BLUE + char * width + C_RESET)


def _severity_color(severity: str) -> str:
    return {
        "critical": C_RED,
        "high":     C_YELLOW,
        "medium":   C_MAGENTA,
        "low":      C_CYAN,
        "none":     C_GREEN,
        "unknown":  C_YELLOW,
        "summary":  C_CYAN,
    }.get(severity, "")


def _print_action(action: dict):
    action_type = action.get("action", "unknown")
    severity    = action.get("severity", "")
    disease     = action.get("disease")
    conf        = action.get("conf") or action.get("confidence")
    plot_id     = action.get("plot_id", "")
    message     = action.get("message", "")

    sc = _severity_color(severity)

    print(f"  {C_BOLD}>> ACT{C_RESET} [{action_type.upper()}]")
    if plot_id:
        print(f"    Plot     : {plot_id}")
    if disease:
        print(f"    Disease  : {disease}")
    if conf is not None:
        print(f"    Conf.    : {conf:.1%}")
    if severity:
        print(f"    Severity : {sc}{severity.upper()}{C_RESET}")
    print(f"    Response : {message}")


def _print_percept(percept: dict):
    ptype = percept.get("percept_type", "")
    data  = percept.get("data", {})
    plot  = data.get("plot_id", "")
    crop  = data.get("crop_type", "")
    detail = f"({plot}, {crop})" if plot and crop else f"({list(data.items())[0][1]})" if data else ""
    print(f"  {C_CYAN}<< PERCEPT{C_RESET} [{ptype}] {detail}")


# ── Main simulation ──────────────────────────────────────────────────────── #

def run_simulation(steps: int = 3, num_plots: int = 6, seed: int = 42, use_real: bool = False,
                   model_path: str = "models/crop_disease_model.pth",
                   class_names_path: str = "models/class_names.json",
                   dataset_dir: str = "dataset"):

    print()
    _sep("=")
    print(f"{C_BOLD}{C_GREEN}  [CROP DISEASE INTELLIGENT AGENT] --- SIMULATION{C_RESET}")
    print(f"     Mode     : {'Real CNN model' if use_real else 'Synthetic (random predictions)'}")
    print(f"     Steps    : {steps}")
    print(f"     Plots    : {num_plots}")
    print(f"     Seed     : {seed}")
    _sep("=")

    # ── Initialise environment ──────────────────────────────── #
    from agent.environment import CropField, PerceptType

    env = CropField(num_plots=num_plots, seed=seed,
                    dataset_dir=dataset_dir if use_real else None)

    # ── Initialise agent ────────────────────────────────────── #
    if use_real:
        if not os.path.isfile(model_path):
            print(f"{C_RED}  Model not found: {model_path}{C_RESET}")
            print("  Run: python train.py --epochs 20  (or use --synthetic)")
            sys.exit(1)
        from agent.agent import CropDiseaseAgent

        class _RealAdapter:
            """Thin wrapper so real agent matches the same dict-based interface."""
            def __init__(self):
                self.inner = CropDiseaseAgent(model_path, class_names_path)
                self.cycle_count = 0
                self.current_plan = None
                self.beliefs = self.inner.beliefs

            def run_cycle(self, percept: dict) -> dict:
                self.cycle_count += 1
                self.inner.perceive(percept)
                plan = self.inner.decide(percept.get("percept_type", ""))
                action_obj = self.inner.act(plan)
                self.current_plan = plan.value
                if action_obj.diagnosis:
                    return {
                        "action":   action_obj.action_type,
                        "disease":  action_obj.diagnosis.disease,
                        "conf":     action_obj.diagnosis.confidence,
                        "severity": action_obj.severity,
                        "message":  action_obj.message,
                        "plot_id":  self.inner.beliefs.current_plot_id,
                    }
                return {"action": action_obj.action_type, "message": action_obj.message}

        agent = _RealAdapter()
    else:
        agent = SyntheticCropDiseaseAgent()

    # ── Simulation loop ─────────────────────────────────────── #
    for step in range(1, steps + 1):
        print()
        _sep("=")
        print(f"{C_BOLD}  STEP {step}/{steps}   |  Weather: {env.weather}  |  "
              f"Field: {sum(1 for p in env.plots if p.health_status.value == 'diseased')} diseased plots{C_RESET}")
        _sep("-")

        percepts = env.generate_percepts()

        for percept_obj in percepts:
            percept_dict = {
                "percept_type": percept_obj.percept_type.value,
                "data": percept_obj.data,
            }

            _print_percept(percept_dict)

            action = agent.run_cycle(percept_dict)
            plan   = getattr(agent, "current_plan", "unknown")
            print(f"  {C_MAGENTA}● DECIDE{C_RESET} Plan selected: {plan}")
            _print_action(action)

            # Feed action back to environment (for image percepts)
            if action.get("action") in ("recommend_treatment", "low_confidence_alert", "escalate_to_expert"):
                env_cmd = {
                    "recommend_treatment": "treat_crop",
                    "low_confidence_alert": "request_inspection",
                    "escalate_to_expert": "request_inspection",
                }.get(action["action"], "no_action")
                result = env.apply_action(env_cmd, {"plot_id": action.get("plot_id", "")})
                print(f"    {C_GREEN}+> Env response: {result['message']}{C_RESET}")

            print()

        env.advance_time_step()

    # ── Final field summary ─────────────────────────────────── #
    _sep("=")
    print(f"{C_BOLD}{C_GREEN}  SIMULATION COMPLETE - Final Field Status{C_RESET}")
    _sep("=")
    summary = env.get_field_summary()
    print(f"  Total Plots : {summary['total_plots']}")
    print(f"  Healthy     : {C_GREEN}{summary['healthy']}{C_RESET}")
    print(f"  Diseased    : {C_RED}{summary['diseased']}{C_RESET}")
    print(f"  Weather     : {summary['weather']}")
    print()
    for plot in summary["plots"]:
        status_c = C_GREEN if plot["status"] == "healthy" else C_RED
        print(f"  {plot['id']:8s} | {plot['crop']:6s} | {status_c}{plot['status']:8s}{C_RESET} | {plot['disease']}")
    _sep("═")
    print()


# ── CLI ──────────────────────────────────────────────────────────────────── #

def main():
    parser = argparse.ArgumentParser(
        description="Crop Disease Intelligent Agent — Prometheus Simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--synthetic", action="store_true", default=True,
                        help="Use random predictions (default, no model needed)")
    parser.add_argument("--real", action="store_true", default=False,
                        help="Use a trained CNN model + real dataset images")
    parser.add_argument("--steps",    type=int, default=3, help="Number of time steps (default: 3)")
    parser.add_argument("--plots",    type=int, default=6, help="Number of crop plots (default: 6)")
    parser.add_argument("--seed",     type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--model",    type=str, default="models/crop_disease_model.pth")
    parser.add_argument("--classes",  type=str, default="models/class_names.json")
    parser.add_argument("--dataset",  type=str, default="dataset")
    args = parser.parse_args()

    use_real = args.real

    run_simulation(
        steps=args.steps,
        num_plots=args.plots,
        seed=args.seed,
        use_real=use_real,
        model_path=args.model,
        class_names_path=args.classes,
        dataset_dir=args.dataset,
    )


if __name__ == "__main__":
    main()
