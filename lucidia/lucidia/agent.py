import os

def load_llm():
    model_path = os.environ.get("LUCIDIA_MODEL_PATH", "models/ggml-model.bin")
    try:
        from llama_cpp import Llama
        return Llama(model_path=model_path)
    except Exception as e:
        raise RuntimeError("llama-cpp-python not available or model missing. Install and set LUCIDIA_MODEL_PATH.") from e


def chat(prompt, llm=None, max_tokens=512):
    try:
        if llm is None:
            llm = load_llm()
    except Exception as e:
        return ("Lucidia is running but no local LLM available. "
                "Place a quantized ggml model in lucidia/models/ or set LUCIDIA_MODEL_PATH, "
                "and install llama-cpp-python. Error: " + str(e))
    try:
        out = llm.create(prompt=prompt, max_tokens=max_tokens)
        return out.get("choices", [{}])[0].get("text", "").strip()
    except Exception as e:
        return "LLM error: " + str(e)
