import React from 'react';

interface TabButtonProps {
    children: React.ReactNode;
    active: boolean;
    onClick: () => void;
}

export default function TabButton({ children, active, onClick }: TabButtonProps) {
    return (
        <button
            onClick={onClick}
            className={`px-4 py-1 font-bold border-2 border-white ${active ? 'bg-neo-primary text-black' : 'bg-transparent text-white hover:bg-white/20'
                }`}
        >
            {children}
        </button>
    );
}
