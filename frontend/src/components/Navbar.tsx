'use client';
import { BoltIcon, ChartBarIcon } from '@heroicons/react/24/solid';

export default function Navbar() {
  return (
    <nav className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between shadow-lg">
      <div className="flex items-center gap-3">
        <div className="bg-blue-500 p-2 rounded-lg">
          <BoltIcon className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-lg leading-none">Decision Intelligence</h1>
          <p className="text-slate-400 text-xs">Platform v1.0</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-slate-300 text-sm">
          <ChartBarIcon className="h-4 w-4 text-green-400" />
          <span className="text-green-400 font-medium">Live</span>
        </div>
        <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-sm font-bold">
          A
        </div>
      </div>
    </nav>
  );
}
