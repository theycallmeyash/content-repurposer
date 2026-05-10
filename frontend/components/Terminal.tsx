interface TerminalProps {
  lines: string[];
  loop?: boolean;
  mode?: "stream" | "static";
}

export function Terminal({ lines, loop = false, mode = "static" }: TerminalProps) {
  return (
    <div className="h-full min-h-[420px] bg-ink p-6 text-newsprint scan-line">
      <div className="mb-5 flex items-center justify-between border-b border-newsprint/20 pb-3">
        <span className="font-mono-ed text-[10px] uppercase tracking-widest text-newsprint/55">
          terminal / {mode}
        </span>
        <span className="font-mono-ed text-[10px] uppercase tracking-widest text-indigo-electric">
          {loop ? "loop" : "live"}
        </span>
      </div>
      <pre className="whitespace-pre-wrap font-mono-ed text-xs leading-6 text-newsprint/85">
        {lines.join("\n")}
      </pre>
    </div>
  );
}
