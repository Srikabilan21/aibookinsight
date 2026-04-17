import { Link, useLocation } from 'react-router-dom';
import { BookOpen, MessageSquare, LibraryBig } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 w-full bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          <Link to="/" className="flex items-center gap-3 group shrink-0">
            <div className="p-2.5 bg-green-50 rounded-xl border border-green-100 group-hover:border-green-200 transition-all duration-300">
              <LibraryBig className="w-6 h-6 text-green-600 group-hover:text-green-700" />
            </div>
            <span className="font-black text-xl sm:text-2xl tracking-tight text-slate-900">
              BookInsight Engine
            </span>
          </Link>

          <div className="flex items-center space-x-2">
            <Link
              to="/"
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 border ${
                isActive('/')
                  ? 'bg-slate-100 text-green-700 border-slate-200'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 border-transparent'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              Dashboard
            </Link>

            <Link
              to="/ask"
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 border ${
                isActive('/ask')
                  ? 'bg-slate-100 text-green-700 border-slate-200'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 border-transparent'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              Smart Q&A
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
