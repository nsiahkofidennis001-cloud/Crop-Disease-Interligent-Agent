"""
Perception layer — image preprocessing and CNN feature extraction.

This module handles the 'sensing' part of the intelligent agent:
converting raw leaf images into feature representations via a
pretrained ResNet-18 backbone.
"""

import torch
from torchvision import transforms, models
from PIL import Image


# ---------- Image Preprocessing ---------- #

class ImagePreprocessor:
    """Resize, normalise and convert a PIL image (or file path) to a tensor
    suitable for the ResNet-18 backbone."""

    def __init__(self, image_size: int = 224):
        self.transform = transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],   # ImageNet means
                std=[0.229, 0.224, 0.225],     # ImageNet stds
            ),
        ])

    def __call__(self, image) -> torch.Tensor:
        """Accept a PIL Image, file path (str), or numpy array and return
        a batched tensor of shape (1, 3, H, W)."""
        if isinstance(image, str):
            image = Image.open(image).convert("RGB")
        elif not isinstance(image, Image.Image):
            image = Image.fromarray(image).convert("RGB")
        else:
            image = image.convert("RGB")
        return self.transform(image).unsqueeze(0)  # add batch dim


# ---------- Feature Extraction ---------- #

class FeatureExtractor:
    """Load a fine-tuned ResNet-18 checkpoint and run the forward pass to
    produce raw logits for each disease class."""

    def __init__(self, model_path: str, num_classes: int, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Build the same architecture used during training
        self.model = models.resnet18(weights=None)
        self.model.fc = torch.nn.Linear(self.model.fc.in_features, num_classes)

        # Load trained weights
        state_dict = torch.load(model_path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

    @torch.no_grad()
    def extract(self, image_tensor: torch.Tensor) -> torch.Tensor:
        """Return raw logits of shape (1, num_classes)."""
        image_tensor = image_tensor.to(self.device)
        logits = self.model(image_tensor)
        return logits
