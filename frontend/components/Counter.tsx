interface CounterProps {
  to: number;
  suffix?: string;
  decimals?: number;
}

export function Counter({ to, suffix = "", decimals = 0 }: CounterProps) {
  return (
    <>
      {to.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}
      {suffix}
    </>
  );
}
