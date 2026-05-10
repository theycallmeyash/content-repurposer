import { Link } from "@tanstack/react-router";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/analyzer", label: "Analyzer" },
  { to: "/generator", label: "Generator" },
  { to: "/scheduler", label: "Scheduler" },
  { to: "/manifesto", label: "Manifesto" },
] as const;

export function TopNav() {
  return (
    <header className="sticky top-0 z-30 border-b border-ink bg-newsprint/95 backdrop-blur">
      <nav className="flex min-h-16 items-center justify-between gap-4 px-4 md:px-8">
        <Link to="/" className="font-display text-2xl leading-none tracking-tight">
          Press/Engine<span className="text-indigo-electric">.</span>
        </Link>
        <div className="flex items-center gap-1 overflow-x-auto">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className="font-mono-ed text-[10px] uppercase tracking-widest px-3 py-2 hover:bg-ink hover:text-newsprint"
              activeProps={{ className: "bg-ink text-newsprint" }}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
