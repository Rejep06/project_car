import { label } from "../utils/labels";
export function StatusBadge({ value }: { value: string }) {
  return <span className={`status status-${value}`}>{label(value)}</span>;
}
