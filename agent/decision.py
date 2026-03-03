"""
Decision layer — map CNN logits to a disease diagnosis and treatment recommendation.

This module acts as the 'brain' of the intelligent agent, interpreting
the raw model output and selecting an actionable recommendation.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from dataclasses import dataclass


# ---------- Diagnosis Result ---------- #

@dataclass
class DiagnosisResult:
    """Structured output returned to the user / downstream system."""
    disease: str
    confidence: float
    treatment: str
    top_predictions: list[dict]  # [{class, confidence}, ...]


# ---------- Treatment Database ---------- #

# Maps class folder names → human-readable treatment recommendations.
# Extend this dictionary as you add new classes to your dataset.
TREATMENT_DB: dict[str, str] = {
    # ── Tomato ──────────────────────────────────────────────
    "Tomato___Bacterial_spot": (
        "Apply copper-based bactericide. Remove and destroy infected leaves. "
        "Avoid overhead watering. Rotate crops every 2-3 years."
    ),
    "Tomato___Early_blight": (
        "Apply fungicide (chlorothalonil or mancozeb). Mulch around plants. "
        "Water at the base. Remove lower infected leaves."
    ),
    "Tomato___Late_blight": (
        "Apply fungicide immediately (metalaxyl-based). Remove all infected "
        "plant material. Ensure good air circulation."
    ),
    "Tomato___Leaf_Mold": (
        "Improve air circulation and reduce humidity. Apply fungicide if "
        "severe. Avoid wetting the leaves."
    ),
    "Tomato___Septoria_leaf_spot": (
        "Remove infected leaves. Apply fungicide (chlorothalonil). "
        "Mulch to prevent soil splash."
    ),
    "Tomato___Spider_mites_Two_spotted_spider_mite": (
        "Spray with insecticidal soap or neem oil. Increase humidity around "
        "the plant. Introduce predatory mites."
    ),
    "Tomato___Target_Spot": (
        "Apply fungicide. Remove infected debris. Maintain proper plant spacing."
    ),
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": (
        "Control whitefly vectors with insecticides or sticky traps. "
        "Remove and destroy infected plants. Use resistant varieties."
    ),
    "Tomato___Tomato_mosaic_virus": (
        "Remove and destroy infected plants. Disinfect tools. "
        "Wash hands before handling plants. Use resistant cultivars."
    ),
    "Tomato___healthy": (
        "No disease detected. Continue regular care — adequate watering, "
        "balanced fertilisation, and crop rotation."
    ),

    # ── Potato ──────────────────────────────────────────────
    "Potato___Early_blight": (
        "Apply fungicide (mancozeb or chlorothalonil). Remove infected foliage. "
        "Practise crop rotation."
    ),
    "Potato___Late_blight": (
        "Apply systemic fungicide immediately. Destroy all infected plant "
        "material. Avoid overhead irrigation."
    ),
    "Potato___healthy": (
        "No disease detected. Maintain good drainage and balanced fertilisation."
    ),

    # ── Corn ────────────────────────────────────────────────
    "Corn_(maize)___Cercospora_leaf_spot_Gray_leaf_spot": (
        "Apply foliar fungicide (strobilurin). Practise crop rotation and "
        "tillage to reduce inoculum."
    ),
    "Corn_(maize)___Common_rust_": (
        "Apply fungicide if infection is early. Use rust-resistant hybrids. "
        "Monitor fields regularly."
    ),
    "Corn_(maize)___Northern_Leaf_Blight": (
        "Apply foliar fungicide. Use resistant hybrids. Rotate crops and "
        "manage crop residue."
    ),
    "Corn_(maize)___healthy": (
        "No disease detected. Continue standard management practices."
    ),

    # ── Apple ───────────────────────────────────────────────
    "Apple___Apple_scab": (
        "Apply fungicide (captan or myclobutanil) during spring. Rake and "
        "destroy fallen leaves. Prune for air circulation."
    ),
    "Apple___Black_rot": (
        "Prune dead / infected branches. Apply fungicide. Remove mummified "
        "fruit from the canopy."
    ),
    "Apple___Cedar_apple_rust": (
        "Apply fungicide in spring. Remove nearby cedar/juniper hosts if "
        "possible. Use resistant cultivars."
    ),
    "Apple___healthy": (
        "No disease detected. Maintain regular pruning and pest management."
    ),

    # ── Grape ───────────────────────────────────────────────
    "Grape___Black_rot": (
        "Apply fungicide early in the season. Remove mummified berries. "
        "Ensure good air circulation."
    ),
    "Grape___Esca_(Black_Measles)": (
        "Prune and destroy infected wood. No effective chemical treatment — "
        "focus on prevention and sanitation."
    ),
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": (
        "Apply fungicide. Remove infected leaves. Improve canopy management."
    ),
    "Grape___healthy": (
        "No disease detected. Continue regular vineyard management."
    ),
}

# Fallback for classes not in the database
_DEFAULT_TREATMENT = (
    "Consult a local agricultural extension officer for a precise diagnosis "
    "and treatment plan tailored to your region."
)


# ---------- Decision Engine ---------- #

class DecisionEngine:
    """Convert raw model logits into an actionable diagnosis with
    confidence score and treatment recommendation."""

    def __init__(self, class_names: list[str]):
        self.class_names = class_names

    def decide(self, logits: torch.Tensor, top_k: int = 3) -> DiagnosisResult:
        """
        Parameters
        ----------
        logits : Tensor of shape (1, num_classes)
        top_k  : number of top predictions to include

        Returns
        -------
        DiagnosisResult
        """
        probabilities = F.softmax(logits, dim=1).squeeze(0)  # (num_classes,)
        top_probs, top_indices = torch.topk(probabilities, min(top_k, len(self.class_names)))

        top_class = self.class_names[top_indices[0].item()]
        top_conf = top_probs[0].item()

        top_predictions = [
            {"class": self.class_names[idx.item()], "confidence": round(prob.item(), 4)}
            for prob, idx in zip(top_probs, top_indices)
        ]

        treatment = TREATMENT_DB.get(top_class, _DEFAULT_TREATMENT)

        return DiagnosisResult(
            disease=top_class.replace("_", " ").replace("  ", " — "),
            confidence=round(top_conf, 4),
            treatment=treatment,
            top_predictions=top_predictions,
        )
