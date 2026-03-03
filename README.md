# 🌿 Crop Disease Intelligent Agent

An intelligent agent system for detecting and diagnosing crop diseases from leaf images using deep learning (ResNet-18 transfer learning), structured as a **Perception → Decision → Action** pipeline with a Gradio web interface.

## Architecture

```
Input Image → [Perception Layer] → [Decision Engine] → Diagnosis Result
                  │                       │
           ResNet-18 CNN           Softmax + Treatment DB
          Feature Extraction       Class + Confidence + Rx
```

| Module | File | Role |
|--------|------|------|
| Perception | `agent/perception.py` | Image preprocessing & CNN feature extraction |
| Decision | `agent/decision.py` | Classification, confidence scoring & treatment recommendation |
| Orchestrator | `agent/agent.py` | End-to-end diagnosis pipeline |
| Training | `train.py` | Fine-tune ResNet-18 on your dataset |
| Evaluation | `evaluate.py` | Accuracy, F1, confusion matrix |
| Web UI | `app.py` | Gradio interface for drag-and-drop diagnosis |

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/Crop-Disease-Inteligent-Agent.git
cd Crop-Disease-Inteligent-Agent

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Dataset

Organise your dataset in **ImageFolder** format:

```
dataset/
├── train/
│   ├── Tomato_Blight/
│   │   ├── img001.jpg
│   │   └── ...
│   ├── Corn_Rust/
│   └── Healthy/
└── test/
    ├── Tomato_Blight/
    ├── Corn_Rust/
    └── Healthy/
```

> **Tip:** The [PlantVillage](https://www.kaggle.com/datasets/emmarex/plantdisease) dataset on Kaggle works out of the box.

## Usage

### Train

```bash
python train.py --epochs 20 --batch_size 32 --lr 0.001
```

The best model checkpoint is saved to `models/crop_disease_model.pth`.

### Evaluate

```bash
python evaluate.py
```

Prints a classification report and saves a confusion matrix to `models/confusion_matrix.png`.

### Run the Web App

```bash
python app.py
```

Open **http://localhost:7860** in your browser, upload a leaf image, and get an instant diagnosis.

## License

MIT
