import React from 'react';
import { Sparkles, MessageSquare } from 'lucide-react';

export default function SuggestedPrompts({ onSelectPrompt }) {
  const prompts = [
    "What are today's critical errors?",
    "Which server has the most problems?",
    "Why did Server-03 fail?",
    "Are there any security threats?",
    "What caused the latest incident?"
  ];

  return (
    <div className="mb-4">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5">
        <Sparkles className="w-3.5 h-3.5 text-blue-500" />
        <span>Suggested Questions</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {prompts.map((q, idx) => (
          <button
            key={idx}
            onClick={() => onSelectPrompt(q)}
            className="text-xs bg-white hover:bg-blue-50/50 hover:border-blue-300 text-slate-700 hover:text-blue-700 font-medium px-3 py-1.5 rounded-full border border-slate-200 transition-all flex items-center gap-1.5 shadow-xs"
          >
            <MessageSquare className="w-3 h-3 text-slate-400" />
            <span>{q}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
