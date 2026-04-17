import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { ArrowLeft, Sparkles, AlertCircle, ExternalLink, Star } from 'lucide-react';

export default function BookDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [related, setRelated] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBookDetails = async () => {
      try {
        const [detailRes, summaryRes, relatedRes] = await Promise.all([
          api.get(`/books/${id}/`),
          api.get(`/summary/${id}/`),
          api.get(`/books/${id}/related/`),
        ]);

        setData({
          ...detailRes.data.data,
          summary: summaryRes.data.summary,
        });
        setRelated(relatedRes.data.data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchBookDetails();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="w-10 h-10 border-4 border-green-100 border-t-green-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-red-50 border border-red-200 p-6 rounded-2xl flex items-center gap-4 shadow-sm">
        <AlertCircle className="w-6 h-6 text-red-600" />
        <p className="text-red-800 font-medium">Unable to load details for this book.</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
      <button 
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-slate-600 hover:text-green-600 transition-colors mb-8 font-medium"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </button>

      <div className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-8 sm:p-12 shadow-sm">
        
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-50 border border-green-100 rounded-full text-green-700 text-sm font-semibold mb-6 shadow-sm">
            <Sparkles className="w-4 h-4" />
            AI Insight Generation
          </div>
          
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 mb-8 tracking-tight">
            {data.title}
          </h1>

          <div className="grid sm:grid-cols-2 gap-4 mb-6">
            <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 shadow-sm">
              <p className="text-xs uppercase text-slate-500 font-semibold mb-1">Author</p>
              <p className="text-slate-900 font-medium">{data.author || "Unknown"}</p>
            </div>
            <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 shadow-sm">
              <p className="text-xs uppercase text-slate-500 font-semibold mb-1">Rating</p>
              <p className="text-slate-900 font-medium inline-flex items-center gap-2">
                <Star className="w-4 h-4 text-amber-500 fill-current" />
                {data.rating ?? "N/A"}
              </p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 mb-6 shadow-sm text-slate-700">
            <h3 className="text-sm uppercase tracking-widest text-slate-500 font-bold mb-4">Description</h3>
            <p className="text-lg leading-relaxed">
              {data.description || "No description available."}
            </p>
            {data.url && (
              <a
                href={data.url}
                target="_blank"
                rel="noreferrer"
                className="mt-6 inline-flex items-center gap-2 text-green-600 hover:text-green-800 font-semibold"
              >
                Open source link
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>

          <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-sm text-slate-700">
            <h3 className="text-sm uppercase tracking-widest text-slate-500 font-bold mb-4">Book Summary</h3>
            <p className="text-lg leading-relaxed">
              {data.summary}
            </p>
          </div>

          {related.length > 0 && (
            <div className="bg-slate-50 rounded-2xl p-6 sm:p-8 border border-slate-200 mt-6 shadow-sm">
              <h3 className="text-sm uppercase tracking-widest text-slate-500 font-bold mb-4">Related Books</h3>
              <ul className="space-y-3 text-slate-700">
                {related.map((book, index) => (
                  <li key={`${book.title}-${index}`} className="rounded-xl bg-white border border-slate-200 p-3 shadow-sm font-medium">
                    <span className="text-green-600 font-bold mr-2">{index + 1}.</span> {book.title} - <span className="text-slate-500">{book.author}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
