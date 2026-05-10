interface SectionHeaderProps {
  num: string;
  kicker: string;
  title: string;
  right?: string;
}

export function SectionHeader({ num, kicker, title, right }: SectionHeaderProps) {
  return (
    <section className="grid grid-cols-12 border-b border-ink bg-newsprint">
      <div className="col-span-12 md:col-span-2 border-b md:border-b-0 md:border-r border-ink/15 p-5 font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50">
        {num}
      </div>
      <div className="col-span-12 md:col-span-7 border-b md:border-b-0 md:border-r border-ink/15 p-5">
        <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-2">
          {kicker}
        </div>
        <h2 className="font-display text-4xl md:text-6xl leading-none tracking-tight">{title}</h2>
      </div>
      <div className="col-span-12 md:col-span-3 p-5 flex items-end justify-start md:justify-end font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50">
        {right}
      </div>
    </section>
  );
}
