import { BooksPage } from './pages/BooksPage';

function App() {
  return (
    <div className="min-h-screen flex flex-col bg-background-off">
      <main className="flex-1 overflow-hidden">
        <BooksPage />
      </main>
    </div>
  );
}

export default App;
