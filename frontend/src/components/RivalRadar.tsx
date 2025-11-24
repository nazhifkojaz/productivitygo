import React from 'react';
import { Shield, Lock } from 'lucide-react';

interface RivalRadarProps {
    battle: any;
}

export default function RivalRadar({ battle }: RivalRadarProps) {
    return (
        <aside className="w-full bg-neo-dark text-neo-white border-3 border-black p-6 shadow-neo relative">
            <div className="absolute top-0 right-0 bg-neo-accent text-black px-3 py-1 font-bold border-l-3 border-b-3 border-black text-sm">
                RIVAL DETECTED
            </div>
            <h2 className="text-xl font-black uppercase mb-4 flex items-center gap-2 text-neo-white">
                <Shield className="w-5 h-5" /> Rival Radar
            </h2>

            <div className="bg-gray-800 border-3 border-white p-4 mb-6 text-center">
                <div className="w-16 h-16 bg-gray-600 rounded-full mx-auto border-3 border-white mb-2 flex items-center justify-center">
                    <span className="text-2xl">😈</span>
                </div>
                <h3 className="text-lg font-bold text-white">{battle?.rival?.username || 'Rival'}</h3>
                <p className="text-neo-secondary font-bold text-xs">Level {battle?.rival?.level || '?'}</p>
            </div>

            <div className="space-y-4">
                <div className="flex justify-between items-center text-xs font-bold uppercase">
                    <span>Progress</span>
                    <span>{battle?.rival?.tasks_completed || 0}/{battle?.rival?.tasks_total || 0} Tasks</span>
                </div>
                <div className="w-full h-4 bg-gray-700 border-3 border-white relative">
                    <div
                        className="h-full bg-neo-primary transition-all duration-500"
                        style={{ width: `${battle?.rival?.tasks_total ? (battle.rival.tasks_completed / battle.rival.tasks_total) * 100 : 0}%` }}
                    ></div>
                </div>

                <div className="mt-4 p-3 bg-gray-800 border-2 border-dashed border-gray-500 text-center">
                    <Lock className="w-6 h-6 mx-auto text-gray-500 mb-1" />
                    <p className="text-gray-400 font-bold text-xs">
                        DATA ENCRYPTED
                    </p>
                </div>
            </div>
        </aside>
    );
}
