import { BooksPage } from './pages/BooksPage';
import { ToastContainer } from './components/ToastContainer';
import { Guidance } from './components/Guidance';
import { DebugToolbox } from './components/DebugToolbox';

function App() {
  return (
    <div className="min-h-screen flex flex-col bg-background-off">
      <main className="flex-1 overflow-hidden">
        <BooksPage />
      </main>
      <ToastContainer />
      <Guidance />
      <DebugToolbox />
    </div>
  );
}

export default App;
