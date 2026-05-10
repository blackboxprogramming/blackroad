// /api/tags · Ollama-shape model list.
//
// version2.hosted.html populates the model picker from this endpoint
// (Ollama's /api/tags wire format: { models: [{ name, modified_at, size }] }).
// We surface the HF-Router models that /api/chat actually understands, plus
// nicknames the existing client already prefers (roadlm:latest, qwen2.5*).

const NOW = new Date().toISOString();

const MODELS = [
  // Nicknames the picker prefers — keep these first.
  { name: "roadlm:latest" },
  { name: "qwen2.5-coder:7b" },
  { name: "qwen2.5:7b" },
  { name: "qwen2.5:3b" },
  { name: "qwen2.5:0.5b" },
  // HF-Router-resolvable ids for callers that pass a slash-form id directly.
  { name: "Qwen/Qwen2.5-72B-Instruct" },
  { name: "Qwen/Qwen2.5-7B-Instruct" },
  { name: "Qwen/Qwen2.5-Coder-7B-Instruct" },
  { name: "meta-llama/Llama-3.3-70B-Instruct" },
  { name: "meta-llama/Llama-3.1-8B-Instruct" },
];

export const onRequestGet = () =>
  new Response(JSON.stringify({
    models: MODELS.map((m) => ({
      name: m.name,
      model: m.name,
      modified_at: NOW,
      size: 0,
      digest: "",
      details: { family: "qwen2.5", parameter_size: "via /api/chat", quantization_level: "Q?" },
    })),
  }), {
    headers: {
      "content-type": "application/json",
      "cache-control": "public, max-age=60",
      "access-control-allow-origin": "*",
    },
  });
