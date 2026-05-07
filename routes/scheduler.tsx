import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { TopNav } from "../components/TopNav";
import { Footer } from "../components/Footer";
import { SectionHeader } from "../components/SectionHeader";

export const Route = createFileRoute("/scheduler")({
  head: () => ({
    meta: [
      { title: "Scheduler · Press/Engine" },
      { name: "description", content: "Calendar control. Send drafts to press across platforms in a single timeline." },
    ],
  }),
  component: Scheduler,
});

const DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"];

type Slot = { day: number; hour: number; platform: string; title: string; status: "queued" | "approved" | "draft" };

const SLOTS: Slot[] = [
  { day: 0, hour: 9, platform: "IG", title: "monochrome moodboard", status: "approved" },
  { day: 0, hour: 14, platform: "X", title: "shipped a redesign…", status: "queued" },
  { day: 1, hour: 8, platform: "LI", title: "Three principles for restraint", status: "queued" },
  { day: 1, hour: 19, platform: "TH", title: "tuesday notes", status: "draft" },
  { day: 2, hour: 11, platform: "TT", title: "spring shoot BTS · 30s", status: "approved" },
  { day: 2, hour: 16, platform: "IG", title: "carousel · type as material", status: "queued" },
  { day: 3, hour: 9, platform: "X", title: "white space is expensive", status: "queued" },
  { day: 4, hour: 12, platform: "LI", title: "case study: brand refresh", status: "approved" },
  { day: 4, hour: 18, platform: "IG", title: "weekend reading", status: "draft" },
  { day: 5, hour: 10, platform: "TH", title: "saturday studio", status: "queued" },
  { day: 6, hour: 20, platform: "X", title: "sunday hot take", status: "draft" },
];

const HOURS = [6, 9, 12, 15, 18, 21];

function Scheduler() {
  const [view, setView] = useState<"week" | "list">("week");

  return (
    <div className="min-h-screen bg-newsprint flex flex-col">
      <TopNav />

      <SectionHeader num="04" kicker="Step 04 — Publish" title="The Scheduler" right="↘ wk 17 · apr 27 — may 03 · 2026" />

      {/* TOOLBAR */}
      <section className="grid grid-cols-12 border-b border-ink bg-card">
        <div className="col-span-12 md:col-span-4 border-r border-ink/15 p-5 flex items-center gap-3">
          <button className="ed-btn ed-btn-ghost h-10 px-3 text-xs">← prev</button>
          <div className="font-display text-2xl">April 2026</div>
          <button className="ed-btn ed-btn-ghost h-10 px-3 text-xs">next →</button>
        </div>
        <div className="col-span-12 md:col-span-4 border-r border-ink/15 p-5 flex items-center justify-center gap-2">
          {(["week", "list"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`font-mono-ed text-xs uppercase tracking-widest px-3 py-1.5 border border-ink ${view === v ? "bg-ink text-newsprint" : "hover:bg-ink hover:text-newsprint"}`}
            >
              {v}
            </button>
          ))}
        </div>
        <div className="col-span-12 md:col-span-4 p-5 flex items-center justify-end gap-2">
          <span className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50">
            autopilot
          </span>
          <button className="relative w-12 h-6 border border-ink bg-indigo-electric">
            <span className="absolute top-0 right-0 size-6 bg-ink" />
          </button>
          <button className="ed-btn h-10 px-4 text-xs">+ Add slot</button>
        </div>
      </section>

      {view === "week" ? (
        <section className="border-b border-ink overflow-x-auto">
          <div className="grid grid-cols-[80px_repeat(7,minmax(140px,1fr))] min-w-[900px]">
            {/* header row */}
            <div className="border-b border-r border-ink/15 bg-ink text-newsprint p-3 font-mono-ed text-[10px] uppercase tracking-widest">
              UTC
            </div>
            {DAYS.map((d, i) => (
              <div key={d} className={`border-b border-ink/15 ${i < 6 ? "border-r" : ""} bg-ink text-newsprint p-3`}>
                <div className="font-mono-ed text-[10px] uppercase tracking-widest text-newsprint/50">{d}</div>
                <div className="font-display text-2xl">{27 + i > 30 ? 27 + i - 30 : 27 + i}</div>
              </div>
            ))}

            {/* time rows */}
            {HOURS.map((h, hi) => (
              <>
                <div key={`h-${h}`} className={`border-r border-ink/15 ${hi < HOURS.length - 1 ? "border-b" : ""} p-3 font-mono-ed text-xs text-foreground/60 bg-card`}>
                  {h.toString().padStart(2, "0")}:00
                </div>
                {DAYS.map((_, di) => {
                  const slot = SLOTS.find(s => s.day === di && Math.abs(s.hour - h) < 2);
                  return (
                    <div key={`${h}-${di}`} className={`${di < 6 ? "border-r" : ""} ${hi < HOURS.length - 1 ? "border-b" : ""} border-ink/15 p-2 min-h-[100px] hover:bg-secondary/50 transition-colors relative group`}>
                      {slot && (
                        <div className={`border border-ink p-2.5 h-full cursor-grab transition-all hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[3px_3px_0px_0px_var(--ink)] ${
                          slot.status === "approved" ? "bg-ink text-newsprint" :
                          slot.status === "draft" ? "bg-newsprint" : "bg-card"
                        }`}>
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="font-mono-ed text-[9px] tracking-widest border border-current px-1 py-px">{slot.platform}</span>
                            <span className="font-mono-ed text-[9px] opacity-60">{slot.hour.toString().padStart(2,"0")}:00</span>
                          </div>
                          <div className="font-display text-sm leading-tight">{slot.title}</div>
                          {slot.status === "approved" && <div className="mt-1.5 size-1.5 bg-indigo-electric" />}
                        </div>
                      )}
                    </div>
                  );
                })}
              </>
            ))}
          </div>
        </section>
      ) : (
        <section className="border-b border-ink">
          {SLOTS.sort((a,b) => a.day === b.day ? a.hour - b.hour : a.day - b.day).map((s, i) => (
            <div key={i} className="grid grid-cols-12 border-b border-ink/15 last:border-b-0 hover:bg-ink hover:text-newsprint group">
              <div className="col-span-2 md:col-span-1 border-r border-ink/15 group-hover:border-newsprint/20 p-4 font-mono-ed text-xs">{DAYS[s.day]}</div>
              <div className="col-span-2 md:col-span-1 border-r border-ink/15 group-hover:border-newsprint/20 p-4 font-mono-ed text-xs">{s.hour.toString().padStart(2,"0")}:00</div>
              <div className="col-span-2 md:col-span-1 border-r border-ink/15 group-hover:border-newsprint/20 p-4 font-mono-ed text-[11px] tracking-widest">{s.platform}</div>
              <div className="col-span-6 md:col-span-7 border-r border-ink/15 group-hover:border-newsprint/20 p-4 font-display text-xl">{s.title}</div>
              <div className="col-span-12 md:col-span-2 p-4 flex items-center justify-end">
                <span className={`ed-tag group-hover:border-newsprint ${s.status === "approved" ? "bg-indigo-electric text-newsprint border-indigo-electric" : ""}`}>◉ {s.status}</span>
              </div>
            </div>
          ))}
        </section>
      )}

      {/* LEGEND */}
      <section className="grid grid-cols-12 border-b border-ink bg-card">
        <div className="col-span-12 md:col-span-3 border-r border-ink/15 p-5">
          <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-2">Legend</div>
          <div className="flex items-center gap-3 mt-3">
            <span className="size-4 bg-ink" />
            <span className="font-mono-ed text-xs">approved</span>
          </div>
          <div className="flex items-center gap-3 mt-2">
            <span className="size-4 bg-card border border-ink" />
            <span className="font-mono-ed text-xs">queued</span>
          </div>
          <div className="flex items-center gap-3 mt-2">
            <span className="size-4 bg-newsprint border border-dashed border-ink" />
            <span className="font-mono-ed text-xs">draft</span>
          </div>
        </div>
        <div className="col-span-12 md:col-span-9 p-5">
          <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-2">Tip</div>
          <p className="font-display text-2xl leading-snug">
            Drag any slot to reschedule. Hold <kbd className="font-mono-ed text-xs border border-ink px-1.5 py-0.5 mx-1">⌘</kbd> and click to duplicate. The press fires automatically when autopilot is on.
          </p>
        </div>
      </section>

      <Footer />
    </div>
  );
}
