import { create } from 'zustand';

export class Instruction {
  text: string;
  callbacks: (() => void)[] | null;
  buttonLabels?: string[];

  constructor(text: string, callbacks: (() => void)[] = [], buttonLabels?: string[]) {
    this.text = text;
    this.callbacks = callbacks;
    this.buttonLabels = buttonLabels;
  }
}

interface GuidanceStore {
  instructions: Instruction[];
  currentIndex: number;
  isOpen: boolean;
  exitWarning?: string;
  
  // Actions
  setInstructions: (instructions: Instruction[], exitWarning?: string) => void;
  addInstruction: (instruction: Instruction) => void;
  nextInstruction: () => void;
  previousInstruction: () => void;
  goToInstruction: (index: number) => void;
  openGuidance: () => void;
  closeGuidance: () => void;
}

/**
 * Zustand store for managing guidance modal and instructions
 * 
 * @example
 * ```tsx
 * const { 
 *   instructions, 
 *   currentIndex, 
 *   isOpen,
 *   setInstructions,
 *   nextInstruction,
 *   previousInstruction,
 *   openGuidance,
 *   closeGuidance 
 * } = useGuidanceStore();
 * 
 * // Set instructions
 * setInstructions([
 *   new Instruction('First instruction'),
 *   new Instruction('Second instruction'),
 * ]);
 * 
 * // Open guidance modal
 * openGuidance();
 * 
 * // Navigate
 * nextInstruction();
 * previousInstruction();
 * ```
 */
export const useGuidanceStore = create<GuidanceStore>((set) => ({
  instructions: [],
  currentIndex: 0,
  isOpen: false,
  exitWarning: undefined,

  setInstructions: (instructions, exitWarning) => {
    set({ 
      instructions,
      currentIndex: 0, // Reset to first instruction when setting new instructions
      exitWarning,
    });
  },

  addInstruction: (instruction) => {
    set((state) => ({
      instructions: [...state.instructions, instruction],
    }));
  },

  nextInstruction: () => {
    set((state) => {
      const maxIndex = state.instructions.length - 1;
      const nextIndex = state.currentIndex < maxIndex 
        ? state.currentIndex + 1 
        : state.currentIndex;
      return { currentIndex: nextIndex };
    });
  },

  previousInstruction: () => {
    set((state) => {
      const prevIndex = state.currentIndex > 0 
        ? state.currentIndex - 1 
        : state.currentIndex;
      return { currentIndex: prevIndex };
    });
  },

  goToInstruction: (index) => {
    set((state) => {
      if (index >= 0 && index < state.instructions.length) {
        return { currentIndex: index };
      }
      return state;
    });
  },

  openGuidance: () => {
    set({ isOpen: true });
  },

  closeGuidance: () => {
    set({ isOpen: false });
  },
}));
