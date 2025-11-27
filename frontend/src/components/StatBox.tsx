import React from 'react';

interface StatBoxProps {
    label: string;
    value: number | string;
    icon: React.ReactNode;
}

export default function StatBox({ label, value, icon }: StatBoxProps) {
    return (
        <div className="bg-gray-100 border-2 border-black p-2 text-center">
            <div className="flex justify-center mb-1 text-gray-600">{icon}</div>
            <div className="font-black text-lg">{value || 0}</div>
            <div className="text-[10px] uppercase font-bold text-gray-500">{label}</div>
        </div>
    );
}
