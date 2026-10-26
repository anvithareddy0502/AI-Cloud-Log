import React from 'react';

export default function Card({ children, className = '', hover = false, onClick }) {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-lg border border-slate-200/90 shadow-sm ${
        hover ? 'transition-all duration-150 hover:border-slate-300 hover:shadow cursor-pointer' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
}
