"""
Crop Disease Intelligent Agent package.

Exports the environment classes without requiring torch (for simulation/demo mode).
CNN-based classes (CropDiseaseAgent, ImagePreprocessor, FeatureExtractor, DecisionEngine)
are available but require PyTorch to be installed.
"""

from .environment import CropField, CropPlot, Percept, PerceptType

__all__ = [
    "CropField",
    "CropPlot",
    "Percept",
    "PerceptType",
]

# Lazy-load torch-dependent modules only when requested
def _load_torch_classes():
    from .agent import CropDiseaseAgent, BeliefBase, AgentGoal, AgentPlan, AgentAction
    from .decision import DecisionEngine, DiagnosisResult
    from .perception import ImagePreprocessor, FeatureExtractor
    return (
        CropDiseaseAgent, BeliefBase, AgentGoal, AgentPlan, AgentAction,
        DecisionEngine, DiagnosisResult, ImagePreprocessor, FeatureExtractor,
    )


def __getattr__(name):
    torch_classes = [
        "CropDiseaseAgent", "BeliefBase", "AgentGoal", "AgentPlan", "AgentAction",
        "DecisionEngine", "DiagnosisResult", "ImagePreprocessor", "FeatureExtractor",
    ]
    if name in torch_classes:
        classes = _load_torch_classes()
        names = [
            "CropDiseaseAgent", "BeliefBase", "AgentGoal", "AgentPlan", "AgentAction",
            "DecisionEngine", "DiagnosisResult", "ImagePreprocessor", "FeatureExtractor",
        ]
        mapping = dict(zip(names, classes))
        return mapping[name]
    raise AttributeError(f"module 'agent' has no attribute {name!r}")
