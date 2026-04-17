import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../lib/api';
import { Book, Star, ExternalLink, RefreshCw, Search, Sparkles, TrendingUp } from 'lucide-react';

export default function Dashboard() {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [sortBy, setSortBy] = useState('rating');

  const fetchBooks = async () => {
    try {
      setLoading(true);
      setError('');
      const res = await api.get('/books/');
      setBooks(res.data.data || []);
    } catch (err) {
      console.error(err);
      setError('Unable to load books. Check backend server and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleScrape = async () => {
    try {
      setScraping(true);
      setError('');
      await api.get('/scrape-books/');
      await fetchBooks();
    } catch (err) {
      console.error(err);
      setError('Scraping failed. Ensure Chrome/driver setup is available and retry.');
    } finally {
      setScraping(false);
    }
  };

  useEffect(() => {
    fetchBooks();
  }, []);

  const filteredBooks = books
    .filter((book) => {
      const text = `${book.title} ${book.author} ${book.description}`.toLowerCase();
      return text.includes(query.toLowerCase());
    })
    .sort((a, b) => {
      if (sortBy === 'title') {
        return (a.title || '').localeCompare(b.title || '');
      }
      return (b.rating || 0) - (a.rating || 0);
    });

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      <section className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5">
          <div>
            <p className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-green-600 font-semibold mb-3">
              <Sparkles className="w-4 h-4" />
              Intelligence Dashboard
            </p>
            <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-slate-900 mb-2">Explore Stylish Book Intelligence</h1>
            <p className="text-slate-600 max-w-2xl">
              Browse a rich, AI-powered library with smart filtering, deep insights, and a clean premium experience.
            </p>
          </div>
          <button
            onClick={handleScrape}
            disabled={scraping}
            className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl font-semibold transition-all duration-300 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-5 h-5 ${scraping ? 'animate-spin' : ''}`} />
            {scraping ? 'Scraping Data...' : 'Scrape Web Books'}
          </button>
        </div>
      </section>

      {error && <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      <div className="grid sm:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-4">
          <p className="text-xs uppercase font-semibold tracking-wide text-slate-500">Books</p>
          <p className="text-3xl font-black text-slate-900 mt-2">{books.length}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-4">
          <p className="text-xs uppercase font-semibold tracking-wide text-slate-500">Avg Rating</p>
          <p className="text-3xl font-black text-slate-900 mt-2">
            {books.length ? (books.reduce((s, b) => s + (b.rating || 0), 0) / books.length).toFixed(1) : "N/A"}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-4">
          <p className="text-xs uppercase font-semibold tracking-wide text-slate-500 inline-flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-600" />
            Top Rated
          </p>
          <p className="text-lg font-semibold text-slate-900 mt-2 line-clamp-1">{books[0]?.title || 'No data'}</p>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <div className="md:col-span-2 relative">
          <Search className="absolute left-3 top-3.5 w-4 h-4 text-slate-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by title, author, or description..."
            className="w-full rounded-xl bg-white border border-slate-200 shadow-sm pl-10 pr-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500 transition-all text-ellipsis"
          />
        </div>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="rounded-xl bg-white border border-slate-200 shadow-sm px-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500 transition-all font-medium"
        >
          <option value="rating">Sort: Highest Rating</option>
          <option value="title">Sort: Title A-Z</option>
        </select>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="animate-pulse bg-slate-200 rounded-2xl h-[300px] border border-slate-100 shadow-sm" />
          ))}
        </div>
      ) : filteredBooks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 px-4 text-center bg-white rounded-3xl border border-slate-200 border-dashed shadow-sm">
          <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-6">
            <Book className="w-10 h-10 text-slate-400" />
          </div>
          <h3 className="text-2xl font-bold text-slate-900 mb-3">No Books Found</h3>
          <p className="text-slate-500 mb-8 max-w-sm">Try changing filters or scrape additional books to expand your library.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredBooks.map((book) => (
            <div
              key={book.id}
              className="group relative flex flex-col bg-white border border-slate-200 rounded-2xl p-6 hover:border-green-400/50 transition-all duration-300 hover:shadow-lg shadow-sm"
            >
              <div className="relative z-10 flex-grow">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 bg-green-50 rounded-xl border border-green-100">
                    <Book className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="flex items-center gap-1.5 px-3 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded-full text-xs font-bold">
                    <Star className="w-3.5 h-3.5 fill-current text-amber-500" />
                    {book.rating || "N/A"}
                  </div>
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-1 line-clamp-2 leading-tight group-hover:text-green-700 transition-colors">{book.title}</h3>
                <p className="text-sm font-medium text-slate-600 mb-4">By {book.author || "Unknown"}</p>
                <p className="text-slate-500 text-sm line-clamp-3 mb-6 leading-relaxed">{book.description || "No description provided for this book."}</p>
              </div>
              <div className="relative z-10 mt-auto pt-4 border-t border-slate-100 flex items-center justify-between">
                <Link to={`/book/${book.id}`} className="text-green-600 text-sm font-semibold hover:text-green-800 transition-colors flex items-center gap-1">
                  View Details &rarr;
                </Link>
                {book.url && (
                  <a
                    href={book.url}
                    target="_blank"
                    rel="noreferrer"
                    className="p-2 text-slate-400 hover:text-slate-700 bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors border border-slate-100"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
