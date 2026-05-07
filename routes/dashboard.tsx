import { createFileRoute, Link } from "@tanstack/react-router";
import { TopNav } from "../components/TopNav";
import { Footer } from "../components/Footer";
import { Counter } from "../components/Counter";
import { SectionHeader } from "../components/SectionHeader";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard · Press/Engine" },
      { name: "description", content: "Your editorial control room. Engine status, voice match, queue, performance." },
    ],
  }),
  component: Dashboard,
});

const QUEUE = [
  { time: "09:00", platform: "IG", title: "the camera doesn't lie. it just edits the truth.", status: "queued" },
  { time: "12:30", platform: "X", title: "shipped a redesign. nobody noticed. highest compliment.", status: "queued" },
  { time: "15:00", platform: "LI", title: "Hot take: most design systems are style guides with anxiety.", status: "draft" },
  { time: "18:45", platform: "TT", title: "30s carousel — process behind the spring shoot.", status: "approved" },
  { time: "20:00", platform: "TH", title: "lowercase notes from a tuesday studio.", status: "queued" },
];

const SPARK = [4, 7, 5, 9, 12, 8, 14, 11, 17, 13, 19, 16, 22, 20, 26, 24, 31, 28, 35, 33, 41, 38, 47, 44];

function Dashboard() {
  const max = Math.max(...SPARK);
  return (
    <div className="min-h-screen bg-newsprint flex flex-col">
      <TopNav />

      <SectionHeader num="01" kicker="Control Room" title="Editorial Dashboard" right="↘ live · auto-refresh 30s" />

      {/* TOP BENTO */}
      <section className="grid grid-cols-12 border-b border-ink">
        {/* Voice match large */}
        <div className="col-span-12 lg:col-span-5 border-r border-ink/15 p-8 bg-card relative overflow-hidden">
          <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-4">
            Voice Match Index · 7-day rolling
          </div>
          <div className="font-display text-[10rem] md:text-[12rem] leading-[0.85] tracking-tighter">
            <Counter to={96.4} decimals={1} suffix="%" />
          </div>
          <div className="mt-2 flex items-center gap-2 font-mono-ed text-xs">
            <span className="text-indigo-electric">▲ +2.1</span>
            <span className="text-foreground/50 uppercase tracking-widest">vs prior week</span>
          </div>
          <div className="absolute top-4 right-4 size-3 bg-indigo-electric animate-pulse" />
        </div>

        {/* Right column metrics */}
        <div className="col-span-12 lg:col-span-7 grid grid-cols-2">
          {[
            { k: "Posts published", v: 247, sub: "this month" },
            { k: "Hours reclaimed", v: 31, suf: "h", sub: "vs manual" },
            { k: "Avg engagement", v: 4.7, suf: "%", d: 1, sub: "median across feeds" },
            { k: "Drafts in queue", v: 18, sub: "next 14 days" },
          ].map((m, i) => (
            <div key={m.k} className={`p-6 ${i % 2 === 0 ? "border-r border-ink/15" : ""} ${i < 2 ? "border-b border-ink/15" : ""}`}>
              <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-2">{m.k}</div>
              <div className="font-display text-5xl leading-none">
                <Counter to={m.v} suffix={m.suf || ""} decimals={m.d || 0} />
              </div>
              <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/40 mt-2">{m.sub}</div>
            </div>
          ))}
        </div>
      </section>

      {/* MID — chart + engine status */}
      <section className="grid grid-cols-12 border-b border-ink">
        <div className="col-span-12 lg:col-span-8 border-r border-ink/15 p-8 bg-card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-1">Output volume · last 24 hours</div>
              <h3 className="font-display text-3xl">Press throughput<span className="italic font-light text-indigo-electric">.</span></h3>
            </div>
            <div className="flex gap-1.5">
              {["24H", "7D", "30D", "ALL"].map((p, i) => (
                <button key={p} className={`font-mono-ed text-[10px] tracking-widest px-2.5 py-1 border border-ink ${i === 0 ? "bg-ink text-newsprint" : "hover:bg-ink hover:text-newsprint"}`}>{p}</button>
              ))}
            </div>
          </div>

          <div className="flex items-end gap-1 h-48 border-b border-ink/30">
            {SPARK.map((v, i) => (
              <div key={i} className="flex-1 flex flex-col justify-end group">
                <div className="bg-ink hover:bg-indigo-electric transition-colors" style={{ height: `${(v / max) * 100}%` }} />
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-3 font-mono-ed text-[10px] uppercase tracking-widest text-foreground/40">
            <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>23:59</span>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 p-8 bg-ink text-newsprint relative scan-line">
          <div className="font-mono-ed text-[10px] uppercase tracking-widest text-newsprint/50 mb-4">
            Engine Status
          </div>
          <h3 className="font-display text-3xl mb-6">Online<span className="italic font-light text-indigo-electric">.</span></h3>
          <ul className="space-y-3 font-mono-ed text-xs">
            {[
              { k: "Model version", v: "lora-v3.027" },
              { k: "Tenant", v: "studio-veld" },
              { k: "GPU pool", v: "h100 / 2 nodes" },
              { k: "Queue depth", v: "00:00:02" },
              { k: "Last train", v: "14h ago" },
              { k: "Uptime", v: "99.998%" },
            ].map((r) => (
              <li key={r.k} className="flex justify-between border-b border-newsprint/20 pb-2">
                <span className="text-newsprint/60 uppercase tracking-widest">{r.k}</span>
                <span className="text-indigo-electric">{r.v}</span>
              </li>
            ))}
          </ul>
          <Link to="/analyzer" className="ed-btn bg-newsprint text-ink border-newsprint w-full mt-6 hover:bg-indigo-electric hover:border-indigo-electric hover:text-newsprint">
            Retrain model →
          </Link>
        </div>
      </section>

      {/* QUEUE */}
      <section className="border-b border-ink">
        <div className="grid grid-cols-12 border-b border-ink/15 bg-card">
          <div className="col-span-6 p-5 border-r border-ink/15">
            <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-1">Today's Queue</div>
            <h3 className="font-display text-3xl">5 dispatches scheduled<span className="italic font-light text-indigo-electric">.</span></h3>
          </div>
          <div className="col-span-6 p-5 flex items-center justify-end gap-2">
            <Link to="/scheduler" className="ed-btn ed-btn-ghost h-10 text-xs">Open Scheduler</Link>
            <Link to="/generator" className="ed-btn h-10 text-xs">+ New Draft</Link>
          </div>
        </div>

        {QUEUE.map((q, i) => (
          <div key={i} className="grid grid-cols-12 border-b border-ink/15 last:border-b-0 hover:bg-ink hover:text-newsprint transition-colors group">
            <div className="col-span-2 md:col-span-1 border-r border-ink/15 group-hover:border-newsprint/20 p-4 font-mono-ed text-xs flex items-center">
              {q.time}
            </div>
            <div className="col-span-2 md:col-span-1 border-r border-ink/15 group-hover:border-newsprint/20 p-4 font-mono-ed text-[11px] tracking-widest flex items-center">
              {q.platform}
            </div>
            <div className="col-span-8 md:col-span-7 border-r border-ink/15 group-hover:border-newsprint/20 p-4 font-display text-lg md:text-xl leading-snug">
              {q.title}
            </div>
            <div className="col-span-12 md:col-span-3 p-4 flex items-center justify-between gap-2">
              <span className={`ed-tag group-hover:border-newsprint ${q.status === "approved" ? "bg-indigo-electric text-newsprint border-indigo-electric" : ""}`}>
                ◉ {q.status}
              </span>
              <button className="font-mono-ed text-[10px] uppercase tracking-widest underline underline-offset-4">edit →</button>
            </div>
          </div>
        ))}
      </section>

      <Footer />
    </div>
  );
}
