interface DialProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
}

export function Dial({ label, value, onChange }: DialProps) {
  const rotation = -135 + value * 2.7;

  return (
    <label className="block border border-ink bg-newsprint p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/55">
          {label}
        </span>
        <span className="font-mono-ed text-xs">{value}</span>
      </div>
      <div className="mx-auto mb-4 grid size-24 place-items-center rounded-full border-2 border-ink bg-card">
        <div
          className="h-10 w-1 origin-bottom bg-indigo-electric"
          style={{ transform: `rotate(${rotation}deg)` }}
        />
      </div>
      <input
        type="range"
        min="0"
        max="100"
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="w-full accent-indigo-electric"
      />
    </label>
  );
}
