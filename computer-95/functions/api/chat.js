// /api/chat · Ollama-shape chat endpoint.
//
// The version2.hosted.html shell speaks Ollama's wire format
// (POST {model, messages, stream:true} → NDJSON of {message:{content},done}).
// Local Ollama isn't reachable from a public visitor's browser, so this
// endpoint translates the request to chatStream() / chatCompletion() (HF
// Router with local-tunnel + Workers-AI fallback) and re-encodes the
// response as NDJSON so the existing client code keeps working unchanged.

import { chatStream, chatCompletion } from "../_llm.js";

const OLLAMA_TO_HF = {
  "roadlm:latest": "Qwen/Qwen2.5-72B-Instruct",
  "qwen2.5:72b": "Qwen/Qwen2.5-72B-Instruct",
  "qwen2.5-coder:7b": "Qwen/Qwen2.5-Coder-7B-Instruct",
  "qwen2.5:7b": "Qwen/Qwen2.5-7B-Instruct",
  "qwen2.5:3b": "Qwen/Qwen2.5-7B-Instruct",
  "qwen2.5:1.5b": "Qwen/Qwen2.5-7B-Instruct",
  "qwen2.5:0.5b": "Qwen/Qwen2.5-7B-Instruct",
};

function resolveModel(m) {
  if (!m) return undefined;
  if (m.includes("/")) return m;
  return OLLAMA_TO_HF[m] || undefined;
}

function ndjsonLine(obj) {
  return JSON.stringify(obj) + "\n";
}

async function workersAiFallback(env, { messages, model }) {
  if (!env?.AI) return null;
  try {
    const r = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
      messages,
      max_tokens: 700,
      temperature: 0.4,
    });
    return { content: r?.response || "", model: "@cf/meta/llama-3.1-8b-instruct", source: "workers-ai" };
  } catch {
    return null;
  }
}

export const onRequestPost = async ({ request, env }) => {
  const body = await request.json().catch(() => ({}));
  const messages = Array.isArray(body.messages) ? body.messages : [];
  if (!messages.length) {
    return new Response(JSON.stringify({ error: "messages required" }), {
      status: 400,
      headers: { "content-type": "application/json" },
    });
  }
  const requestedModel = body.model || "";
  const hfModel = resolveModel(requestedModel);
  const wantStream = body.stream !== false;

  const enc = new TextEncoder();
  const upstreamCtrl = new AbortController();
  request.signal?.addEventListener("abort", () => upstreamCtrl.abort());

  if (!wantStream) {
    try {
      const { content, model: usedModel } = await chatCompletion(env, { messages, model: hfModel });
      return new Response(JSON.stringify({
        model: requestedModel || usedModel,
        message: { role: "assistant", content },
        done: true,
      }), { headers: { "content-type": "application/json" } });
    } catch (e) {
      const fb = await workersAiFallback(env, { messages, model: hfModel });
      if (fb) {
        return new Response(JSON.stringify({
          model: requestedModel || fb.model,
          message: { role: "assistant", content: fb.content },
          done: true,
        }), { headers: { "content-type": "application/json" } });
      }
      return new Response(JSON.stringify({ error: e.message || "chat failed" }), {
        status: 502, headers: { "content-type": "application/json" },
      });
    }
  }

  const stream = new ReadableStream({
    async start(controller) {
      const send = (obj) => controller.enqueue(enc.encode(ndjsonLine(obj)));
      try {
        const { response: r, model: usedModel } = await chatStream(env, {
          messages, model: hfModel, max_tokens: 700, temperature: 0.4, signal: upstreamCtrl.signal,
        });
        const reader = r.body.getReader();
        const dec = new TextDecoder();
        let buf = "";
        let any = false;
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buf += dec.decode(value, { stream: true });
          const lines = buf.split("\n");
          buf = lines.pop();
          for (const line of lines) {
            const t = line.trim();
            if (!t.startsWith("data:")) continue;
            const data = t.slice(5).trim();
            if (data === "[DONE]") continue;
            try {
              const j = JSON.parse(data);
              const tok = j.choices?.[0]?.delta?.content;
              if (tok) {
                any = true;
                send({ model: requestedModel || usedModel, message: { role: "assistant", content: tok }, done: false });
              }
            } catch {}
          }
        }
        if (!any) {
          const fb = await workersAiFallback(env, { messages, model: hfModel });
          if (fb?.content) {
            send({ model: requestedModel || fb.model, message: { role: "assistant", content: fb.content }, done: false });
          }
        }
        send({ model: requestedModel || usedModel, message: { role: "assistant", content: "" }, done: true });
      } catch (e) {
        const fb = await workersAiFallback(env, { messages, model: hfModel });
        if (fb?.content) {
          send({ model: requestedModel || fb.model, message: { role: "assistant", content: fb.content }, done: false });
          send({ model: requestedModel || fb.model, message: { role: "assistant", content: "" }, done: true });
        } else {
          send({ error: e.message || "chat failed", done: true });
        }
      } finally {
        controller.close();
      }
    },
    cancel() { upstreamCtrl.abort(); },
  });

  return new Response(stream, {
    headers: {
      "content-type": "application/x-ndjson",
      "cache-control": "no-store",
      "x-accel-buffering": "no",
    },
  });
};

export const onRequestGet = () =>
  new Response(JSON.stringify({ endpoint: "/api/chat", methods: ["POST"], shape: "ollama" }), {
    headers: { "content-type": "application/json" },
  });
