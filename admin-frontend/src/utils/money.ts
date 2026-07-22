const SCALE = 6;
const FACTOR = 1_000_000n;
const MONEY_RE = /^(-?)(\d+)(?:\.(\d{1,6}))?$/;

export function toAtomic(value: string): bigint {
  const match = MONEY_RE.exec(value.trim());
  if (!match)
    throw new Error(
      "Сумма должна содержать не более шести знаков после запятой",
    );
  const sign = match[1] === "-" ? -1n : 1n;
  return (
    sign *
    (BigInt(match[2]) * FACTOR + BigInt((match[3] ?? "").padEnd(SCALE, "0")))
  );
}

export function fromAtomic(value: bigint): string {
  const sign = value < 0n ? "-" : "";
  const absolute = value < 0n ? -value : value;
  return `${sign}${absolute / FACTOR}.${(absolute % FACTOR).toString().padStart(SCALE, "0")}`;
}

export function formatMoney(value: string): string {
  const [whole, fraction] = fromAtomic(toAtomic(value)).split(".");
  const sign = whole.startsWith("-") ? "-" : "";
  const digits = sign ? whole.slice(1) : whole;
  return `${sign}${digits.replace(/\B(?=(\d{3})+(?!\d))/g, " ")}.${fraction}`;
}

export function compareMoney(left: string, right: string): number {
  const a = toAtomic(left);
  const b = toAtomic(right);
  return a === b ? 0 : a > b ? 1 : -1;
}

export function subtractMoney(left: string, right: string): string {
  return fromAtomic(toAtomic(left) - toAtomic(right));
}
