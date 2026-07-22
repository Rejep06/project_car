import { formatMoney } from "../utils/money";

export function MoneyValue({
  value,
  asset = "USDT",
  signed = false,
}: {
  value: string;
  asset?: string;
  signed?: boolean;
}) {
  let formatted = value || "0.000000";
  try {
    formatted = formatMoney(formatted);
  } catch {
    // В форме пользователь может временно ввести "50."; интерфейс не должен падать.
  }
  const prefix =
    signed && !formatted.startsWith("-") && formatted !== "0.000000" ? "+" : "";
  return (
    <span className="money-value">
      {prefix}
      {formatted} <small>{asset}</small>
    </span>
  );
}
