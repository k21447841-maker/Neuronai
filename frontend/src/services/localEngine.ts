const STORE_KEY = "neuroflow_standalone_db_v1";

interface LocalDB {
  providers: Record<string, { apiKey: string; model: string; status: string; lastError: string | null }>;
  projects: any[];
  scripts: Record<string, { script: any; scenes: any[] }>;
  images: any[];
  audios: any[];
  videos: any[];
  workflows: any[];
  usage: any[];
}

const CATALOG = [
  { slug: "claude", display_name: "Anthropic Claude", category: "llm", default_model: "claude-3-7-sonnet-20250219", available_models: ["claude-3-7-sonnet-20250219", "claude-3-5-haiku-20241022"] },
  { slug: "deepseek", display_name: "DeepSeek", category: "llm", default_model: "deepseek-chat", available_models: ["deepseek-chat", "deepseek-reasoner"] },
  { slug: "gemini", display_name: "Google Gemini", category: "llm", default_model: "gemini-2.5-flash", available_models: ["gemini-2.5-flash", "gemini-2.5-pro"] },
  { slug: "elevenlabs", display_name: "ElevenLabs Voice", category: "voice", default_model: "eleven_multilingual_v2", available_models: ["eleven_multilingual_v2", "eleven_turbo_v2_5"] },
  { slug: "openai_images", display_name: "OpenAI Visual / DALL-E", category: "visual", default_model: "dall-e-3", available_models: ["dall-e-3", "gpt-image-1"] },
];

function readDB(): LocalDB {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) return JSON.parse(raw) as LocalDB;
  } catch { /* ignore */ }
  return { providers: {}, projects: [], scripts: {}, images: [], audios: [], videos: [], workflows: [], usage: [] };
}

function writeDB(db: LocalDB): void {
  localStorage.setItem(STORE_KEY, JSON.stringify(db));
}

function mask(k: string): string {
  return k.length <= 8 ? "****" : `${k.slice(0, 4)}...${k.slice(-4)}`;
}

async function callLLM(slug: string, systemPrompt: string, userPrompt: string): Promise<{ text: string; tokens: number }> {
  const db = readDB();
  const cfg = db.providers[slug];
  if (!cfg?.apiKey) throw new Error(`Please save your ${slug} API key in API Integrations first.`);

  if (slug === "claude") {
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": cfg.apiKey,
        "anthropic-version": "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true",
        "content-type": "application/json",
      },
      body: JSON.stringify({ model: cfg.model, max_tokens: 4096, system: systemPrompt, messages: [{ role: "user", content: userPrompt }] }),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d?.error?.message || `Claude error ${r.status}`);
    const text = (d.content || []).map((b: any) => b.text || "").join("");
    return { text, tokens: (d.usage?.input_tokens || 0) + (d.usage?.output_tokens || 0) };
  }

  if (slug === "deepseek") {
    const r = await fetch("https://api.deepseek.com/chat/completions", {
      method: "POST",
      headers: { Authorization: `Bearer ${cfg.apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({ model: cfg.model, messages: [{ role: "system", content: systemPrompt }, { role: "user", content: userPrompt }] }),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d?.error?.message || `DeepSeek error ${r.status}`);
    return { text: d.choices?.[0]?.message?.content || "", tokens: d.usage?.total_tokens || 0 };
  }

  if (slug === "gemini") {
    const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${cfg.model}:generateContent?key=${encodeURIComponent(cfg.apiKey)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: systemPrompt }] },
        contents: [{ parts: [{ text: userPrompt }] }],
      }),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d?.error?.message || `Gemini error ${r.status}`);
    const text = (d.candidates?.[0]?.content?.parts || []).map((p: any) => p.text || "").join("");
    return { text, tokens: d.usageMetadata?.totalTokenCount || 0 };
  }

  throw new Error(`Unsupported LLM: ${slug}`);
}

function bufferToWavDataUrl(audioBuffer: AudioBuffer, startSample: number, endSample: number): string {
  const len = Math.max(1, endSample - startSample);
  const channels = audioBuffer.numberOfChannels;
  const sampleRate = audioBuffer.sampleRate;
  const wavBytes = 44 + len * channels * 2;
  const buf = new ArrayBuffer(wavBytes);
  const view = new DataView(buf);
  const writeStr = (off: number, s: string) => { for (let i = 0; i < s.length; i++) view.setUint8(off + i, s.charCodeAt(i)); };

  writeStr(0, "RIFF");
  view.setUint32(4, wavBytes - 8, true);
  writeStr(8, "WAVE");
  writeStr(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, channels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * channels * 2, true);
  view.setUint16(32, channels * 2, true);
  view.setUint16(34, 16, true);
  writeStr(36, "data");
  view.setUint32(40, len * channels * 2, true);

  let offset = 44;
  for (let i = startSample; i < endSample; i++) {
    for (let ch = 0; ch < channels; ch++) {
      const sample = Math.max(-1, Math.min(1, audioBuffer.getChannelData(ch)[i] || 0));
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
      offset += 2;
    }
  }
  const bytes = new Uint8Array(buf);
  let bin = "";
  for (let i = 0; i < bytes.length; i += 8192) {
    bin += String.fromCharCode(...bytes.subarray(i, i + 8192));
  }
  return `data:audio/wav;base64,${btoa(bin)}`;
}

export async function localApiHandler<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method || "GET").toUpperCase();
  const body = options.body ? JSON.parse(String(options.body)) : {};
  const db = readDB();

  if (path === "/api/analytics/overview") {
    return {
      total_generated_videos: db.videos.length,
      total_published_videos: 0,
      total_scheduled_videos: 0,
      failed_generation_jobs: 0,
      connected_channels: 0,
      voice_characters_used: db.usage.filter((u) => u.provider_slug === "elevenlabs").reduce((a, b) => a + b.units_consumed, 0),
    } as T;
  }

  if (path === "/api/projects" && method === "GET") return db.projects as T;
  if (path === "/api/projects" && method === "POST") {
    const proj = { id: crypto.randomUUID(), ...body, status: "draft", created_at: new Date().toISOString() };
    db.projects.unshift(proj);
    writeDB(db);
    return proj as T;
  }

  if (path === "/api/providers" && method === "GET") {
    return CATALOG.map((c) => {
      const s = db.providers[c.slug];
      return {
        ...c,
        configured: Boolean(s?.apiKey),
        key_hint: s?.apiKey ? mask(s.apiKey) : null,
        selected_model: s?.model || c.default_model,
        is_enabled: Boolean(s?.apiKey),
        connection_status: s?.status || "unconfigured",
        last_error: s?.lastError || null,
      };
    }) as T;
  }

  if (path === "/api/providers" && method === "PUT") {
    const prev = db.providers[body.provider_slug] || { apiKey: "", model: body.selected_model, status: "unverified", lastError: null };
    db.providers[body.provider_slug] = {
      apiKey: body.api_key ? String(body.api_key).trim() : prev.apiKey,
      model: body.selected_model || prev.model,
      status: body.api_key ? "unverified" : prev.status,
      lastError: null,
    };
    writeDB(db);
    return { status: "saved" } as T;
  }

  if (path.startsWith("/api/providers/") && path.endsWith("/test")) {
    const slug = path.split("/")[3];
    const cfg = db.providers[slug];
    if (!cfg?.apiKey) throw new Error("Save API key first.");
    try {
      if (["claude", "deepseek", "gemini"].includes(slug)) {
        await callLLM(slug, "Reply OK.", "Ping");
      } else if (slug === "elevenlabs") {
        const r = await fetch("https://api.elevenlabs.io/v1/user/subscription", { headers: { "xi-api-key": cfg.apiKey } });
        if (!r.ok) throw new Error(`ElevenLabs auth failed (${r.status})`);
      } else if (slug === "openai_images") {
        const r = await fetch("https://api.openai.com/v1/models", { headers: { Authorization: `Bearer ${cfg.apiKey}` } });
        if (!r.ok) throw new Error(`OpenAI auth failed (${r.status})`);
      }
      db.providers[slug].status = "connected";
      db.providers[slug].lastError = null;
      writeDB(db);
      return { status: "connected" } as T;
    } catch (e: any) {
      db.providers[slug].status = "error";
      db.providers[slug].lastError = e.message;
      writeDB(db);
      throw e;
    }
  }

  if (path.startsWith("/api/scripts/project/")) {
    const pid = path.split("/").pop() || "";
    return (db.scripts[pid] || { script: null, versions: [], scenes: [] }) as T;
  }

  if (path === "/api/scripts/generate" && method === "POST") {
    const sys = "Return valid JSON ONLY (no markdown) with keys: hook, introduction, body, ending, call_to_action, scenes (array of scene_number, narration, estimated_duration_seconds, visual_description, camera_movement).";
    const usr = `Topic: ${body.topic}\nNiche: ${body.niche}\nLanguage: ${body.language || "en"}\nDuration: ${body.duration_seconds || 180}s\nTone: ${body.tone || "engaging"}`;
    const res = await callLLM(body.provider_slug || "gemini", sys, usr);
    const cleaned = res.text.trim().replace(/^```json\s*/i, "").replace(/^```\s*/, "").replace(/```$/, "").trim();
    const parsed = JSON.parse(cleaned);
    const fullText = [parsed.hook, parsed.introduction, parsed.body, parsed.ending, parsed.call_to_action].filter(Boolean).join("\n\n");
    const scenes = (parsed.scenes || []).map((s: any, idx: number) => ({ id: crypto.randomUUID(), scene_number: s.scene_number || idx + 1, ...s }));
    db.scripts[body.project_id] = {
      script: { id: crypto.randomUUID(), ...parsed, full_text: fullText, current_version: 1 },
      scenes,
    };
    db.usage.unshift({ id: crypto.randomUUID(), provider_slug: body.provider_slug, operation: "script_generation", units_consumed: res.tokens, unit_type: "tokens", created_at: new Date().toISOString() });
    writeDB(db);
    return { script_id: db.scripts[body.project_id].script.id, scene_count: scenes.length } as T;
  }

  if (path === "/api/voice/library") {
    const cfg = db.providers.elevenlabs;
    if (!cfg?.apiKey) throw new Error("Add your ElevenLabs API key in API Integrations first.");
    const r = await fetch("https://api.elevenlabs.io/v1/voices", { headers: { "xi-api-key": cfg.apiKey } });
    const d = await r.json();
    if (!r.ok) throw new Error(d?.detail?.message || `ElevenLabs error ${r.status}`);
    return { voices: d.voices || [] } as T;
  }

  if (path === "/api/voice/generate" && method === "POST") {
    const cfg = db.providers.elevenlabs;
    if (!cfg?.apiKey) throw new Error("Add your ElevenLabs API key in API Integrations first.");
    const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${body.voice_id}`, {
      method: "POST",
      headers: { "xi-api-key": cfg.apiKey, Accept: "audio/mpeg", "Content-Type": "application/json" },
      body: JSON.stringify({
        text: body.text,
        model_id: cfg.model || "eleven_multilingual_v2",
        voice_settings: { stability: body.stability ?? 0.5, similarity_boost: body.similarity_boost ?? 0.75 },
      }),
    });
    if (!r.ok) throw new Error(`ElevenLabs TTS failed (${r.status})`);
    const ab = await r.arrayBuffer();
    const bytes = new Uint8Array(ab);
    let bin = "";
    for (let i = 0; i < bytes.length; i += 8192) bin += String.fromCharCode(...bytes.subarray(i, i + 8192));
    const dataUrl = `data:audio/mpeg;base64,${btoa(bin)}`;
    const row = { id: crypto.randomUUID(), project_id: body.project_id, voice_name: body.voice_name || "ElevenLabs", duration_seconds: Math.max(2, Math.round(body.text.length / 15)), url: dataUrl, created_at: new Date().toISOString() };
    db.audios.unshift(row);
    db.usage.unshift({ id: crypto.randomUUID(), provider_slug: "elevenlabs", operation: "tts_generation", units_consumed: body.text.length, unit_type: "characters", created_at: new Date().toISOString() });
    writeDB(db);
    return { audio_id: row.id, audio_url: dataUrl } as T;
  }

  if (path === "/api/voice/audio/edit" && method === "POST") {
    const audio = db.audios.find((a) => a.id === body.audio_id);
    if (!audio?.url) throw new Error("Audio track not found.");
    const res = await fetch(audio.url);
    const buf = await res.arrayBuffer();
    const ctx = new AudioContext();
    const decoded = await ctx.decodeAudioData(buf);
    const ch0 = decoded.getChannelData(0);
    const thresh = Math.pow(10, (body.silence_threshold_db || -35) / 20);
    let start = 0;
    let end = ch0.length - 1;
    while (start < end && Math.abs(ch0[start]) < thresh) start++;
    while (end > start && Math.abs(ch0[end]) < thresh) end--;
    const wavUrl = bufferToWavDataUrl(decoded, start, end);
    audio.url = wavUrl;
    audio.duration_seconds = Number(((end - start) / decoded.sampleRate).toFixed(2));
    writeDB(db);
    await ctx.close();
    return { job_id: `local-${audio.id}`, processed_url: wavUrl } as T;
  }

  if (path === "/api/media/visuals/generate" && method === "POST") {
    const cfg = db.providers.openai_images;
    if (!cfg?.apiKey) throw new Error("Add your OpenAI API key in API Integrations first.");
    const r = await fetch("https://api.openai.com/v1/images/generations", {
      method: "POST",
      headers: { Authorization: `Bearer ${cfg.apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({ model: cfg.model || "dall-e-3", prompt: body.prompt, size: "1024x1024", response_format: "b64_json", n: 1 }),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d?.error?.message || `OpenAI image error ${r.status}`);
    const url = `data:image/png;base64,${d.data[0].b64_json}`;
    const img = { id: crypto.randomUUID(), prompt: body.prompt, url, kind: body.asset_kind || "scene_frame", created_at: new Date().toISOString() };
    db.images.unshift(img);
    writeDB(db);
    return { image_id: img.id, url } as T;
  }

  if (path === "/api/media/jobs") return [] as T;
  if (path === "/api/library") return { images: db.images, videos: db.videos, audios: db.audios } as T;
  if (path === "/api/usage") return db.usage as T;
  if (path === "/api/youtube/channels") return [] as T;
  if (path === "/api/analytics/youtube") return { videos: [] } as T;

  if (path === "/api/automation/workflows" && method === "GET") return db.workflows as T;
  if (path === "/api/automation/workflows" && method === "POST") {
    const wf = { id: crypto.randomUUID(), ...body, status: "paused" };
    db.workflows.unshift(wf);
    writeDB(db);
    return wf as T;
  }

  throw new Error("This feature requires connecting a cloud backend URL in Settings.");
}
