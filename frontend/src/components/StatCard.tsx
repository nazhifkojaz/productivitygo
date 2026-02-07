import type { ReactNode } from 'react';

interface StatCardProps {
    icon: ReactNode;
    label: string;
    value: number | string;
    color: string;
}

export default function StatCard({ icon, label, value, color }: StatCardProps) {
    return (
        <div className={`${color} border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center`}>
            <div className="flex items-center justify-center gap-2 mb-2 text-white">
                {icon}
                <span className="text-xs font-black uppercase">{label}</span>
            </div>
            <div className="text-2xl md:text-3xl font-black text-white">{value}</div>
        </div>
    );
}
