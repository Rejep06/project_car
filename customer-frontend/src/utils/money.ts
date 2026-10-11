const SCALE = 6;
const FACTOR = 1_000_000n;
const MONEY_RE = /^(-?)(\d+)(?:\.(\d{1,6}))?$/;

export function toAtomic(value: string): bigint {
  const normalized = value.trim();
  const match = MONEY_RE.exec(normalized);
  if (!match)
    throw new Error(
      "Сумма должна быть строкой с не более чем шестью знаками после запятой",
    );
  const sign = match[1] === "-" ? -1n : 1n;
  const whole = BigInt(match[2]);
  const fraction = BigInt((match[3] ?? "").padEnd(SCALE, "0"));
  return sign * (whole * FACTOR + fraction);
}

export function fromAtomic(value: bigint): string {
  const sign = value < 0n ? "-" : "";
  const absolute = value < 0n ? -value : value;
  const whole = absolute / FACTOR;
  const fraction = (absolute % FACTOR).toString().padStart(SCALE, "0");
  return `${sign}${whole.toString()}.${fraction}`;
}

export function formatMoney(value: string): string {
  const normalized = fromAtomic(toAtomic(value));
  const [whole, fraction] = normalized.split(".");
  const sign = whole.startsWith("-") ? "-" : "";
  const digits = sign ? whole.slice(1) : whole;
  const grouped = digits.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return `${sign}${grouped}.${fraction}`;
}

export function compareMoney(left: string, right: string): number {
  const a = toAtomic(left);
  const b = toAtomic(right);
  return a === b ? 0 : a > b ? 1 : -1;
}

export function subtractMoney(left: string, right: string): string {
  return fromAtomic(toAtomic(left) - toAtomic(right));
}

export function addMoney(left: string, right: string): string {
  return fromAtomic(toAtomic(left) + toAtomic(right));
}

export function multiplyMoney(value: string, multiplier: number): string {
  if (!Number.isInteger(multiplier) || multiplier < 0)
    throw new Error("Множитель должен быть целым неотрицательным числом");
  return fromAtomic(toAtomic(value) * BigInt(multiplier));
}

// Одинаковое с backend округление half-up до 0.000001 USDT.
export function percentageFee(value: string, percent: number): string {
  if (!Number.isInteger(percent) || percent < 0 || percent > 100)
    throw new Error("Процент комиссии должен быть целым числом от 0 до 100");
  const amount = toAtomic(value);
  if (amount < 0) throw new Error("Сумма не может быть отрицательной");
  return fromAtomic((amount * BigInt(percent) + 50n) / 100n);
}
