import { useEffect, useState } from 'react';
import { BookOpen } from 'lucide-react';

export default function WelcomeScreen({ onDismiss }) {
  const [isExiting, setIsExiting] = useState(false);

  const proceed = () => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss();
    }, 500);
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        proceed();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onDismiss]);

  return (
    <div
      onClick={proceed}
      className={`fixed inset-0 z-[100] flex flex-col items-center justify-center bg-green-600 text-white transition-opacity duration-500 ease-in-out cursor-pointer ${
        isExiting ? 'opacity-0 pointer-events-none' : 'opacity-100'
      }`}
    >
      <div className="flex flex-col items-center animate-in fade-in slide-in-from-bottom-4 duration-1000 ease-out">
        <div className="p-4 bg-white/10 rounded-2xl border border-white/20 mb-6 backdrop-blur-md">
          <BookOpen className="w-16 h-16 text-white" />
        </div>
        <h1 className="text-4xl sm:text-6xl font-black mb-4 tracking-tight text-center">
          Welcome to BookInsight Engine
        </h1>
        <p className="text-green-100 text-lg sm:text-xl font-medium mb-12 text-center max-w-lg">
          Your portal to deep, AI-powered book intelligence and insights.
        </p>

        <div className="flex items-center gap-3 animate-pulse text-white/80 font-semibold tracking-wide uppercase text-sm mt-8 p-3 rounded-xl border border-white/20 bg-black/10 backdrop-blur-sm">
          <span>Press</span>
          <kbd className="px-2 py-1 bg-white text-green-700 rounded-md shadow-sm font-sans font-bold">Tab</kbd>
          <span>or</span>
          <kbd className="px-2 py-1 bg-white text-green-700 rounded-md shadow-sm font-sans font-bold">Enter</kbd>
          <span>to continue</span>
        </div>
      </div>
    </div>
  );
}
