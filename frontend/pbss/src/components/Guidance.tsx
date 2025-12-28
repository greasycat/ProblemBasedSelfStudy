import { useState } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { ConfirmDialog } from './ConfirmDialog';
import { useGuidanceStore } from '../stores/useGuidanceStore';

/**
 * Guidance modal component
 * Displays instructions with navigation arrows
 */
export function Guidance() {
  const {
    instructions,
    currentIndex,
    isOpen,
    exitWarning,
    nextInstruction,
    previousInstruction,
    closeGuidance,
  } = useGuidanceStore();

  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  const currentInstruction = instructions[currentIndex];
  const hasNext = currentIndex < instructions.length - 1;
  const hasPrevious = currentIndex > 0;

  const handleClose = () => {
    if (exitWarning) {
      setShowConfirmDialog(true);
    } else {
      closeGuidance();
    }
  };

  const handleConfirmClose = () => {
    setShowConfirmDialog(false);
    closeGuidance();
  };

  const handleCancelClose = () => {
    setShowConfirmDialog(false);
  };

  if (!isOpen || instructions.length === 0) return null;

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={handleClose}
        title="Guidance"
        maxWidth="max-w-2xl"
      >
      <div className="flex flex-col gap-6">
        {/* Instruction content */}
        <div className="min-h-[200px] flex items-center justify-center p-6 rounded-lg">
          {currentInstruction ? (
            <p className="text-text-primary text-lg leading-relaxed text-center">
              {currentInstruction.text}
            </p>
          ) : (
            <p className="text-text-secondary">No instruction available</p>
          )}
        </div>

        {/* Callback buttons - vertically aligned column */}
        {currentInstruction?.callbacks && currentInstruction.callbacks.length > 0 && (
          <div className="flex flex-col gap-3">
            {currentInstruction.callbacks.map((callback, index) => {
              const buttonLabel = currentInstruction.buttonLabels?.[index] || `Action ${index + 1}`;
              return (
                <Button
                  key={index}
                  variant="primary"
                  size="medium"
                  onClick={callback}
                  className="w-full"
                >
                  {buttonLabel}
                </Button>
              );
            })}
          </div>
        )}

        {/* Navigation footer */}
        <div className="flex items-center justify-between">
          {hasPrevious ? (
            <Button
              variant="secondary"
              size="medium"
              onClick={previousInstruction}
              className="flex items-center gap-2"
            >
              <span>←</span>
              <span>Previous</span>
            </Button>
          ) : (
            <div></div>
          )}

          <div className="text-text-secondary text-sm">
            {currentIndex + 1} of {instructions.length}
          </div>

          {hasNext ? (
            <Button
              variant="secondary"
              size="medium"
              onClick={nextInstruction}
              className="flex items-center gap-2"
            >
              <span>Next</span>
              <span>→</span>
            </Button>
          ) : (
            <div></div>
          )}
        </div>
      </div>
    </Modal>
    <ConfirmDialog
      isOpen={showConfirmDialog}
      message={exitWarning || ''}
      onConfirm={handleConfirmClose}
      onCancel={handleCancelClose}
      confirmLabel="Exit"
      cancelLabel="Cancel"
    />
    </>
  );
}
