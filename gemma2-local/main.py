import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Chat-taugliche Variante:
MODEL_ID = os.getenv("MODEL_ID", "google/gemma-2-2b-it")

print("Lade Tokenizer/Modell ... (beim ersten Mal wird es heruntergeladen)")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto",  # nutzt automatisch CPU oder GPU
)

prompt = "Erkläre in 2 Sätzen einfach, was ein neuronales Netz ist."
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

outputs = model.generate(
    **inputs,
    max_new_tokens=120,
    do_sample=True,
    temperature=0.7,
)

print("\n--- Antwort ---\n")
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
