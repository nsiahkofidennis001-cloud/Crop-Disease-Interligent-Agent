"""
Evaluation script — compute metrics on the test set using a saved checkpoint.

Usage
-----
    python evaluate.py

Outputs
-------
- Classification report (printed to console)
- Confusion matrix image saved to models/confusion_matrix.png
"""

import argparse
import json
import os

import numpy as np
import torch
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt


def load_model(model_path: str, num_classes: int, device: str):
    """Recreate the ResNet-18 architecture and load trained weights."""
    model = models.resnet18(weights=None)
    model.fc = torch.nn.Sequential(
        torch.nn.Dropout(0.3),
        torch.nn.Linear(model.fc.in_features, num_classes),
    )
    state_dict = torch.load(model_path, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model


def evaluate(model, dataloader, device):
    """Run inference on the full test set and collect predictions."""
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())

    return np.array(all_labels), np.array(all_preds)


def plot_confusion_matrix(cm, class_names, save_path):
    """Save a colour-coded confusion matrix as a PNG."""
    fig, ax = plt.subplots(figsize=(max(10, len(class_names) * 0.6),
                                    max(8, len(class_names) * 0.5)))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)

    ax.set(
        xticks=np.arange(len(class_names)),
        yticks=np.arange(len(class_names)),
        xticklabels=class_names,
        yticklabels=class_names,
        ylabel="True label",
        xlabel="Predicted label",
        title="Confusion Matrix",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Annotate cells
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], "d"),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black",
                    fontsize=7)

    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"Confusion matrix saved to {save_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate crop disease model")
    parser.add_argument("--data_dir", type=str, default="dataset",
                        help="Root dataset directory")
    parser.add_argument("--model_path", type=str, default="models/crop_disease_model.pth")
    parser.add_argument("--class_names_path", type=str, default="models/class_names.json")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--image_size", type=int, default=224)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # ── Class names ─────────────────────────────────────────
    with open(args.class_names_path, "r") as f:
        class_names = json.load(f)
    num_classes = len(class_names)
    print(f"Evaluating {num_classes} classes")

    # ── Data ────────────────────────────────────────────────
    test_transform = transforms.Compose([
        transforms.Resize((args.image_size, args.image_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ])

    test_dataset = datasets.ImageFolder(
        os.path.join(args.data_dir, "test"), transform=test_transform
    )
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size,
                             shuffle=False, num_workers=2, pin_memory=True)

    # ── Model ───────────────────────────────────────────────
    model = load_model(args.model_path, num_classes, device)

    # ── Evaluate ────────────────────────────────────────────
    labels, preds = evaluate(model, test_loader, device)

    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)
    print(classification_report(labels, preds, target_names=class_names, digits=4))

    # ── Confusion Matrix ────────────────────────────────────
    cm = confusion_matrix(labels, preds)
    plot_confusion_matrix(cm, class_names, save_path="models/confusion_matrix.png")

    # ── Overall accuracy ────────────────────────────────────
    accuracy = (preds == labels).sum() / len(labels)
    print(f"\nOverall Test Accuracy: {accuracy:.4f}")


if __name__ == "__main__":
    main()
