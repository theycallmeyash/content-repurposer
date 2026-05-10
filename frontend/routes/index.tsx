import { createFileRoute, Link } from "@tanstack/react-router";
import { TopNav } from "../components/TopNav";
import { Footer } from "../components/Footer";
import { Terminal } from "../components/Terminal";
import { Counter } from "../components/Counter";
import { SectionHeader } from "../components/SectionHeader";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Press/Engine — Automate the aesthetic" },
      { name: "description", content: "Ingest your social profiles. Train a private model. Publish on-brand content with mechanical precision." },
      { property: "og:title", content: "Press/Engine — Automate the aesthetic" },
      { property: "og:description", content: "An algorithmic editorial engine for serious creators." },
    ],
  }),
  component: Index,
});

const HERO_LINES = [
  "> engine.boot --target=@your_handle",
  "loading kernel ............... [OK]",
  "auth.session ................. [OK]",
  "> engine.ingest --platform=instagram",
  "scanning 1,247 posts ......... [OK]",
  "extracting tone vectors ...... [OK]",
  "mapping aesthetic clusters ... [OK]",
  "> engine.synthesize",
  "tone:        sharp / dry / 78%",
  "cadence:     short-form / 14s",
  "palette:     mono / film grain",
  "themes:      craft, ritual, urban",
  "> engine.compose --n=5",
  "draft 01 ..................... [OK]",
  "draft 02 ..................... [OK]",
  "draft 03 ..................... [OK]",
  "ready to publish.",
];

const PLATFORMS = [
  { name: "Instagram", code: "IG", followers: "127K" },
  { name: "TikTok", code: "TT", followers: "84K" },
  { name: "X / Twitter", code: "XX", followers: "212K" },
  { name: "LinkedIn", code: "LI", followers: "31K" },
  { name: "Threads", code: "TH", followers: "19K" },
  { name: "YouTube", code: "YT", followers: "8.2K" },
];

function Index() {
  return (
    <div className="min-h-screen bg-newsprint flex flex-col">
      <TopNav />

      {/* HERO — split asymmetric */}
      <section className="grid grid-cols-12 border-b border-ink">
        <div className="col-span-12 lg:col-span-7 border-r border-ink/15 relative overflow-hidden">
          <div className="absolute inset-0 grid-rule pointer-events-none opacity-60" />
          <div className="relative p-6 md:p-12 lg:p-16">
            <div className="flex items-center gap-3 mb-8 anim-snap-in">
              <span className="ed-tag">▸ Vol. III · 2026</span>
              <span className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50">
                Issue 027 — The Algorithmic Editor
              </span>
            </div>

            <h1 className="font-display text-[14vw] lg:text-[10rem] leading-[0.85] tracking-tighter">
              <span className="block anim-mask-up" style={{ animationDelay: "0.1s" }}>Automate</span>
              <span className="block italic font-light text-foreground/90 anim-mask-up" style={{ animationDelay: "0.25s" }}>the</span>
              <span className="block anim-mask-up" style={{ animationDelay: "0.4s" }}>
                aesthetic<span className="text-indigo-electric">.</span>
              </span>
            </h1>

            <div className="mt-12 grid grid-cols-12 gap-6 max-w-3xl">
              <p className="col-span-12 md:col-span-7 font-display text-xl md:text-2xl leading-snug text-foreground/85">
                A private model trained on <em className="italic">your</em> voice. A press that publishes
                while you sleep. The end of generic content.
              </p>
              <div className="col-span-12 md:col-span-5 font-mono-ed text-[11px] uppercase tracking-widest text-foreground/55 leading-[1.7]">
                <div className="border-l border-ink pl-3">
                  Ingest. <br/> Synthesize. <br/> Schedule. <br/> Publish.
                </div>
              </div>
            </div>

            <div className="mt-10 flex flex-wrap items-center gap-3">
              <Link to="/analyzer" className="ed-btn">Synthesize Profile →</Link>
              <Link to="/generator" className="ed-btn ed-btn-ghost">Open Generator</Link>
              <span className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/45 ml-2">
                · No card. 14-day press pass.
              </span>
            </div>
          </div>

          {/* metrics strip */}
          <div className="grid grid-cols-3 border-t border-ink/15">
            {[
              { k: "Posts/mo", v: 247, suf: "+", d: 0 },
              { k: "Voice match", v: 96.4, suf: "%", d: 1 },
              { k: "Hours saved", v: 31, suf: "h", d: 0 },
            ].map((m) => (
              <div key={m.k} className="border-r border-ink/15 last:border-r-0 p-5">
                <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-1">
                  {m.k}
                </div>
                <div className="font-display text-3xl md:text-4xl leading-none">
                  <Counter to={m.v} suffix={m.suf} decimals={m.d} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-5 bg-ink anim-snap-in" style={{ animationDelay: "0.55s" }}>
          <Terminal lines={HERO_LINES} loop />
        </div>
      </section>

      {/* PLATFORM MARQUEE */}
      <section className="border-b border-ink overflow-hidden bg-card">
        <div className="flex items-center gap-12 py-5 marquee whitespace-nowrap">
          {[...PLATFORMS, ...PLATFORMS, ...PLATFORMS].map((p, i) => (
            <div key={i} className="flex items-center gap-3 px-4">
              <span className="font-mono-ed text-[10px] tracking-widest border border-ink px-2 py-0.5">{p.code}</span>
              <span className="font-display text-2xl">{p.name}</span>
              <span className="font-mono-ed text-[10px] text-foreground/40">/ {p.followers}</span>
              <span className="text-ink/30 text-2xl">·</span>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS — bento */}
      <SectionHeader num="01" kicker="The Process" title="From profile to press in four motions." right="↘ four steps · zero excuses" />

      <section className="grid grid-cols-12 border-b border-ink">
        {[
          { n: "01", t: "Ingest", d: "Connect any social handle. The engine reads every post, comment, caption, and DM you authorize — building a 14-dimensional voice fingerprint.", tag: "READ-ONLY OAUTH" },
          { n: "02", t: "Synthesize", d: "A private LoRA is fine-tuned on your fingerprint. No data leaves your tenant. No model is shared. Your voice is yours.", tag: "PRIVATE MODEL" },
          { n: "03", t: "Compose", d: "The Generator drafts on-brand posts at the dial of a knob. Tune snark, brevity, professionalism. Reshuffle the press.", tag: "TONE-CALIBRATED" },
          { n: "04", t: "Publish", d: "Schedule across platforms in a single calendar. The press fires on cadence. You approve, edit, or let it run autopilot.", tag: "AUTOPILOT READY" },
        ].map((s, i) => (
          <article key={s.n} className={`col-span-12 md:col-span-6 lg:col-span-3 ${i < 3 ? "border-r border-ink/15" : ""} border-b md:border-b-0 border-ink/15 p-6 md:p-8 group hover:bg-ink hover:text-newsprint transition-colors duration-300`}>
            <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 group-hover:text-newsprint/50 mb-4">
              § {s.n} / {s.tag}
            </div>
            <h3 className="font-display text-5xl mb-4 leading-none">{s.t}<span className="italic font-light text-indigo-electric">.</span></h3>
            <p className="text-sm leading-relaxed text-foreground/75 group-hover:text-newsprint/85">
              {s.d}
            </p>
            <div className="mt-6 inline-block font-mono-ed text-[10px] uppercase tracking-widest border-b border-ink group-hover:border-newsprint pb-0.5">
              read more →
            </div>
          </article>
        ))}
      </section>

      {/* EDITORIAL FEATURE — split with quote */}
      <section className="grid grid-cols-12 border-b border-ink">
        <div className="col-span-12 lg:col-span-5 border-r border-ink/15 p-8 md:p-12 bg-card">
          <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-6">
            FEATURE · 03.4 · GENERATOR
          </div>
          <h2 className="font-display text-5xl md:text-6xl leading-[0.9] mb-6">
            A printing press <em className="italic font-light">disguised</em> as software.
          </h2>
          <p className="text-base leading-relaxed text-foreground/80 mb-8">
            Most AI tools generate slop. We built an instrument. Tone dials are physical.
            Drafts snap into place like cut paper. Every output carries your fingerprint —
            because the model trained on you and only you.
          </p>
          <div className="border-l-2 border-indigo-electric pl-5 py-2">
            <p className="font-display text-2xl italic leading-tight">
              "The first AI tool that doesn't make my brand sound like a chatbot."
            </p>
            <p className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/55 mt-3">
              — M. Halberstam, Creative Director · Studio Veld
            </p>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-7 p-8 md:p-12 bg-ink text-newsprint relative">
          <div className="absolute inset-0 grid-rule opacity-20" />
          <div className="relative">
            <div className="font-mono-ed text-[10px] uppercase tracking-widest text-newsprint/50 mb-6">
              SAMPLE OUTPUT · TONE: SHARP / DRY · LENGTH: SHORT
            </div>
            <div className="space-y-5">
              {[
                { k: "DRAFT 01 / IG", t: "the camera doesn't lie. it just edits the truth." },
                { k: "DRAFT 02 / X", t: "shipped a redesign. nobody noticed. that's the highest compliment a brand can receive." },
                { k: "DRAFT 03 / LI", t: "Hot take: most 'design systems' are just style guides with anxiety." },
              ].map((d, i) => (
                <div key={i} className="border border-newsprint/30 p-5 hover:border-indigo-electric transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono-ed text-[10px] tracking-widest text-newsprint/50">{d.k}</span>
                    <div className="flex gap-2">
                      <button className="font-mono-ed text-[10px] uppercase tracking-widest hover:text-indigo-electric">edit</button>
                      <button className="font-mono-ed text-[10px] uppercase tracking-widest hover:text-indigo-electric">queue →</button>
                    </div>
                  </div>
                  <p className="font-display text-xl md:text-2xl leading-snug">{d.t}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* PRICING / CTA */}
      <SectionHeader num="02" kicker="The Subscription" title="Three presses. One engine." right="↘ all plans · cancel anytime" />

      <section className="grid grid-cols-12 border-b border-ink">
        {[
          { name: "Apprentice", price: "0", per: "/mo", desc: "Connect one profile. 30 drafts/month.", cta: "Start free", primary: false },
          { name: "Editor", price: "49", per: "/mo", desc: "Three profiles. Unlimited drafts. Tone dials. Scheduler.", cta: "Begin subscription", primary: true },
          { name: "Atelier", price: "Custom", per: "", desc: "Team seats. Brand guardrails. Priority press. SSO.", cta: "Contact sales", primary: false },
        ].map((p, i) => (
          <div key={p.name} className={`col-span-12 md:col-span-4 ${i < 2 ? "border-r border-ink/15" : ""} p-8 ${p.primary ? "bg-ink text-newsprint" : "bg-card"} relative`}>
            {p.primary && (
              <div className="absolute top-0 right-0 bg-indigo-electric text-newsprint font-mono-ed text-[10px] uppercase tracking-widest px-3 py-1">
                Most adopted
              </div>
            )}
            <div className="font-mono-ed text-[10px] uppercase tracking-widest opacity-60 mb-4">PLAN · 0{i + 1}</div>
            <h3 className="font-display text-4xl mb-2">{p.name}</h3>
            <div className="flex items-baseline gap-1 mb-6">
              <span className="font-display text-7xl leading-none">{p.price === "Custom" ? "—" : `$${p.price}`}</span>
              <span className="font-mono-ed text-xs opacity-60">{p.per || "by quote"}</span>
            </div>
            <p className="text-sm leading-relaxed mb-8 opacity-85">{p.desc}</p>
            <button className={p.primary ? "ed-btn bg-newsprint text-ink border-newsprint w-full hover:bg-indigo-electric hover:border-indigo-electric hover:text-newsprint" : "ed-btn ed-btn-ghost w-full"}>
              {p.cta} →
            </button>
          </div>
        ))}
      </section>

      {/* FINAL CTA */}
      <section className="border-b border-ink p-8 md:p-16 text-center bg-card">
        <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-4">
          Ready when you are.
        </div>
        <h2 className="font-display text-5xl md:text-8xl leading-[0.9] tracking-tighter mb-8">
          Stop posting. <span className="italic font-light">Start</span> publishing<span className="text-indigo-electric">.</span>
        </h2>
        <Link to="/analyzer" className="ed-btn">Synthesize my profile →</Link>
      </section>

      <Footer />
    </div>
  );
}
