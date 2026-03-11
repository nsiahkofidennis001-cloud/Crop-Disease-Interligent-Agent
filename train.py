"""
Training script — fine-tune a ResNet-18 on a crop-disease dataset.

Usage
-----
    python train.py --epochs 20 --batch_size 32 --lr 0.001

The dataset must be in ImageFolder layout::

    dataset/
    ├── train/<class>/*.jpg
    └── test/<class>/*.jpg

Outputs
-------
- models/crop_disease_model.pth  — best model weights
- models/class_names.json        — ordered list of class folder names
"""

import argparse
import json
import os
import copy

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


# ------------------------------------------------------------------ #
#  Data transforms                                                    #
# ------------------------------------------------------------------ #

def get_transforms(image_size: int = 224):
    """Return train (with augmentation) and validation transforms."""
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(image_size),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(25),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ])

    return train_transform, val_transform


# ------------------------------------------------------------------ #
#  Model builder                                                      #
# ------------------------------------------------------------------ #

def build_model(num_classes: int, freeze_backbone: bool = True):
    """Return a ResNet-18 with a replaced FC head."""
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

    # Optionally freeze all convolutional layers
    if freeze_backbone:
        for param in model.parameters():
            param.requires_grad = False

    # Replace the final fully-connected layer
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, num_classes),
    )

    return model


# ------------------------------------------------------------------ #
#  Training loop                                                      #
# ------------------------------------------------------------------ #

def train_model(
    model: nn.Module,
    dataloaders: dict,
    criterion,
    optimizer,
    device: str,
    num_epochs: int = 20,
):
    """Train and validate; return the best model weights."""
    best_weights = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch + 1}/{num_epochs}")
        print("-" * 40)

        for phase in ["train", "val"]:
            if phase == "train":
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0
            total_samples = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == "train"):
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    _, preds = torch.max(outputs, 1)

                    if phase == "train":
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels).item()
                total_samples += inputs.size(0)

            epoch_loss = running_loss / total_samples
            epoch_acc = running_corrects / total_samples

            print(f"  {phase:<5s}  Loss: {epoch_loss:.4f}  Acc: {epoch_acc:.4f}")

            # Save best validation model
            if phase == "val" and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_weights = copy.deepcopy(model.state_dict())

    print(f"\nBest validation accuracy: {best_acc:.4f}")
    model.load_state_dict(best_weights)
    return model


# ------------------------------------------------------------------ #
#  Main                                                               #
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(description="Train crop disease classifier")
    parser.add_argument("--data_dir", type=str, default="dataset",
                        help="Root dataset directory (must contain train/ and test/ subdirs)")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--image_size", type=int, default=224)
    parser.add_argument("--freeze", action="store_true", default=True,
                        help="Freeze backbone conv layers (default: True)")
    parser.add_argument("--no_freeze", dest="freeze", action="store_false")
    parser.add_argument("--output_dir", type=str, default="models")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # ── Data ────────────────────────────────────────────────
    train_transform, val_transform = get_transforms(args.image_size)

    train_dataset = datasets.ImageFolder(
        os.path.join(args.data_dir, "train"), transform=train_transform
    )
    val_dataset = datasets.ImageFolder(
        os.path.join(args.data_dir, "test"), transform=val_transform
    )

    dataloaders = {
        "train": DataLoader(train_dataset, batch_size=args.batch_size,
                            shuffle=True, num_workers=2, pin_memory=True),
        "val": DataLoader(val_dataset, batch_size=args.batch_size,
                          shuffle=False, num_workers=2, pin_memory=True),
    }

    class_names = train_dataset.classes
    num_classes = len(class_names)
    print(f"Found {num_classes} classes: {class_names}")

    # ── Model ───────────────────────────────────────────────
    model = build_model(num_classes, freeze_backbone=args.freeze).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()),
                           lr=args.lr)

    # Train 
    model = train_model(model, dataloaders, criterion, optimizer, device, args.epochs)

    # ── Save 
    os.makedirs(args.output_dir, exist_ok=True)
    model_path = os.path.join(args.output_dir, "crop_disease_model.pth")
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")

    class_names_path = os.path.join(args.output_dir, "class_names.json")
    with open(class_names_path, "w") as f:
        json.dump(class_names, f, indent=2)
    print(f"Class names saved to {class_names_path}")


if __name__ == "__main__":
    main()
