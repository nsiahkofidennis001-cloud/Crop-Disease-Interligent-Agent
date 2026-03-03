"""
Crop Disease Agent — top-level orchestrator.

Ties together the perception and decision layers into a single
`diagnose(image)` interface that the web app (or any consumer) can call.
"""

from __future__ import annotations

import json
import os

from .perception import ImagePreprocessor, FeatureExtractor
from .decision import DecisionEngine, DiagnosisResult


class CropDiseaseAgent:
    """Intelligent agent for crop disease diagnosis.

    Usage
    -----
    >>> agent = CropDiseaseAgent("models/crop_disease_model.pth",
    ...                          "models/class_names.json")
    >>> result = agent.diagnose("leaf_photo.jpg")
    >>> print(result.disease, result.confidence, result.treatment)
    """

    def __init__(self, model_path: str, class_names_path: str, device: str | None = None):
        """
        Parameters
        ----------
        model_path       : path to the saved `.pth` checkpoint
        class_names_path : path to a JSON list of class names produced by train.py
        device           : 'cuda', 'cpu', or None (auto-detect)
        """
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Model checkpoint not found: {model_path}")
        if not os.path.isfile(class_names_path):
            raise FileNotFoundError(f"Class names file not found: {class_names_path}")

        with open(class_names_path, "r") as f:
            self.class_names: list[str] = json.load(f)

        self.preprocessor = ImagePreprocessor()
        self.feature_extractor = FeatureExtractor(
            model_path=model_path,
            num_classes=len(self.class_names),
            device=device,
        )
        self.decision_engine = DecisionEngine(self.class_names)

    # ------------------------------------------------------------------ #
    #  Public API                                                         #
    # ------------------------------------------------------------------ #

    def diagnose(self, image) -> DiagnosisResult:
        """Run the full perception → decision pipeline.

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
        return result
