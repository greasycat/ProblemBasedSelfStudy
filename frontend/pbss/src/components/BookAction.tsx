import { useState } from 'react';
import { Button } from './Button';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

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
  const [isExpanded, setIsExpanded] = useState(true);

  if (actions.length === 0) {
    return null;
  }

  // Calculate approximate width: each button is 200px + 16px margin on each side (32px total) + gap
  const buttonWidth = 200 + 32; // 200px button + 16px margin on each side
  const gapWidth = 12; // gap-3 = 12px
  const totalWidth = actions.length * buttonWidth + (actions.length - 1) * gapWidth;

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div
        className={`${!isExpanded ? 'overflow-hidden' : ''} transition-all duration-300 ease-in-out`}
        style={{
          maxWidth: isExpanded ? `${totalWidth}px` : '0px',
        }}
      >
        <div className="flex gap-3">
          {actions.map((action, index) => (
            <Button
              key={index}
              variant={action.variant || 'primary'}
              size="none"
              className="py-1 mx-4 text-white bg-primary border-2 border-t-0 border-primary rounded-b-lg w-[200px] hover:opacity-80 hover:pt-8 min-h-[20px] flex-shrink-0 duration-500 ease-out"
              onClick={action.onClick}
              disabled={action.disabled}
            >
              {action.label}
            </Button>
          ))}
        </div>
      </div>
      <Button
        variant="none"
        size="none"
        className="py-2 px-2 text-primary bg-white rounded-b-lg hover:opacity-80 hover:text-primary transition-all duration-500 ease-out rounded-b-lg flex-shrink-0 origin-top"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-label={isExpanded ? 'Collapse actions' : 'Expand actions'}
      >
        {isExpanded ? (
          <div className="flex items-center gap-2">
            <span className="text-bold">Collapse</span>
            <ChevronLeftIcon className="w-5 h-5 " />
          </div>
        ) : (
          <div className="flex items-center gap-2">
          <ChevronRightIcon className="w-5 h-5 " />
            <span className=" text-bold">Build Actions</span>
          </div>
        )}
      </Button>
    </div>
  );
}

