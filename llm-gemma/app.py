import os
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
# login() ist nicht nötig, wir geben den Token direkt an from_pretrained

MODEL_ID = os.getenv("MODEL_ID", "google/gemma-2-2b-it")
TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
DEFAULT_MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "80"))

app = FastAPI(title="Gemma API")

_tokenizer = None
_model = None

def ensure_model_loaded():
    global _tokenizer, _model
    if _tokenizer is not None and _model is not None:
        return

    print("Lade Gemma... (erster Ladevorgang kann dauern)")
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, token=TOKEN)

    # dtype statt torch_dtype verwenden (Warnung vermeiden)
    dtype = torch.float32  # CPU-sicher; auf GPU könntest du bfloat16 nehmen
    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        token=TOKEN,
        dtype=dtype,                 # <- hier statt torch_dtype
        device_map="auto",
        low_cpu_mem_usage=True,
    )

class GenIn(BaseModel):
    prompt: str
    max_new_tokens: int | None = None
    temperature: float | None = 0.7

@app.get("/health")
def health():
    return {"ok": True, "model_loaded": _model is not None}

@app.post("/generate")
def generate(inp: GenIn):
    try:
        ensure_model_loaded()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model load failed: {type(e).__name__}: {e}")

    inputs = _tokenizer(inp.prompt, return_tensors="pt").to(_model.device)
    out = _model.generate(
        **inputs,
        max_new_tokens=inp.max_new_tokens or DEFAULT_MAX_NEW_TOKENS,
        do_sample=True,
        temperature=inp.temperature or 0.7,
    )
    return {"text": _tokenizer.decode(out[0], skip_special_tokens=True)}
