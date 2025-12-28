import { Modal } from './Modal';
import { Button } from './Button';

interface ConfirmDialogProps {
  isOpen: boolean;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmLabel?: string;
  cancelLabel?: string;
}

/**
 * Confirmation dialog component
 * Displays a message with confirm and cancel buttons
 */
export function ConfirmDialog({
  isOpen,
  message,
  onConfirm,
  onCancel,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
}: ConfirmDialogProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onCancel}
      title="Confirm"
      maxWidth="max-w-md"
      zIndex={2000}
    >
      <div className="flex flex-col gap-6">
        <p className="text-text-primary text-base leading-relaxed">
          {message}
        </p>
        <div className="flex justify-end gap-3">
          <Button
            variant="secondary"
            size="medium"
            onClick={onCancel}
          >
            {cancelLabel}
          </Button>
          <Button
            variant="primary"
            size="medium"
            onClick={onConfirm}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
