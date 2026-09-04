import os
import uvicorn
import gradio as gr
from app.main import app as fastapi_app

# Informational dashboard shown when opening the Hugging Face Space URL directly in a browser
with gr.Blocks(title="IP-SAKTI Sahayak — Legal Backend") as demo:
    gr.Markdown("# 🏛️ IP-SAKTI Sahayak — AI Legal Backend")
    gr.Markdown("🟢 **Backend Status**: **ONLINE & READY** (Running on Free 16 GB RAM)")
    gr.Markdown(
        "This Hugging Face Space hosts the FastAPI statutory inference and retrieval engine for **IP-SAKTI Sahayak**."
    )
    with gr.Row():
        gr.Markdown("- 📡 **API Documentation**: [/docs](/docs)")
        gr.Markdown("- ❤️ **Health Check**: [/health](/health)")
        gr.Markdown("- 📜 **Statutory Corpus**: [/corpus](/corpus)")
        gr.Markdown("- 🛡️ **DPDP Minimal Audit**: [/admin/audit/view](/admin/audit/view)")

# Mount Gradio onto the existing FastAPI application
# All FastAPI routes (/ask, /ask/stream, /pdf/{filename}, /health, /feedback, etc.) remain intact
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
