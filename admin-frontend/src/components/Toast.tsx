export function Toast({
  message,
  type = "success",
}: {
  message: string;
  type?: "success" | "error";
}) {
  return (
    <div className={`toast toast-${type}`} role="status" aria-live="polite">
      {message}
    </div>
  );
}
