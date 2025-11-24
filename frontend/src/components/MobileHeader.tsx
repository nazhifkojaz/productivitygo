import React from 'react';
import { User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function MobileHeader() {
    const navigate = useNavigate();

    return (
        <header className="fixed top-0 left-0 right-0 bg-neo-white border-b-3 border-black p-3 z-50 flex justify-between items-center md:hidden">
            <div className="font-black italic uppercase text-lg tracking-tighter">
                Productivity<span className="text-neo-primary">GO</span>
            </div>
            <button
                onClick={() => navigate('/profile')}
                className="bg-neo-accent border-2 border-black p-1 rounded-sm shadow-neo-sm active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all"
            >
                <User className="w-5 h-5" />
            </button>
        </header>
    );
}
