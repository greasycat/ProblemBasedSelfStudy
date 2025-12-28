# Frontend Refactoring TODO

This document outlines actionable steps to fix the top 3 critical design issues identified in FRONTEND.md.

## Problem 1: State Management Issues

### 1.1 Fix Excessive State in BooksPage

#### Step 1.1.1: Create Modal State Management Hook
- [x] Create `src/hooks/useModalState.ts`
- [x] Implement generic modal state hook with `isOpen`, `data`, `open`, `close` methods
- [x] Support multiple modal types (edit, details, view, etc.)

```typescript
// Example structure
interface UseModalStateReturn<T> {
  isOpen: boolean;
  data: T | null;
  open: (data?: T) => void;
  close: () => void;
}
```

#### Step 1.1.2: Create Book View State Hook
- [x] Create `src/hooks/useBookViewState.ts`
- [x] Consolidate `bookViewBook`, `bookViewPage`, `isBookViewOpen` states
- [x] Include logic for page navigation and alignment offset

#### Step 1.1.3: Refactor BooksPage to Use New Hooks
- [x] Replace individual state variables with modal hooks
- [x] Replace book view states with `useBookViewState`
- [x] Remove redundant state declarations
- [x] Test all modal/book view functionality still works

### 1.2 Implement Global State Management

#### Step 1.2.1: Install Zustand
- [ ] Run `npm install zustand` (or `bun add zustand`)
- [ ] Add TypeScript types if needed

#### Step 1.2.2: Create Books Store
- [ ] Create `src/stores/useBooksStore.ts`
- [ ] Move books state from `useBooks` hook to store
- [ ] Move `selectedBook` state to store
- [ ] Implement actions: `setBooks`, `selectBook`, `updateBook`, `removeBook`
- [ ] Add selectors for filtered/sorted books if needed

#### Step 1.2.3: Create UI State Store
- [ ] Create `src/stores/useUIStore.ts`
- [ ] Move global UI state (loading, errors) to store
- [ ] Implement actions for managing UI state
- [ ] Add toast notification state if implementing toasts

#### Step 1.2.4: Refactor Components to Use Stores
- [ ] Update `BooksPage` to use `useBooksStore` and `useUIStore`
- [ ] Update `Sidebar` to use stores instead of props
- [ ] Update `Chat` component to use stores
- [ ] Remove prop drilling for books and selectedBook
- [ ] Test all functionality still works

#### Step 1.2.5: Update useBooks Hook (Optional)
- [ ] Refactor `useBooks` to use stores internally, or
- [ ] Deprecate `useBooks` and migrate components to use stores directly
- [ ] Update all components using `useBooks` hook

### 1.3 Consolidate Duplicated State Logic in Hooks

#### Step 1.3.1: Create Generic useResource Hook
- [ ] Create `src/hooks/useResource.ts`
- [ ] Implement generic CRUD operations pattern
- [ ] Include common state: `items`, `loading`, `error`, `setError`
- [ ] Support operations: `load`, `loadOne`, `create`, `update`, `remove`
- [ ] Use TypeScript generics for type safety

```typescript
// Example structure
interface UseResourceOptions<T, ID> {
  loadFn: () => Promise<T[]>;
  loadOneFn?: (id: ID) => Promise<T>;
  createFn?: (data: Partial<T>) => Promise<T>;
  updateFn?: (id: ID, data: Partial<T>) => Promise<T>;
  deleteFn?: (id: ID) => Promise<void>;
}

function useResource<T, ID extends string | number>(options: UseResourceOptions<T, ID>)
```

#### Step 1.3.2: Refactor useBooks Hook
- [ ] Refactor `useBooks.ts` to use `useResource` internally
- [ ] Remove duplicated state management code
- [ ] Keep book-specific logic (like upload, alignment) in hook
- [ ] Test all book operations

#### Step 1.3.3: Refactor usePages Hook
- [ ] Refactor `usePages.ts` to use `useResource`
- [ ] Remove duplicated patterns
- [ ] Test all page operations

#### Step 1.3.4: Refactor useSections Hook
- [ ] Refactor `useSections.ts` to use `useResource`
- [ ] Remove duplicated patterns
- [ ] Test all section operations

#### Step 1.3.5: Create Shared Error Handling Utility
- [ ] Create `src/utils/errorHandler.ts`
- [ ] Extract common error message formatting logic
- [ ] Create error handler functions for ApiError, generic Error, unknown
- [ ] Update all hooks to use shared error handler

---

## Problem 2: Component Architecture Issues

### 2.1 Refactor God Component (BooksPage)

#### Step 2.1.1: Extract Modal Management
- [ ] Create `src/components/modals/BookEditModal.tsx` (if not already componentized)
- [ ] Create `src/components/modals/BookDetailsModal.tsx` (if not already componentized)
- [ ] Create `src/components/modals/BookViewModal.tsx` (if not already componentized)
- [ ] Move modal rendering logic from BooksPage to separate components
- [ ] Pass only necessary props to modal components

#### Step 2.1.2: Extract Visual Alignment Logic
- [ ] Create `src/hooks/useVisualAlignment.ts`
- [ ] Move `handleVisualAlign` logic from BooksPage to hook
- [ ] Move `handleVisualAlignConfirm` logic to hook
- [ ] Include alignment offset calculation logic
- [ ] Return alignment functions and state from hook

#### Step 2.1.3: Extract Book Actions Logic
- [ ] Create `src/hooks/useBookActions.ts`
- [ ] Move `handleView`, `handleEdit`, `handleDelete` logic to hook
- [ ] Include error handling for each action
- [ ] Return action handlers from hook

#### Step 2.1.4: Create BooksPageContainer Component
- [ ] Create `src/pages/BooksPageContainer.tsx`
- [ ] Move all business logic and hooks to container
- [ ] Keep only presentation logic in BooksPage
- [ ] Use composition pattern to connect container with presentation

#### Step 2.1.5: Split BooksPage into Smaller Components
- [ ] Create `src/components/books/BooksLayout.tsx` for layout structure
- [ ] Extract Sidebar integration into separate component
- [ ] Extract Chat integration into separate component
- [ ] Reduce BooksPage to orchestration component
- [ ] Ensure single responsibility for each component

### 2.2 Extract Business Logic from Components

#### Step 2.2.1: Extract Chat Business Logic
- [ ] Create `src/hooks/useChat.ts`
- [ ] Move message state management to hook
- [ ] Move `fetchChapters`, `fetchSections` logic to hook
- [ ] Move `handleSend` logic to hook
- [ ] Return state and handlers from hook

#### Step 2.2.2: Extract Table of Contents Logic
- [ ] Create `src/hooks/useTableOfContents.ts`
- [ ] Move TOC item selection logic to hook
- [ ] Move navigation (back, forward) logic to hook
- [ ] Move display items state to hook

#### Step 2.2.3: Extract Book Edit Logic
- [ ] Create `src/hooks/useBookEdit.ts`
- [ ] Move form state management to hook
- [ ] Move validation logic to hook
- [ ] Move save/cancel logic to hook
- [ ] Update BookEdit component to use hook

#### Step 2.2.4: Extract Book Details Logic
- [ ] Create `src/hooks/useBookDetails.ts`
- [ ] Move page loading logic to hook
- [ ] Move update operations logic to hook
- [ ] Update BookDetails component to use hook

#### Step 2.2.5: Create Utility Functions for Calculations
- [ ] Create `src/utils/bookUtils.ts`
- [ ] Extract alignment offset calculations
- [ ] Extract page number calculations
- [ ] Extract any other calculation logic from components
- [ ] Add unit tests for utility functions

### 2.3 Improve Component Composition

#### Step 2.3.1: Create Book Card Compound Component
- [ ] Refactor `BookCard` (if exists) or create new compound component
- [ ] Use compound component pattern for book actions
- [ ] Make components composable and reusable

#### Step 2.3.2: Create Modal Compound Components
- [ ] Refactor Modal component to support compound pattern
- [ ] Create Modal.Header, Modal.Body, Modal.Footer sub-components
- [ ] Update all modal usages to use compound pattern

#### Step 2.3.3: Reduce Props Drilling
- [ ] Identify components with deep prop drilling
- [ ] Use Context API for deeply nested props (if not using Zustand)
- [ ] Or use render props pattern where appropriate
- [ ] Refactor to reduce prop passing depth

#### Step 2.3.4: Create Reusable Component Patterns
- [ ] Create `src/components/common/` directory for reusable components
- [ ] Extract common patterns into reusable components
- [ ] Document component usage patterns

---

## Problem 3: Error Handling Issues

### 3.1 Implement Consistent Error Handling

#### Step 3.1.1: Create Error Types
- [ ] Create `src/types/errors.ts`
- [ ] Define error type interfaces (ApiError, ValidationError, NetworkError, etc.)
- [ ] Create error type guards/checkers
- [ ] Export error types for use across codebase

#### Step 3.1.2: Create Error Handler Utility
- [ ] Create `src/utils/errorHandler.ts`
- [ ] Implement `handleApiError(error: unknown): string` function
- [ ] Implement `handleNetworkError(error: unknown): string` function
- [ ] Implement `handleValidationError(error: unknown): string` function
- [ ] Create unified error message formatting
- [ ] Support error code mapping if needed

#### Step 3.1.3: Create Error Context/Provider
- [ ] Create `src/contexts/ErrorContext.tsx`
- [ ] Implement ErrorProvider with error state
- [ ] Provide methods: `setError`, `clearError`, `handleError`
- [ ] Support different error types and severity levels

#### Step 3.1.4: Implement Error Boundary Component
- [ ] Create `src/components/ErrorBoundary.tsx`
- [ ] Implement React Error Boundary class component
- [ ] Add error logging (to be replaced with proper logger later)
- [ ] Create user-friendly error fallback UI
- [ ] Wrap App or main routes with ErrorBoundary

#### Step 3.1.5: Standardize Error Handling in Hooks
- [ ] Update `useBooks` hook to use error handler utility
- [ ] Update `usePages` hook to use error handler utility
- [ ] Update `useSections` hook to use error handler utility
- [ ] Ensure all hooks handle errors consistently
- [ ] Always set user-friendly error messages

#### Step 3.1.6: Standardize Error Handling in Components
- [ ] Update `BooksPage` to use consistent error handling
- [ ] Update `Chat` component error handling
- [ ] Update `BookEdit` error handling
- [ ] Update `BookDetails` error handling
- [ ] Remove inconsistent try-catch patterns
- [ ] Ensure all errors are shown to users

### 3.2 Replace Console Logging

#### Step 3.2.1: Install Logging Library
- [ ] Choose logging library (recommended: `pino` or create custom logger)
- [ ] Run `npm install pino` (or preferred library)
- [ ] Install `pino-pretty` for development if using pino

#### Step 3.2.2: Create Logger Utility
- [ ] Create `src/utils/logger.ts`
- [ ] Implement logger with levels: debug, info, warn, error
- [ ] Support environment-based logging (dev vs production)
- [ ] Disable logging in production or use appropriate levels
- [ ] Add structured logging support

```typescript
// Example structure
export const logger = {
  debug: (message: string, ...args: any[]) => { /* ... */ },
  info: (message: string, ...args: any[]) => { /* ... */ },
  warn: (message: string, ...args: any[]) => { /* ... */ },
  error: (message: string, error?: Error, ...args: any[]) => { /* ... */ },
};
```

#### Step 3.2.3: Replace Console Logs in API Service
- [ ] Update `src/services/api.ts`
- [ ] Replace `console.log('Fetching API:', url)` with `logger.debug(...)`
- [ ] Replace `console.error` statements with `logger.error(...)`
- [ ] Remove or guard all console statements
- [ ] Test API calls still work correctly

#### Step 3.2.4: Replace Console Logs in Components
- [ ] Update `src/components/Chat.tsx` - remove/replace 7 console statements
- [ ] Update `src/pages/BooksPage.tsx` - remove/replace 5 console statements
- [ ] Update `src/components/BookEdit.tsx` - remove/replace 1 console.log
- [ ] Update `src/components/Sidebar.tsx` - remove/replace 1 console.error
- [ ] Replace with appropriate logger calls or remove if unnecessary

#### Step 3.2.5: Replace Console Logs in Hooks
- [ ] Update `src/hooks/useBooks.ts` - remove/replace 1 console.error
- [ ] Ensure all hooks use logger instead of console
- [ ] Remove debug-only console logs

#### Step 3.2.6: Add ESLint Rule to Prevent Console Logs
- [ ] Update `eslint.config.js` or create `.eslintrc` rule
- [ ] Add rule to warn/error on console.log/error usage
- [ ] Allow console in test files if needed
- [ ] Test ESLint catches console usage

### 3.3 Implement User Feedback for Errors

#### Step 3.3.1: Install Toast Notification Library
- [ ] Choose toast library (recommended: `react-hot-toast` or `sonner`)
- [ ] Run `npm install react-hot-toast` (or preferred library)
- [ ] Add TypeScript types if needed

#### Step 3.3.2: Setup Toast Provider
- [ ] Create `src/components/Toaster.tsx` or use library's provider
- [ ] Wrap App with Toaster provider
- [ ] Configure toast styles to match design system
- [ ] Test toast rendering works

#### Step 3.3.3: Create Toast Utility Functions
- [ ] Create `src/utils/toast.ts`
- [ ] Implement wrapper functions: `toast.success()`, `toast.error()`, `toast.info()`, `toast.warning()`
- [ ] Create specific error toast helpers: `showApiError()`, `showNetworkError()`
- [ ] Support custom durations and actions

#### Step 3.3.4: Integrate Toasts in Error Handler
- [ ] Update `src/utils/errorHandler.ts`
- [ ] Add optional toast notification when errors occur
- [ ] Make toasts configurable (can be disabled)
- [ ] Ensure user-friendly error messages

#### Step 3.3.5: Add Toasts to API Error Handling
- [ ] Update `src/services/api.ts` error handling
- [ ] Show toast notifications for API errors (if not handled by component)
- [ ] Use appropriate toast types (error, warning) based on error type

#### Step 3.3.6: Add Toasts to Hook Error Handling
- [ ] Update `useBooks` hook to show toasts on errors
- [ ] Update `usePages` hook to show toasts on errors
- [ ] Update `useSections` hook to show toasts on errors
- [ ] Ensure toasts don't duplicate with component error displays

#### Step 3.3.7: Add Toasts to Component Error Handling
- [ ] Update `BooksPage` to show toasts for critical errors
- [ ] Update `Chat` to show toasts for fetch errors
- [ ] Update `BookEdit` to show toasts for save errors
- [ ] Update `BookDetails` to show toasts for operation errors
- [ ] Ensure all user-facing errors show feedback

#### Step 3.3.8: Add Success Toasts
- [ ] Add success toasts for successful operations (create, update, delete)
- [ ] Update `useBooks` to show success toasts
- [ ] Update `BookEdit` to show success toast on save
- [ ] Update other components with success operations
- [ ] Ensure consistent success messaging

#### Step 3.3.9: Replace window.confirm with Custom Modal
- [ ] Create `src/components/modals/ConfirmDialog.tsx`
- [ ] Implement reusable confirmation dialog component
- [ ] Update `BooksPage` handleDelete to use ConfirmDialog instead of window.confirm
- [ ] Test delete confirmation flow
- [ ] Replace any other window.confirm/alert usage

---

## Testing Checklist

After completing each major section, test the following:

### State Management Testing
- [ ] All modals open/close correctly
- [ ] Book selection works across components
- [ ] State updates propagate correctly
- [ ] No state synchronization issues
- [ ] Performance is acceptable (no unnecessary re-renders)

### Component Architecture Testing
- [ ] All components render correctly
- [ ] Business logic extracted correctly
- [ ] No broken functionality
- [ ] Component composition works as expected
- [ ] Code is more maintainable and readable

### Error Handling Testing
- [ ] Errors are caught and displayed to users
- [ ] Toast notifications appear correctly
- [ ] Error messages are user-friendly
- [ ] No console errors in browser console
- [ ] Error boundary catches React errors
- [ ] Network errors are handled gracefully

---

## Implementation Order Recommendation

1. **Start with Error Handling (Problem 3)** - Provides foundation for better error tracking during refactoring
   - 3.2 (Logger) → 3.1 (Error handling) → 3.3 (User feedback)

2. **Then State Management (Problem 1)** - Simplifies component refactoring
   - 1.3 (Generic hooks) → 1.2 (Global state) → 1.1 (BooksPage state)

3. **Finally Component Architecture (Problem 2)** - Builds on improved state management
   - 2.2 (Extract logic) → 2.1 (Refactor BooksPage) → 2.3 (Composition)

---

## Notes

- Complete each step and test before moving to the next
- Update this TODO as you complete items
- Consider creating feature branches for each major section
- Write tests for new utilities and hooks as you create them
- Keep the existing functionality working throughout refactoring

