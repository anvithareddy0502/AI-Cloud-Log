import React from 'react';

export default function FilterDropdown({ label, value, options, onChange, icon: Icon }) {
  return (
    <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-md px-2.5 py-1.5 shadow-xs text-xs text-slate-700 hover:border-slate-300">
      {Icon && <Icon className="w-3.5 h-3.5 text-slate-400" />}
      {label && <span className="text-slate-400 font-medium">{label}:</span>}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-transparent border-none p-0 pr-2 focus:ring-0 text-slate-800 font-medium text-xs cursor-pointer focus:outline-none"
      >
        {options.map((opt) => {
          const val = typeof opt === 'string' ? opt : opt.value;
          const lbl = typeof opt === 'string' ? opt : opt.label;
          return (
            <option key={val} value={val}>
              {lbl}
            </option>
          );
        })}
      </select>
    </div>
  );
}
