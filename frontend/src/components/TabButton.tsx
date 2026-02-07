import React from 'react';

interface TabButtonProps {
    children: React.ReactNode;
    active: boolean;
    onClick: () => void;
}

/**
 * TabButton component for Design 1
 * Used in Lobby Social Hub with white border style on dark backgrounds
 */
export default function TabButton({ children, active, onClick }: TabButtonProps) {
    return (
        <button
            onClick={onClick}
            className={`px-3 py-1 text-xs font-black border-2 border-white transition-all ${
                active ? 'bg-white text-black' : 'text-white hover:bg-white/20'
            }`}
        >
            {children}
        </button>
    );
}
