import os

def load_llm():
    model_path = os.environ.get("LUCIDIA_MODEL_PATH", "models/ggml-model.bin")
    try:
        from llama_cpp import Llama
        return Llama(model_path=model_path)
    except Exception as e:
        raise RuntimeError("llama-cpp-python not available or model missing. Install and set LUCIDIA_MODEL_PATH.") from e


def chat(prompt, llm=None, max_tokens=512):
    if llm is None:
        llm = load_llm()
    out = llm.create(prompt=prompt, max_tokens=max_tokens)
    return out.get("choices", [{}])[0].get("text", "").strip()
