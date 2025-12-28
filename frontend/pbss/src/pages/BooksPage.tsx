import { BookEdit } from '../components/BookEdit';
import { BookView } from '../components/BookView';
import { Sidebar } from '../components/Sidebar';
import { Chat } from '../components/Chat';

export function BooksPage() {
  return (
    <div className="flex h-screen relative">
      {/* Sidebar */}
      <div className="w-80 flex-shrink-0 relative z-10">
        <Sidebar />
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 relative z-20">
        <Chat />
      </div>

      <BookEdit />
      <BookView />
    </div>
  );
}
