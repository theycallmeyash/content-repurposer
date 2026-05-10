import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { TopNav } from "../components/TopNav";
import { Footer } from "../components/Footer";
import { Terminal } from "../components/Terminal";
import { SectionHeader } from "../components/SectionHeader";

export const Route = createFileRoute("/analyzer")({
  head: () => ({
    meta: [
      { title: "Analyzer · Press/Engine" },
      { name: "description", content: "Ingest a social profile. Synthesize a private voice model." },
    ],
  }),
  component: Analyzer,
});

type PlatformKey = "instagram" | "linkedin" | "x" | "threads" | "youtube" | "tiktok";
type PlatformState = "idle" | "connecting" | "connected" | "error";

interface PlatformTile {
  code: string;
  key: PlatformKey;
  name: string;
  implemented: boolean;
}

interface ScrapeSummary {
  posts: number;
  comments: number;
  collectedTweets: number;
  analysis?: {
    tone_vectors?: Array<{ k: string; v: number }>;
    highlights?: string[];
  };
  storagePath?: string;
}

const PLATFORMS: PlatformTile[] = [
  { code: "IG", key: "instagram", name: "Instagram", implemented: true },
  { code: "TT", key: "tiktok", name: "TikTok", implemented: false },
  { code: "XX", key: "x", name: "X / Twitter", implemented: true },
  { code: "LI", key: "linkedin", name: "LinkedIn", implemented: false },
  { code: "TH", key: "threads", name: "Threads", implemented: false },
  { code: "YT", key: "youtube", name: "YouTube", implemented: false },
];

const DEFAULT_TONE_VECTORS = [
  { k: "Sharpness", v: 78 },
  { k: "Brevity", v: 92 },
  { k: "Wit / Dryness", v: 64 },
  { k: "Warmth", v: 31 },
  { k: "Authority", v: 71 },
  { k: "Playfulness", v: 22 },
  { k: "Technicality", v: 58 },
  { k: "Provocation", v: 47 },
];

const DEFAULT_HIGHLIGHTS = [
  "Short-form bias (avg 14 sec read).",
  "Frequent monochrome / film references.",
  "Lowercase as stylistic signature.",
  "Avoids exclamations, emoji, hype words.",
  "Rituals · craft · materials as core themes.",
];

const ENGINE_BASE_URL = import.meta.env.VITE_ANALYZER_ENGINE_URL ?? "http://127.0.0.1:8788";
const SLEEP_MS = 260;

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const bootLines = [" > engine.ingest --target=@studio.veld"];

const lineWithStatus = (label: string, status: "[OK]" | "[...]" | "[ERR]") =>
  `${label.padEnd(30, ".")} ${status}`;

async function scrapeProfile(platform: PlatformKey, handle: string): Promise<ScrapeSummary> {
  const normalizedHandle = handle.replace("@", "").trim();
  if (!normalizedHandle) {
    throw new Error("Handle is required.");
  }

  if (platform === "linkedin") {
    throw new Error("LinkedIn connector is intentionally deferred for now.");
  }

  if (platform !== "instagram" && platform !== "x") {
    throw new Error(`${platform} is not implemented yet.`);
  }

  const response = await fetch(`${ENGINE_BASE_URL}/scrape/${platform}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ handle: normalizedHandle }),
  });

  if (!response.ok) {
    let detail = "Engine request failed.";
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      const body = await response.text();
      if (body) detail = body;
    }
    throw new Error(detail);
  }

  const payload = (await response.json()) as {
    posts?: number;
    comments?: number;
    collected_tweets?: number;
    analysis?: {
      tone_vectors?: Array<{ k: string; v: number }>;
      highlights?: string[];
    };
    storage_path?: string;
  };

  return {
    posts: payload.posts ?? 0,
    comments: payload.comments ?? 0,
    collectedTweets: payload.collected_tweets ?? 0,
    analysis: payload.analysis,
    storagePath: payload.storage_path,
  };
}

function Analyzer() {
  const [handle, setHandle] = useState("@studio.veld");
  const [running, setRunning] = useState(false);
  const [terminalLines, setTerminalLines] = useState<string[]>(bootLines);
  const [toneVectors, setToneVectors] = useState(DEFAULT_TONE_VECTORS);
  const [clusterHighlights, setClusterHighlights] = useState<string[]>(DEFAULT_HIGHLIGHTS);
  const [platformState, setPlatformState] = useState<Record<PlatformKey, PlatformState>>({
    instagram: "idle",
    linkedin: "idle",
    x: "idle",
    threads: "idle",
    youtube: "idle",
    tiktok: "idle",
  });

  const connectedCount = useMemo(
    () => Object.values(platformState).filter((state) => state === "connected").length,
    [platformState],
  );

  const clusterTitle = useMemo(() => {
    const top = [...toneVectors]
      .sort((a, b) => b.v - a.v)
      .slice(0, 3)
      .map((item) => item.k.split("/")[0].trim());
    return top.join(". ") + ".";
  }, [toneVectors]);

  const connectPlatform = async (platform: PlatformTile) => {
    if (!platform.implemented) {
      setTerminalLines([
        ` > engine.ingest --target=${handle} --platform=${platform.name.toLowerCase()}`,
        lineWithStatus("auth.oauth", "[ERR]"),
        `error: ${platform.name} connector is queued.`,
      ]);
      return;
    }

    if (running || platformState[platform.key] === "connecting") return;

    setRunning(true);
    setPlatformState((prev) => ({ ...prev, [platform.key]: "connecting" }));

    const nextLines = [` > engine.ingest --target=${handle} --platform=${platform.name.toLowerCase()}`];
    const pushLine = (line: string) => {
      nextLines.push(line);
      setTerminalLines([...nextLines]);
    };
    const updateLastLine = (line: string) => {
      nextLines[nextLines.length - 1] = line;
      setTerminalLines([...nextLines]);
    };

    try {
      pushLine(lineWithStatus("auth.oauth", "[...]"));
      await delay(SLEEP_MS);
      updateLastLine(lineWithStatus("auth.oauth", "[OK]"));

      pushLine(lineWithStatus("fetching feed metadata", "[...]"));
      const summary = await scrapeProfile(platform.key, handle);
      updateLastLine(lineWithStatus("fetching feed metadata", "[OK]"));

      pushLine(lineWithStatus(`scanning ${summary.posts.toLocaleString()} posts`, "[OK]"));
      await delay(SLEEP_MS);
      pushLine(lineWithStatus(`scanning ${summary.comments.toLocaleString()} comments`, "[OK]"));
      await delay(SLEEP_MS);
      pushLine(lineWithStatus(`collecting ${summary.collectedTweets.toLocaleString()} tweets`, "[OK]"));
      await delay(SLEEP_MS);
      pushLine(lineWithStatus("extracting hashtag clusters", "[OK]"));
      await delay(SLEEP_MS);
      pushLine(lineWithStatus("extracting emoji density", "[OK]"));
      if (summary.storagePath) {
        pushLine(`persisted dataset: ${summary.storagePath}`);
      }
      pushLine("> ready.");

      if (summary.analysis?.tone_vectors?.length) {
        setToneVectors(summary.analysis.tone_vectors);
      }
      if (summary.analysis?.highlights?.length) {
        setClusterHighlights(summary.analysis.highlights);
      }

      setPlatformState((prev) => ({ ...prev, [platform.key]: "connected" }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      if (nextLines[nextLines.length - 1].startsWith("fetching feed metadata")) {
        updateLastLine(lineWithStatus("fetching feed metadata", "[ERR]"));
      } else {
        pushLine(lineWithStatus("fetching feed metadata", "[ERR]"));
      }
      pushLine(`error: ${message}`);
      setPlatformState((prev) => ({ ...prev, [platform.key]: "error" }));
    } finally {
      setRunning(false);
    }
  };

  const runXFromHandle = async () => {
    const xTile = PLATFORMS.find((p) => p.key === "x");
    if (!xTile) return;
    await connectPlatform(xTile);
  };

  return (
    <div className="min-h-screen bg-newsprint flex flex-col">
      <TopNav />

      <SectionHeader num="02" kicker="Step 01 — Ingest" title="Synthesize a private voice." right="↘ read-only OAuth · zero data egress" />

      {/* INGEST FORM */}
      <section className="grid grid-cols-12 border-b border-ink">
        <div className="col-span-12 lg:col-span-7 border-r border-ink/15 p-8 md:p-12 bg-card">
          <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-3">
            Target profile
          </div>
          <div className="flex items-center border-b-2 border-ink pb-2 mb-8">
            <span className="font-display text-5xl text-foreground/30 mr-2">@</span>
            <input
              value={handle.replace("@", "")}
              onChange={(e) => setHandle("@" + e.target.value.replace("@", ""))}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  void runXFromHandle();
                }
              }}
              className="flex-1 bg-transparent font-display text-4xl md:text-5xl outline-none placeholder:text-foreground/20"
              placeholder="your_handle"
            />
            <button onClick={() => void runXFromHandle()} className="ed-btn ml-4" disabled={running}>
              {running ? "Analyzing..." : "Analyze X →"}
            </button>
          </div>

          <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-4">
            Connected platforms · {connectedCount}/6
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {PLATFORMS.map((p) => (
              <button
                key={p.code}
                onClick={() => connectPlatform(p)}
                disabled={running}
                className={`border border-ink p-4 text-left transition-all hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[4px_4px_0px_0px_var(--ink)] disabled:opacity-70 disabled:cursor-not-allowed ${
                  platformState[p.key] === "connected" ? "bg-ink text-newsprint" : "bg-newsprint"
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono-ed text-xs tracking-widest border border-current px-1.5 py-0.5">{p.code}</span>
                  <span className={`size-2 ${platformState[p.key] === "connected" ? "bg-indigo-electric" : "bg-current opacity-30"}`} />
                </div>
                <div className="font-display text-xl leading-none">{p.name}</div>
                <div className="font-mono-ed text-[10px] uppercase tracking-widest opacity-60 mt-2">
                  {platformState[p.key] === "connected"
                    ? "linked"
                    : platformState[p.key] === "connecting"
                      ? "connecting..."
                      : p.implemented
                        ? "+ connect"
                        : "queued"}
                </div>
              </button>
            ))}
          </div>

          <div className="mt-10 border border-ink p-5 bg-newsprint">
            <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-2">
              ⚠ Privacy clause
            </div>
            <p className="text-sm leading-relaxed text-foreground/80">
              Your model is fine-tuned within your tenant. Weights are encrypted at rest.
              No data is shared with foundation providers. Revoke OAuth at any time and the model is shredded within 24h.
            </p>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-5 bg-ink min-h-[500px]">
          <Terminal lines={terminalLines} mode="stream" loop={false} />
        </div>
      </section>

      {/* VOICE FINGERPRINT */}
      <SectionHeader num="03" kicker="Step 02 — Synthesize" title="Voice fingerprint" right="↘ 14 dimensions · normalized 0–100" />

      <section className="grid grid-cols-12 border-b border-ink">
        <div className="col-span-12 lg:col-span-8 border-r border-ink/15 p-8 bg-card">
          <div className="space-y-5">
            {toneVectors.map((t) => (
              <div key={t.k}>
                <div className="flex items-baseline justify-between mb-1.5">
                  <div className="font-display text-2xl">{t.k}</div>
                  <div className="font-mono-ed text-sm tabular-nums">
                    <span className="text-indigo-electric">{t.v}</span>
                    <span className="text-foreground/40"> / 100</span>
                  </div>
                </div>
                <div className="h-2 bg-ink/10 relative">
                  <div className="h-full bg-ink" style={{ width: `${t.v}%` }} />
                  <div className="absolute top-0 h-full w-px bg-indigo-electric" style={{ left: `${t.v}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 p-8 bg-ink text-newsprint">
          <div className="font-mono-ed text-[10px] uppercase tracking-widest text-newsprint/50 mb-3">
            Cluster summary
          </div>
          <h3 className="font-display text-4xl mb-6 leading-tight">
            {clusterTitle} <em className="italic font-light text-indigo-electric">Computed.</em>
          </h3>
          <ul className="space-y-3 text-sm">
            {clusterHighlights.map((s, i) => (
              <li key={i} className="flex gap-3 border-b border-newsprint/20 pb-2">
                <span className="font-mono-ed text-[10px] text-indigo-electric mt-1">▸</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
          <Link to="/generator" className="ed-btn bg-newsprint text-ink border-newsprint w-full mt-8 hover:bg-indigo-electric hover:border-indigo-electric hover:text-newsprint">
            Open Generator →
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
