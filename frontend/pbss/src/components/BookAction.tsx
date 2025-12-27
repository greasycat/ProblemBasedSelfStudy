import { Button } from './Button';

export interface ActionCallback {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'none';
  disabled?: boolean;
}

interface BookActionProps {
  actions: ActionCallback[];
  className?: string;
}

export function BookAction({ actions, className = '' }: BookActionProps) {
  if (actions.length === 0) {
    return null;
  }

  return (
    <div className={`flex justify-center gap-3 ${className}`}>
      {actions.map((action, index) => (
        <Button
          key={index}
          variant={action.variant || 'primary'}
          size="none"
          className="py-1 mx-4 text-white bg-primary border-2 border-t-0 border-primary rounded-b-lg w-[200px] hover:opacity-80 hover:translate-y-[-2px]"
          onClick={action.onClick}
          disabled={action.disabled}
        >
          {action.label}
        </Button>
      ))}
    </div>
  );
}

