import React from 'react';
import { Sword, Clock } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';

export default function MobileNav() {
    const navigate = useNavigate();
    const location = useLocation();

    const isActive = (path: string) => location.pathname === path;

    return (
        <nav className="fixed bottom-0 left-0 right-0 bg-neo-white border-t-3 border-black p-4 flex justify-around md:hidden z-50">
            <motion.button
                whileTap={{ scale: 0.9 }}
                whileHover={{ scale: 1.1 }}
                onClick={() => navigate('/dashboard')}
                className={`font-bold uppercase text-sm flex flex-col items-center gap-1 ${isActive('/dashboard') ? 'text-neo-primary' : 'text-gray-400 hover:text-neo-dark'}`}
            >
                <Sword className="w-5 h-5" /> Battle
            </motion.button>
            <motion.button
                whileTap={{ scale: 0.9 }}
                whileHover={{ scale: 1.1 }}
                onClick={() => navigate('/plan')}
                className={`font-bold uppercase text-sm flex flex-col items-center gap-1 ${isActive('/plan') ? 'text-neo-primary' : 'text-gray-400 hover:text-neo-dark'}`}
            >
                <Clock className="w-5 h-5" /> Plan
            </motion.button>
        </nav>
    );
}
