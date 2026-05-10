import { createFileRoute, Link } from "@tanstack/react-router";
import { TopNav } from "../components/TopNav";
import { Footer } from "../components/Footer";
import { SectionHeader } from "../components/SectionHeader";

export const Route = createFileRoute("/manifesto")({
  head: () => ({
    meta: [
      { title: "Manifesto · Press/Engine" },
      { name: "description", content: "Why we built an algorithmic press for serious creators." },
    ],
  }),
  component: Manifesto,
});

const TENETS = [
  { n: "I", t: "The voice belongs to the maker.", d: "Foundation models flatten. Private models elevate. Your model trains on you and only you, ever." },
  { n: "II", t: "Automation should elevate craft.", d: "We do not generate slop. We compose drafts at the dial of a knob and submit them to the maker for final cut." },
  { n: "III", t: "Privacy is a feature, not a footnote.", d: "Read-only OAuth. Encrypted weights. 24-hour shred on revocation. The engine is a tenant, not a tenant farm." },
  { n: "IV", t: "Density over decoration.", d: "We reject soft gradients and friendly mascots. The interface is a printing press. Mechanical, exposed, honest." },
  { n: "V", t: "The tool is an instrument.", d: "Linear keyboard. Space Grotesk labels. JetBrains Mono telemetry. Every pixel earns its place." },
  { n: "VI", t: "The press fires on cadence.", d: "Consistency, not virality, builds equity. The engine ships every day so you can think for the long arc." },
];

function Manifesto() {
  return (
    <div className="min-h-screen bg-newsprint flex flex-col">
      <TopNav />

      {/* HERO BLACK */}
      <section className="bg-ink text-newsprint border-b border-ink p-8 md:p-16 relative overflow-hidden">
        <div className="absolute inset-0 grid-rule opacity-15" />
        <div className="relative max-w-6xl">
          <div className="font-mono-ed text-[10px] uppercase tracking-widest text-newsprint/50 mb-6">
            ◉ Manifesto · published april 2026 · authored by the press
          </div>
          <h1 className="font-display text-[15vw] md:text-[10rem] leading-[0.85] tracking-tighter mb-8">
            Against the <em className="italic font-light text-indigo-electric">slop</em>.
          </h1>
          <p className="font-display text-2xl md:text-4xl leading-snug max-w-4xl text-newsprint/85">
            Most AI tools optimize for output. We optimize for <em className="italic">voice</em>.
            Most platforms farm your data. We encrypt yours. Most interfaces beg for a click.
            This one demands an opinion.
          </p>
        </div>
      </section>

      <SectionHeader num="05" kicker="The Tenets" title="Six positions, no apologies." right="↘ read end-to-end · 4 min" />

      {/* TENETS */}
      <section className="grid grid-cols-12 border-b border-ink">
        {TENETS.map((t, i) => (
          <article
            key={t.n}
            className={`col-span-12 md:col-span-6 ${i % 2 === 0 ? "md:border-r border-ink/15" : ""} border-b border-ink/15 p-8 md:p-12 group hover:bg-ink hover:text-newsprint transition-colors duration-300 relative`}
          >
            <div className="font-display text-[8rem] md:text-[10rem] leading-none italic font-light text-foreground/15 group-hover:text-newsprint/15 absolute top-4 right-6 pointer-events-none">
              {t.n}
            </div>
            <div className="relative">
              <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 group-hover:text-newsprint/50 mb-4">
                Tenet · {t.n}
              </div>
              <h3 className="font-display text-3xl md:text-4xl leading-tight mb-4 max-w-md">
                {t.t}
              </h3>
              <p className="text-base leading-relaxed text-foreground/80 group-hover:text-newsprint/85 max-w-md">
                {t.d}
              </p>
            </div>
          </article>
        ))}
      </section>

      {/* COLOPHON-STYLE SIGN-OFF */}
      <section className="grid grid-cols-12 border-b border-ink bg-card">
        <div className="col-span-12 md:col-span-7 border-r border-ink/15 p-8 md:p-12">
          <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-6">
            Closing argument
          </div>
          <p className="font-display text-3xl md:text-5xl leading-[1.05]">
            If you wanted average, the internet already obliged.
            <br/>
            <span className="italic font-light text-indigo-electric">Press/Engine</span> is for the rest of us.
          </p>
        </div>
        <div className="col-span-12 md:col-span-5 p-8 md:p-12 flex flex-col justify-end gap-6">
          <div>
            <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-2">Authored</div>
            <div className="font-display text-2xl">The Press, Stockholm</div>
          </div>
          <div>
            <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-2">Set in</div>
            <div className="font-display text-2xl">Newsreader · Space Grotesk · JetBrains Mono</div>
          </div>
          <div className="flex gap-3 mt-4">
            <Link to="/analyzer" className="ed-btn">Begin →</Link>
            <Link to="/" className="ed-btn ed-btn-ghost">Back to index</Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
