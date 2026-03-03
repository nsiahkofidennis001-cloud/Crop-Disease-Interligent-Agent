"""
Dataset utility — download from Kaggle and/or split into train/test.

Usage
-----
# Option 1: Download the pre-split "New Plant Diseases" dataset from Kaggle
python download_dataset.py --download

# Option 2: Split an existing folder of class sub-directories into train/test
python download_dataset.py --split --source path/to/all_classes --ratio 0.8

Prerequisites (for --download)
------------------------------
1. pip install kaggle
2. Create a Kaggle API token:
   - Go to https://www.kaggle.com → Your Profile → Account → Create New Token
   - Save the downloaded kaggle.json to:
       Windows:  C:\\Users\\<you>\\.kaggle\\kaggle.json
       Linux:    ~/.kaggle/kaggle.json
"""

import argparse
import os
import shutil
import random


# ------------------------------------------------------------------ #
#  Download from Kaggle                                               #
# ------------------------------------------------------------------ #

def download_from_kaggle(dest_dir: str = "dataset"):
    """Download the 'New Plant Diseases' dataset (already split into
    train/valid) and reorganise into dataset/train and dataset/test."""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("❌ kaggle package not installed. Run:  pip install kaggle")
        return

    api = KaggleApi()
    api.authenticate()

    dataset_slug = "vipoooool/new-plant-diseases-dataset"
    download_path = os.path.join(dest_dir, "_raw")

    print(f"⬇️  Downloading '{dataset_slug}' …")
    api.dataset_download_files(dataset_slug, path=download_path, unzip=True)
    print("✅ Download complete.")

    # The dataset extracts as:
    #   _raw/New Plant Diseases Dataset(Augmented)/New Plant Diseases Dataset(Augmented)/train/
    #   _raw/New Plant Diseases Dataset(Augmented)/New Plant Diseases Dataset(Augmented)/valid/
    # We need to find the actual train/ and valid/ folders.

    raw_train = None
    raw_valid = None
    for root, dirs, _ in os.walk(download_path):
        if "train" in dirs:
            raw_train = os.path.join(root, "train")
        if "valid" in dirs:
            raw_valid = os.path.join(root, "valid")
        if raw_train and raw_valid:
            break

    if not raw_train or not raw_valid:
        print("⚠️  Could not locate train/valid inside the download.")
        print(f"   Please check {download_path} manually.")
        return

    # Move to dataset/train and dataset/test
    final_train = os.path.join(dest_dir, "train")
    final_test = os.path.join(dest_dir, "test")

    if os.path.exists(final_train):
        shutil.rmtree(final_train)
    if os.path.exists(final_test):
        shutil.rmtree(final_test)

    shutil.move(raw_train, final_train)
    shutil.move(raw_valid, final_test)

    # Clean up raw download
    shutil.rmtree(download_path, ignore_errors=True)

    train_classes = sorted(os.listdir(final_train))
    test_classes = sorted(os.listdir(final_test))
    train_count = sum(len(os.listdir(os.path.join(final_train, c))) for c in train_classes)
    test_count = sum(len(os.listdir(os.path.join(final_test, c))) for c in test_classes)

    print(f"\n📂 Dataset ready!")
    print(f"   Train: {train_count:,} images across {len(train_classes)} classes")
    print(f"   Test:  {test_count:,} images across {len(test_classes)} classes")
    print(f"   Path:  {os.path.abspath(dest_dir)}")


# ------------------------------------------------------------------ #
#  Split an existing folder                                           #
# ------------------------------------------------------------------ #

def split_dataset(source_dir: str, dest_dir: str = "dataset", ratio: float = 0.8, seed: int = 42):
    """Split a single ImageFolder directory into train/ and test/.

    Parameters
    ----------
    source_dir : path containing class sub-folders, e.g. PlantVillage/
    dest_dir   : output root (will create train/ and test/ inside)
    ratio      : fraction of images to put in train (default 0.8)
    seed       : random seed for reproducibility
    """
    random.seed(seed)

    train_dir = os.path.join(dest_dir, "train")
    test_dir = os.path.join(dest_dir, "test")

    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)

    classes = sorted([
        d for d in os.listdir(source_dir)
        if os.path.isdir(os.path.join(source_dir, d))
    ])

    if not classes:
        print(f"❌ No class sub-folders found in {source_dir}")
        return

    total_train = 0
    total_test = 0

    for cls in classes:
        cls_src = os.path.join(source_dir, cls)
        images = [
            f for f in os.listdir(cls_src)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"))
        ]
        random.shuffle(images)

        split_idx = int(len(images) * ratio)
        train_imgs = images[:split_idx]
        test_imgs = images[split_idx:]

        # Create class folders
        cls_train = os.path.join(train_dir, cls)
        cls_test = os.path.join(test_dir, cls)
        os.makedirs(cls_train, exist_ok=True)
        os.makedirs(cls_test, exist_ok=True)

        for img in train_imgs:
            shutil.copy2(os.path.join(cls_src, img), os.path.join(cls_train, img))
        for img in test_imgs:
            shutil.copy2(os.path.join(cls_src, img), os.path.join(cls_test, img))

        total_train += len(train_imgs)
        total_test += len(test_imgs)
        print(f"  {cls:<45s}  train: {len(train_imgs):>5d}  test: {len(test_imgs):>5d}")

    print(f"\n📂 Split complete!")
    print(f"   Train: {total_train:,} images")
    print(f"   Test:  {total_test:,} images")
    print(f"   Path:  {os.path.abspath(dest_dir)}")


# ------------------------------------------------------------------ #
#  Main                                                               #
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(
        description="Download or split a crop disease dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--download", action="store_true",
                        help="Download the New Plant Diseases dataset from Kaggle")
    parser.add_argument("--split", action="store_true",
                        help="Split an existing folder into train/test")
    parser.add_argument("--source", type=str, default=None,
                        help="Source directory for --split (folder of class sub-dirs)")
    parser.add_argument("--dest", type=str, default="dataset",
                        help="Destination directory (default: dataset/)")
    parser.add_argument("--ratio", type=float, default=0.8,
                        help="Train ratio for --split (default: 0.8)")
    args = parser.parse_args()

    if not args.download and not args.split:
        parser.print_help()
        print("\n⚠️  Specify --download or --split (or both).")
        return

    if args.download:
        download_from_kaggle(args.dest)

    if args.split:
        if not args.source:
            print("❌ --split requires --source <path_to_class_folders>")
            return
        split_dataset(args.source, args.dest, args.ratio)


if __name__ == "__main__":
    main()
