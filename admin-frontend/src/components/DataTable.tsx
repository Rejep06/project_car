import type { ReactNode } from "react";
export function DataTable({
  children,
  label,
}: {
  children: ReactNode;
  label: string;
}) {
  return (
    <div className="table-scroll">
      <table>
        <caption className="sr-only">{label}</caption>
        {children}
      </table>
    </div>
  );
}
