import { Button } from "./Button";
import { Modal } from "./Modal";
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Подтвердить",
  danger = false,
  loading = false,
  onConfirm,
  onClose,
}: {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  danger?: boolean;
  loading?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}) {
  return (
    <Modal open={open} title={title} onClose={onClose}>
      <p>{description}</p>
      <div className="form-actions">
        <Button variant="secondary" onClick={onClose}>
          Отмена
        </Button>
        <Button
          variant={danger ? "danger" : "primary"}
          loading={loading}
          onClick={onConfirm}
        >
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  );
}
