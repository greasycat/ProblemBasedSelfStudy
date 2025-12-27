import { useState, useRef, useEffect } from 'react';
import { Button } from './Button';
import { TableOfContents } from './TableOfContents';
import { Modal } from './Modal';
import { BookView } from './BookView';
import { bookApi, sectionApi } from '../services/api';
import type { TocItem, Book } from '../types/api';
import { BookAction } from './BookAction';
import type { ActionCallback } from './BookAction';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

interface ChatProps {
  selectedBook?: Book | null;
  bookToViewPdf?: Book | null;
  onPdfViewClose?: () => void;
}

export function Chat({ selectedBook, bookToViewPdf, onPdfViewClose }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [displayItems, setDisplayItems] = useState<TocItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<TocItem | null>(null);
  const [parentItem, setParentItem] = useState<TocItem | null>(null);
  const [tocOpacity, setTocOpacity] = useState(1);
  const [isPdfModalOpen, setIsPdfModalOpen] = useState(false);
  const [isPngModalOpen, setIsPngModalOpen] = useState(false);
  const [currentPngPage, setCurrentPngPage] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number | undefined>(undefined);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
    
  const fetchChapters =  async () => {

      setTocOpacity(0);

      // No book selected, reset state
        if (!selectedBook?.book_id) {
          setSelectedItem(null);
          setDisplayItems([]);
          return;
        }

        setIsLoading(true);
        try {
          const response = await bookApi.getChapters(selectedBook.book_id);
          setDisplayItems(response.chapters);
          setSelectedItem(null);
        } catch (error) {
          console.error('Failed to fetch chapters:', error);
          setDisplayItems([]);
          setSelectedItem(null);
        } finally {
          setIsLoading(false);
        }

      setTimeout(async () => {
        setTocOpacity(1);
      }, 200);
  };

  const fetchSections = async (chapter_id: number) => {

    setTocOpacity(0);

      if (!selectedBook?.book_id) return;
      setIsLoading(true);
      try {
        const response = await sectionApi.getSections(selectedBook.book_id, chapter_id);
        setDisplayItems(response.sections);
      } catch (error) {
        console.error('Failed to fetch sections:', error);
        setDisplayItems([]);
      } finally {
          setIsLoading(false);
        }

    setTimeout(async () => {
    setTocOpacity(1);
    }, 200);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch total pages and chapters when book is selected
  useEffect(() => {
    const fetchTotalPages = async () => {
      if (!selectedBook?.book_id) {
        setTotalPages(undefined);
        return;
      }
      
      try {
        const response = await bookApi.getTotalPages(selectedBook.book_id);
        setTotalPages(response.total_pages);
      } catch (error) {
        console.error('Failed to fetch total pages:', error);
        setTotalPages(undefined);
      }
    };

    fetchTotalPages();
    fetchChapters();
  }, [selectedBook?.book_id]);

  // Open PDF modal when bookToViewPdf changes
  useEffect(() => {
    if (bookToViewPdf) {
      setIsPdfModalOpen(true);
    }
  }, [bookToViewPdf]);

  // Handle chapter click to fetch sections
  const handleTocItemClick = async (item: TocItem) => {
    if (!selectedBook?.book_id || !item) return;

    if (selectedItem) {
      setParentItem(selectedItem);
    }

    setSelectedItem(item);

    if (item.type === 'chapter') {
      if (item.chapter_id) {
        fetchSections(item.chapter_id);
      }
      return;
    }

    if (item.type === 'section') {
      return;
    }

  };

  // Handle back button to return to chapters view
  const handleBack = () => {
    if (!selectedBook?.book_id) return;

    if (selectedItem?.type === 'chapter') {
      fetchChapters();
      return;
    }

    if (selectedItem?.type === 'section') {
      // select selected item to parent item
      setSelectedItem(parentItem);
      return;
    }
  };

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
            <TableOfContents 
              displayItems={displayItems}
              totalPages={totalPages}
              onTocItemClick={handleTocItemClick}
              onBack={handleBack}
              showBackButton={selectedItem !== null}
              selectedItem={selectedItem}
              opacity={tocOpacity}
              bookId={selectedBook.book_id}
            />
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
              if (selectedItem?.start_page_number !== undefined) {
                console.log('Selected item start page number:', selectedItem.start_page_number);
                console.log('Alignment offset:', selectedBook?.alignment_offset);
                console.log('Current PNG page:', selectedItem.start_page_number + (selectedBook?.alignment_offset || 0));
                setCurrentPngPage(selectedItem.start_page_number + (selectedBook?.alignment_offset || 0));
              }
              setIsPngModalOpen(true);
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
      {bookToViewPdf?.book_id && (
        <Modal
          isOpen={isPdfModalOpen}
          onClose={() => {
            setIsPdfModalOpen(false);
            onPdfViewClose?.();
          }}
          title="PDF Viewer"
          maxWidth="max-w-6xl"
          hideHeader={true}
          noShadow={true}
        >
          <div className="w-full h-[100vh]">
            <iframe
              src={`${import.meta.env.VITE_API_BASE_URL || ''}/view-pdf?book_id=${bookToViewPdf.book_id}`}
              className="w-full h-full border-0 rounded-xl"
              title="PDF Viewer"
            />
          </div>
        </Modal>
      )}

      {/* PNG Viewer Modal */}
      {selectedBook?.book_id && currentPngPage !== undefined && (
        <BookView
          isOpen={isPngModalOpen}
          onClose={() => setIsPngModalOpen(false)}
          bookId={selectedBook.book_id}
          currentPage={currentPngPage}
          totalPages={totalPages}
          onPageChange={(page) => setCurrentPngPage(page)}
        />
      )}
    </div>
  );
}
