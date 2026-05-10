export function Footer() {
  return (
    <footer className="mt-auto grid grid-cols-12 border-t border-ink bg-card">
      <div className="col-span-12 md:col-span-7 border-b md:border-b-0 md:border-r border-ink/15 p-6">
        <div className="font-display text-3xl leading-none">
          Press/Engine<span className="italic font-light text-indigo-electric">.</span>
        </div>
      </div>
      <div className="col-span-12 md:col-span-5 p-6 font-mono-ed text-[10px] uppercase tracking-widest text-foreground/55">
        Private voice systems / editorial automation / model-assisted publishing
      </div>
    </footer>
  );
}
