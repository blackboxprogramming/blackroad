import os
import json
import urllib.request


def load_llm():
    model_path = os.environ.get("LUCIDIA_MODEL_PATH", "models/ggml-model.bin")
    try:
        from llama_cpp import Llama
        return Llama(model_path=model_path)
    except Exception as e:
        raise RuntimeError("llama-cpp-python not available or model missing. Install and set LUCIDIA_MODEL_PATH.") from e


def remote_chat_openai(prompt, max_tokens=512):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("No OPENAI_API_KEY in environment")
    model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    url = "https://api.openai.com/v1/chat/completions"
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        rj = json.load(resp)
    # Normalise OpenAI response shape
    if isinstance(rj, dict) and rj.get("choices"):
        c = rj["choices"][0]
        if isinstance(c.get("message"), dict):
            return c["message"].get("content", "")
        return c.get("text", "")
    raise RuntimeError("Unexpected OpenAI response: " + str(rj))


def chat(prompt, llm=None, max_tokens=512):
    # Try local LLM first
    try:
        if llm is None:
            llm = load_llm()
        out = llm.create(prompt=prompt, max_tokens=max_tokens)
        return out.get("choices", [{}])[0].get("text", "").strip()
    except Exception as local_err:
        # Fallback to remote OpenAI if configured
        try:
            return remote_chat_openai(prompt, max_tokens=max_tokens)
        except Exception as remote_err:
            return ("No local LLM and remote fallback failed. Local error: " + str(local_err) +
                    " | Remote error: " + str(remote_err))
