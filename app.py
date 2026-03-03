"""
Gradio web application — drag-and-drop crop disease diagnosis.

Usage
-----
    python app.py

Then open http://localhost:7860 in your browser.
"""

import os
import gradio as gr
from agent import CropDiseaseAgent


# ------------------------------------------------------------------ #
#  Configuration                                                      #
# ------------------------------------------------------------------ #

MODEL_PATH = os.environ.get("MODEL_PATH", "models/crop_disease_model.pth")
CLASS_NAMES_PATH = os.environ.get("CLASS_NAMES_PATH", "models/class_names.json")


# ------------------------------------------------------------------ #
#  Agent initialisation                                               #
# ------------------------------------------------------------------ #

agent: CropDiseaseAgent | None = None


def get_agent() -> CropDiseaseAgent:
    """Lazy-load the agent so the app can still start even if the model
    is missing (useful during development)."""
    global agent
    if agent is None:
        agent = CropDiseaseAgent(MODEL_PATH, CLASS_NAMES_PATH)
    return agent


# ------------------------------------------------------------------ #
#  Inference function                                                 #
# ------------------------------------------------------------------ #

def predict(image):
    """Called by Gradio when a user uploads an image."""
    if image is None:
        return "⚠️ Please upload an image.", "", ""

    try:
        result = get_agent().diagnose(image)
    except FileNotFoundError as e:
        return (
            f"⚠️ Model not found: {e}\n\n"
            "Please train the model first with `python train.py`.",
            "", "",
        )
    except Exception as e:
        return f"❌ Error during diagnosis: {e}", "", ""

    # Format top predictions
    top_preds = "\n".join(
        f"  • {p['class'].replace('_', ' ')}  —  {p['confidence']:.2%}"
        for p in result.top_predictions
    )

    disease_display = result.disease.replace("_", " ")
    confidence_display = f"{result.confidence:.2%}"

    diagnosis_text = (
        f"🌿 **Disease:** {disease_display}\n\n"
        f"📊 **Confidence:** {confidence_display}\n\n"
        f"🏥 **Treatment:**\n{result.treatment}\n\n"
        f"📋 **Top Predictions:**\n{top_preds}"
    )

    return diagnosis_text


# ------------------------------------------------------------------ #
#  Gradio UI                                                          #
# ------------------------------------------------------------------ #

def build_app() -> gr.Blocks:
    """Construct the Gradio Blocks app."""
    with gr.Blocks(
        title="🌿 Crop Disease Intelligent Agent",
        theme=gr.themes.Soft(primary_hue="green"),
    ) as app:
        gr.Markdown(
            """
            # 🌿 Crop Disease Intelligent Agent
            Upload a photo of a crop leaf and get an instant AI-powered diagnosis
            with treatment recommendations.
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                image_input = gr.Image(
                    label="Upload Leaf Image",
                    type="pil",
                    height=350,
                )
                submit_btn = gr.Button("🔍 Diagnose", variant="primary", size="lg")

            with gr.Column(scale=1):
                output = gr.Markdown(label="Diagnosis Result")

        submit_btn.click(fn=predict, inputs=image_input, outputs=output)
        image_input.change(fn=predict, inputs=image_input, outputs=output)

        gr.Markdown(
            """
            ---
            **How it works:** The agent uses a ResNet-18 deep learning model fine-tuned
            on crop disease images.  It follows a *Perception → Decision* pipeline to
            identify the disease and recommend a treatment.

            ⚠️ *This tool is for educational purposes. Always consult an agricultural
            expert for critical decisions.*
            """
        )

    return app


# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860)
