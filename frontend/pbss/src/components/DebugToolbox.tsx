import { Button } from './Button';
import { useToastStore } from '../stores/useToastStore';
import { useGuidanceStore, Instruction } from '../stores/useGuidanceStore';

/**
 * Debug toolbox component
 * Provides buttons to test various UI components
 */
export function DebugToolbox() {
  const { showToast } = useToastStore();
  const { setInstructions, openGuidance } = useGuidanceStore();

  const handleTestToast = () => {
    showToast('This is a test toast notification!', 'info');
  };

  const handleTestGuidance = () => {
    setInstructions([
      new Instruction('This is the first test instruction'),
      new Instruction('This is the second test instruction'),
      new Instruction('This is the third test instruction'),
    ]);
    openGuidance();
  };

  const handleTestInstructionButtons = () => {
    setInstructions([
      new Instruction(
        'This instruction has callback buttons. Click them to see console logs!',
        [
          () => console.log('Callback 1 executed!'),
          () => console.log('Callback 2 executed!'),
          () => console.log('Callback 3 executed!'),
        ]
      ),
    ], 'Are you sure you want to exit?');
    openGuidance();
  };

  return (
    <div className="fixed right-4 top-1/2 -translate-y-1/2 z-50 flex flex-col gap-2">
      <Button
        variant="secondary"
        size="small"
        onClick={handleTestToast}
        className="whitespace-nowrap"
      >
        Test Toast
      </Button>
      <Button
        variant="secondary"
        size="small"
        onClick={handleTestGuidance}
        className="whitespace-nowrap"
      >
        Test Guidance
      </Button>
      <Button
        variant="secondary"
        size="small"
        onClick={handleTestInstructionButtons}
        className="whitespace-nowrap"
      >
        Test Instruction Buttons
      </Button>
    </div>
  );
}
