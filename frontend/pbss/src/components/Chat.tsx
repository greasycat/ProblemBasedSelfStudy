import { useState, useRef, useEffect } from 'react';
import { Button } from './Button';
import { TableOfContents } from './TableOfContents';
import { Modal } from './Modal';
import { bookApi } from '../services/api';
import { useBooksStore } from '../stores/useBooksStore';
import { useTocStore } from '../stores/useTocStore';
import { useUIStore } from '../stores/useUIStore';
import { useBookViewStore } from '../stores/useBookViewStore';
import { BookAction } from './BookAction';
import type { ActionCallback } from './BookAction';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

export function Chat() {
  // Get selectedBook from store
  const { selectedBook } = useBooksStore();
  const { state: tocState, fetchChapters, fetchTotalPages, reset } = useTocStore();
  const { pdfViewBook, setPdfViewBook } = useUIStore();
  const { open: openBookView, setPage: setBookViewPage } = useBookViewStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isPdfModalOpen, setIsPdfModalOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch total pages and chapters when book is selected
  useEffect(() => {
    if (!selectedBook?.book_id) {
      reset();
      return;
    }

    fetchTotalPages();
    fetchChapters();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBook?.book_id]); // Store functions are stable, no need to include them

  // Open PDF modal when pdfViewBook changes
  useEffect(() => {
    if (pdfViewBook) {
      setIsPdfModalOpen(true);
    }
  }, [pdfViewBook]);

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Simulate API call - replace with actual API call later
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `This is a placeholder response. The chat functionality will be connected to the backend API.`,
        sender: 'assistant',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1000);
  };

  const handleKeyUp = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Placeholder actions for BookAction component
  const placeholderActions: ActionCallback[] = [
    {
      label: 'Get Table of Contents',
      onClick: () => {
        if (!selectedBook?.book_id) return;
        bookApi.updateToc({
          book_id: selectedBook.book_id,
          overwrite: true,
          caching: false,
        }).then((response) => {
          console.log('Table of contents updated:', response);
        }).catch((error) => {
          console.error('Failed to update table of contents:', error);
        });
      },
      variant: 'none',
    },
    {
      label: 'Extract Current Chapter',
      onClick: () => {
        console.log('Placeholder Action 2 clicked');
      },
      variant: 'none',
    },
    {
      label: 'Extract Current Section',
      onClick: () => {
        console.log('Placeholder Action 3 clicked');
      },
      variant: 'none',
    },
  ];

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Table of Contents Section */}
      {selectedBook && (
        <div className="px-6 py-4 border-b border-gray-200 relative">
            <TableOfContents />
            {/* BookAction Component - positioned absolutely below TOC */}
        </div>
      )}

      {selectedBook && (
        <BookAction actions={placeholderActions} />
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 relative">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-text-secondary">
            <div className="text-center">
              <p className="text-lg mb-2">No messages yet</p>
              <p className="text-sm">Start a conversation by typing a message below</p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 shadow-md ${
                  message.sender === 'user'
                    ? 'bg-primary text-white'
                    : 'bg-background-subtle text-text-primary'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap break-words">{message.text}</p>
                <p
                  className={`text-xs mt-1 ${
                    message.sender === 'user' ? 'text-white/70' : 'text-text-secondary'
                  }`}
                >
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-background-subtle text-text-primary rounded-lg px-4 py-3 shadow-md">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* View PDF and PNG Buttons */}
      {selectedBook?.book_id && (
        <div className="px-6 py-2 justify-center items-center flex gap-2">
          <Button
            variant="primary"
            className="shadow-lg hover:opacity-80 hover:translate-y-[-2px]"
            onClick={() => {
              if (selectedBook && tocState.selectedItem?.start_page_number !== undefined) {
                const pageNumber = tocState.selectedItem.start_page_number + (selectedBook.alignment_offset || 0);
                console.log('Selected item start page number:', tocState.selectedItem.start_page_number);
                console.log('Alignment offset:', selectedBook.alignment_offset);
                console.log('Current PNG page:', pageNumber);
                openBookView(selectedBook);
                setBookViewPage(pageNumber);
              }
            }}
          >
          View
          </Button>
        </div>
      )}

      {/* Input Area */}
      <div className="px-6 py-4 mb-6 justify-center items-center flex">
        <div className="flex gap-2 w-[50%]">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyUp={handleKeyUp}
            placeholder={selectedBook ? "Type your message..." : "Select a book to start chatting"}
            disabled={!selectedBook || isLoading}
            className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg text-base focus:border-primary focus:outline-none disabled:bg-background-subtle disabled:cursor-not-allowed disabled:text-text-light shadow-md shadow-brown"
          />
          <Button
            variant="primary"
            onClick={handleSend}
            disabled={!inputValue.trim() || !selectedBook || isLoading}
            isLoading={isLoading}
          >
            Send
          </Button>
        </div>
      </div>

      {/* PDF Viewer Modal */}
      {pdfViewBook?.book_id && (
        <Modal
          isOpen={isPdfModalOpen}
          onClose={() => {
            setIsPdfModalOpen(false);
            setPdfViewBook(null);
          }}
          title="PDF Viewer"
          maxWidth="max-w-6xl"
          hideHeader={true}
          noShadow={true}
        >
          <div className="w-full h-[100vh]">
            <iframe
              src={`${import.meta.env.VITE_API_BASE_URL || ''}/view-pdf?book_id=${pdfViewBook.book_id}`}
              className="w-full h-full border-0 rounded-xl"
              title="PDF Viewer"
            />
          </div>
        </Modal>
      )}
    </div>
  );
}
