# 🌿 Crop Disease Intelligent Agent
### DCIT 403 – Intelligent Agent System (Prometheus Methodology)

An intelligent **BDI (Belief-Desire-Intention) agent** that autonomously diagnoses crop diseases from leaf images using deep learning (ResNet-18 transfer learning). Built following the **Prometheus agent-design methodology** for an academic semester project.

---

## Architecture

```
                ┌──────────────────────────────────────────┐
                │           CropDiseaseAgent                │
                │                                          │
Percept ───────►│  perceive()  → decide()  → act()         │──────► Action
                │                                          │
                │  Beliefs: disease_history, confidence,   │
                │           plot_health_map, weather        │
                │  Goals:   diagnose, treat, monitor        │
                │  Plans:   diagnose_single,                │
                │           handle_low_confidence,          │
                │           handle_unknown, batch_monitor   │
                │                                          │
                │  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
                │  │Perception│ │Decision  │ │ Action   │ │
                │  │ResNet-18 │ │Engine    │ │Recommend │ │
                │  │CNN       │ │Softmax   │ │Escalate  │ │
                │  └──────────┘ └──────────┘ └──────────┘ │
                └──────────────────────────────────────────┘
```

| Module | File | Role |
|--------|------|------|
| BDI Agent | `agent/agent.py` | BeliefBase, Goals, Plans, perceive→decide→act loop |
| Perception | `agent/perception.py` | Image preprocessing & ResNet-18 feature extraction |
| Decision | `agent/decision.py` | Softmax classification, confidence scoring & treatment DB |
| Environment | `agent/environment.py` | Simulated crop field with percept generation & disease spread |
| Training | `train.py` | Fine-tune ResNet-18 on the PlantVillage dataset |
| Evaluation | `evaluate.py` | Accuracy, F1, confusion matrix |
| Simulation | `simulation.py` | Demonstrates BDI loop across multiple time steps |
| Web UI | `app.py` | Gradio drag-and-drop diagnosis interface |

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/<your-username>/Crop-Disease-Inteligent-Agent.git
cd Crop-Disease-Inteligent-Agent

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
```

### 2. Run the Simulation (no model required)

The simulation demonstrates the full BDI agent loop in **synthetic mode** — no trained model or dataset needed:

```bash
python simulation.py --synthetic --steps 3 --plots 6
```

This shows:
- **◄ PERCEPT** — events arriving from the simulated crop field
- **● DECIDE** — which plan the agent selects (based on beliefs + goals)
- **► ACT** — the action taken (diagnose, escalate, monitor, etc.)
- **↳ Env response** — how the environment reacts to the agent's action

---

## Full Setup (with Trained Model)

### 3. Download the dataset

```bash
pip install kaggle
python download_dataset.py --download
```

> Requires a Kaggle API token saved to `C:\Users\<you>\.kaggle\kaggle.json`.

### 4. Train the model

```bash
python train.py --epochs 20 --batch_size 32 --lr 0.001
```

Saves `models/crop_disease_model.pth` and `models/class_names.json`.

### 5. Evaluate

```bash
python evaluate.py
```

Prints classification report, saves `models/confusion_matrix.png`.

### 6. Run the Web App

```bash
python app.py
```

Open **http://localhost:7860** — upload a leaf image for instant diagnosis.

### 7. Run simulation with real model

```bash
python simulation.py --real --steps 3 --plots 6 --dataset dataset
```

---

## Dataset Layout

```
dataset/
├── train/
│   ├── Tomato___Early_blight/
│   ├── Tomato___healthy/
│   ├── Corn_(maize)___Common_rust_/
│   └── ...
└── test/
    ├── Tomato___Early_blight/
    └── ...
```

---

## Prometheus Design Report

See [`PROMETHEUS_REPORT.md`](PROMETHEUS_REPORT.md) for the complete design document covering:
- **Phase 1** – System Specification (problem, goals, scenarios, environment)
- **Phase 2** – Architectural Design (agent types, acquaintance diagram)
- **Phase 3** – Interaction Design (sequence diagrams, message structures)
- **Phase 4** – Detailed Design (capabilities, plans, beliefs, percepts/actions)
- **Phase 5** – Implementation report (~630 words)

---

## Project Structure

```
Crop-Disease-Inteligent-Agent/
├── agent/
│   ├── __init__.py          # package exports
│   ├── agent.py             # BDI agent (perceive→decide→act)
│   ├── perception.py        # image preprocessing & CNN inference
│   ├── decision.py          # classification & treatment DB
│   └── environment.py       # simulated crop field
├── models/                  # saved model checkpoints (after training)
├── dataset/                 # PlantVillage images (after download)
├── app.py                   # Gradio web interface
├── simulation.py            # BDI loop demonstration
├── train.py                 # model training script
├── evaluate.py              # model evaluation script
├── download_dataset.py      # Kaggle dataset downloader
├── requirements.txt         # Python dependencies
└── PROMETHEUS_REPORT.md     # Full Prometheus design report
```

---

## License

MIT
