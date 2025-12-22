import { useState, useRef, useEffect } from 'react';
import { Button } from './Button';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

interface ChatProps {
  selectedBook?: { pdf_path: string; book_name?: string } | null;
}

export function Chat({ selectedBook }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Chat Header */}
      <div className="px-6 py-4 shadow-sm bg-background-off">
        <h2 className="text-xl font-semibold text-text-primary">
          {selectedBook ? `Chat: ${selectedBook.book_name || selectedBook.pdf_path.split('/').pop()}` : 'Chat'}
        </h2>
        {!selectedBook && (
          <p className="text-sm text-text-secondary mt-1">Select a book to start chatting</p>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
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

      {/* Input Area */}
      <div className="px-6 py-4 shadow-lg bg-background-off">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={selectedBook ? "Type your message..." : "Select a book to start chatting"}
            disabled={!selectedBook || isLoading}
            className="flex-1 px-4 py-3 border-2 border-border rounded-lg text-base focus:border-primary focus:outline-none disabled:bg-background-subtle disabled:cursor-not-allowed disabled:text-text-light shadow-sm"
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
    </div>
  );
}
