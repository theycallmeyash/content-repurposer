import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { TopNav } from "../components/TopNav";
import { Footer } from "../components/Footer";
import { Dial } from "../components/Dial";
import { SectionHeader } from "../components/SectionHeader";
import { repurposeContent } from "../lib/api";

export const Route = createFileRoute("/generator")({
  head: () => ({
    meta: [
      { title: "Generator · Press/Engine" },
      { name: "description", content: "Tune the dials. Compose drafts. Send to press." },
    ],
  }),
  component: Generator,
});

const PLATFORM_OPTS = ["IG", "X", "LI", "TT", "TH"] as const;
type PlatformOption = (typeof PLATFORM_OPTS)[number] | "ALL";
type Draft = { p: PlatformOption; t: string };

const TEMPLATES = [
  {
    snark: 70,
    brev: 90,
    prof: 30,
    drafts: [
      {
        p: "X",
        t: "shipped a redesign. nobody noticed. that's the highest compliment a brand can receive.",
      },
      { p: "IG", t: "the camera doesn't lie. it just edits the truth." },
      { p: "TH", t: "lowercase notes from a tuesday studio." },
      { p: "X", t: "design opinion: white space is the most expensive material on the page." },
      { p: "IG", t: "a brand isn't a logo. a brand is the silence between the posts." },
    ],
  },
  {
    snark: 30,
    brev: 40,
    prof: 80,
    drafts: [
      {
        p: "LI",
        t: "Three principles guided our latest brand refresh: clarity, rhythm, and restraint. The result is a system that scales without losing intent.",
      },
      {
        p: "LI",
        t: "Hot take: most 'design systems' are style guides with anxiety. The fix is governance, not more components.",
      },
      { p: "X", t: "Reposting because it bears repeating: typography is 95% of brand identity." },
      {
        p: "IG",
        t: "Process notes: from research to release, the spring identity took 11 weeks. Worth every iteration.",
      },
      { p: "LI", t: "What separates senior designers from mid: the willingness to delete." },
    ],
  },
  {
    snark: 90,
    brev: 80,
    prof: 50,
    drafts: [
      { p: "X", t: "your brand guidelines pdf is 84 pages and nobody read past 12." },
      { p: "IG", t: "ai-generated content is the new clip art." },
      { p: "X", t: "minimalism isn't a style. it's a discipline. they are not the same." },
      { p: "TH", t: "saw a font crime today. won't say where." },
      { p: "X", t: "we don't need more tools. we need fewer, sharper opinions." },
    ],
  },
];

function Generator() {
  const [snark, setSnark] = useState(70);
  const [brev, setBrev] = useState(90);
  const [prof, setProf] = useState(30);
  const [warmth, setWarmth] = useState(20);
  const [platform, setPlatform] = useState<PlatformOption>("ALL");
  const [topic, setTopic] = useState("a new brand identity is launching");
  const [provider, setProvider] = useState("gemini_free");
  const [apiKey, setApiKey] = useState("");
  const [trendKeywords, setTrendKeywords] = useState("");
  const [generatedDrafts, setGeneratedDrafts] = useState<Draft[] | null>(null);
  const [summary, setSummary] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");

  // pick the closest template based on dial distance
  const drafts = useMemo(() => {
    if (generatedDrafts) {
      return platform === "ALL"
        ? generatedDrafts
        : generatedDrafts
            .filter((d) => d.p === platform)
            .concat(generatedDrafts)
            .slice(0, 5);
    }

    const dist = TEMPLATES.map(
      (t) => Math.abs(t.snark - snark) + Math.abs(t.brev - brev) + Math.abs(t.prof - prof),
    );
    const idx = dist.indexOf(Math.min(...dist));
    const list = TEMPLATES[idx].drafts;
    return platform === "ALL"
      ? list
      : list
          .filter((d) => d.p === platform)
          .concat(list)
          .slice(0, 5);
  }, [generatedDrafts, snark, brev, prof, platform]);

  const generateDrafts = async () => {
    setError("");
    setIsGenerating(true);

    try {
      const keywords = trendKeywords
        .split(",")
        .map((keyword) => keyword.trim())
        .filter(Boolean);
      const result = await repurposeContent({
        content: topic,
        provider,
        api_key: apiKey || undefined,
        trends: keywords.length ? { platform: "manual", keywords } : undefined,
      });

      const nextDrafts: Draft[] = [
        ...result.twitter_thread.map((tweet) => ({ p: "X" as const, t: tweet })),
        { p: "LI", t: result.linkedin_post },
        { p: "IG", t: result.instagram_caption },
        { p: "TH", t: result.tldr },
      ].filter((draft) => draft.t.trim().length > 0);

      setGeneratedDrafts(nextDrafts);
      setSummary(result.core_analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-newsprint flex flex-col">
      <TopNav />

      <SectionHeader
        num="03"
        kicker="Step 03 — Compose"
        title="The Generator"
        right={`↘ live · ${drafts.length} drafts ready`}
      />

      <section className="grid grid-cols-12 border-b border-ink">
        {/* CONTROLS — left rail */}
        <div className="col-span-12 lg:col-span-4 border-r border-ink/15 bg-card">
          <div className="p-6 border-b border-ink/15">
            <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-2">
              Topic seed
            </div>
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              rows={2}
              className="w-full bg-transparent font-display text-2xl leading-tight outline-none border-b-2 border-ink py-2 resize-none"
            />
          </div>

          <div className="p-6 border-b border-ink/15">
            <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-3">
              Backend model
            </div>
            <div className="grid grid-cols-1 gap-3">
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="border border-ink bg-newsprint px-3 py-2 font-mono-ed text-xs uppercase tracking-widest"
              >
                <option value="gemini_free">Gemini Free</option>
                <option value="gemini">Gemini Pro</option>
                <option value="claude">Claude</option>
                <option value="openai">OpenAI</option>
              </select>
              <input
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                type="password"
                className="border border-ink bg-newsprint px-3 py-2 font-mono-ed text-xs"
                placeholder="API key, or leave blank if backend env is configured"
              />
              <input
                value={trendKeywords}
                onChange={(e) => setTrendKeywords(e.target.value)}
                className="border border-ink bg-newsprint px-3 py-2 font-mono-ed text-xs"
                placeholder="Optional trends: AI agents, launch week"
              />
            </div>
          </div>

          <div className="p-6 border-b border-ink/15">
            <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-3">
              Target platform
            </div>
            <div className="flex flex-wrap gap-2">
              {(["ALL", ...PLATFORM_OPTS] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPlatform(p)}
                  className={`font-mono-ed text-xs tracking-widest px-3 py-1.5 border border-ink ${platform === p ? "bg-ink text-newsprint" : "hover:bg-ink hover:text-newsprint"}`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="p-6 border-b border-ink/15">
            <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-4">
              Tone dials · turn to taste
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Dial label="Snark" value={snark} onChange={setSnark} />
              <Dial label="Brevity" value={brev} onChange={setBrev} />
              <Dial label="Professionalism" value={prof} onChange={setProf} />
              <Dial label="Warmth" value={warmth} onChange={setWarmth} />
            </div>
          </div>

          <div className="p-6">
            <button
              className="ed-btn w-full"
              onClick={() => void generateDrafts()}
              disabled={isGenerating}
            >
              {isGenerating ? "Refracting..." : "▸ Generate with backend"}
            </button>
            {error && (
              <div className="mt-3 border border-ink bg-newsprint p-3 font-mono-ed text-[10px] uppercase tracking-widest text-foreground/70">
                {error}
              </div>
            )}
            <div className="mt-3 font-mono-ed text-[10px] uppercase tracking-widest text-foreground/40 text-center">
              backend · prism api · {generatedDrafts ? "connected" : "ready"}
            </div>
          </div>
        </div>

        {/* DRAFTS — masonry feed */}
        <div className="col-span-12 lg:col-span-8 bg-ink text-newsprint p-6 md:p-8 relative">
          <div className="absolute inset-0 grid-rule opacity-10 pointer-events-none" />
          <div className="relative">
            <div className="flex items-center justify-between mb-6">
              <div className="font-mono-ed text-[10px] uppercase tracking-widest text-newsprint/50">
                Live press · {drafts.length} drafts queued
              </div>
              <div className="flex items-center gap-2 font-mono-ed text-[10px] uppercase tracking-widest text-newsprint/50">
                <span className="size-2 bg-indigo-electric animate-pulse" />
                synthesizing
              </div>
            </div>
            {summary && (
              <div className="mb-5 border border-newsprint/30 p-4 font-mono-ed text-[10px] leading-5 uppercase tracking-widest text-newsprint/65">
                {summary.replace(/\*\*/g, "")}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {drafts.map((d, i) => (
                <article
                  key={`${snark}-${brev}-${prof}-${i}`}
                  className="border border-newsprint/30 p-5 bg-ink hover:border-indigo-electric transition-all anim-snap-in"
                  style={{ animationDelay: `${i * 60}ms`, gridRow: i === 0 ? "span 2" : undefined }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono-ed text-[10px] tracking-widest border border-newsprint/40 px-1.5 py-0.5">
                        DRAFT 0{i + 1}
                      </span>
                      <span className="font-mono-ed text-[10px] tracking-widest text-newsprint/50">
                        / {d.p}
                      </span>
                    </div>
                    <span className="font-mono-ed text-[10px] text-indigo-electric">
                      {(95 + Math.random() * 4).toFixed(1)}%
                    </span>
                  </div>
                  <p
                    className={`font-display leading-snug ${i === 0 ? "text-3xl md:text-4xl" : "text-xl md:text-2xl"}`}
                  >
                    {d.t}
                  </p>
                  <div className="mt-5 flex items-center gap-3 pt-3 border-t border-newsprint/20">
                    <button className="font-mono-ed text-[10px] uppercase tracking-widest hover:text-indigo-electric">
                      ↻ regen
                    </button>
                    <button className="font-mono-ed text-[10px] uppercase tracking-widest hover:text-indigo-electric">
                      ✎ edit
                    </button>
                    <button className="font-mono-ed text-[10px] uppercase tracking-widest hover:text-indigo-electric">
                      ↧ save
                    </button>
                    <button className="ml-auto font-mono-ed text-[10px] uppercase tracking-widest bg-indigo-electric text-newsprint px-3 py-1.5 hover:bg-newsprint hover:text-ink">
                      send to press →
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
