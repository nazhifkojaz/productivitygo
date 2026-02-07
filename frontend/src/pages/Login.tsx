import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { supabase } from '../lib/supabase';

export default function Login() {
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleEmailLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        const { error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });

        if (error) {
            setError(error.message);
            setLoading(false);
        } else {
            navigate('/lobby');
        }
    };

    const handleGoogleLogin = async () => {
        const { error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${window.location.origin}${import.meta.env.BASE_URL}lobby`,
            },
        });
        if (error) setError(error.message);
    };

    return (
        <div className="min-h-screen bg-[#E8E4D9] neo-grid-bg flex flex-col items-center justify-center p-4">
            {/* Marquee banner */}
            <div className="fixed top-0 left-0 right-0 bg-black text-white py-2 overflow-hidden z-40">
                <div className="neo-marquee whitespace-nowrap">
                    <span className="mx-8">⚔️ PRODUCTIVITY BATTLE ARENA ⚔️</span>
                    <span className="mx-8">🏆 COMPETE WITH RIVALS 🏆</span>
                    <span className="mx-8">⚡ COMPLETE TASKS ⚡</span>
                    <span className="mx-8">🎯 EARN XP 🎯</span>
                    <span className="mx-8">⚔️ PRODUCTIVITY BATTLE ARENA ⚔️</span>
                    <span className="mx-8">🏆 COMPETE WITH RIVALS 🏆</span>
                    <span className="mx-8">⚡ COMPLETE TASKS ⚡</span>
                    <span className="mx-8">🎯 EARN XP 🎯</span>
                </div>
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md"
            >
                {/* Logo */}
                <div className="text-center mb-8 mt-20">
                    <div className="inline-block bg-white border-4 border-black px-8 py-6 shadow-[6px_6px_0_0_#000] neo-rotate-1">
                        <h1 className="text-5xl font-black tracking-tighter">
                            <span className="text-[#E63946]">P</span>RODUCTIVITY<span className="text-[#E63946]">GO</span>
                        </h1>
                        <p className="mt-2 font-mono text-xs font-bold text-gray-600">
                            [ GAMIFIED TASK BATTLE SYSTEM ]
                        </p>
                    </div>
                </div>

                {/* Login card */}
                <div className="bg-white border-4 border-black shadow-[8px_8px_0_0_#000] p-8 relative">
                    {/* Decorative badge */}
                    <div className="absolute -top-4 -right-4 bg-[#F4A261] border-3 border-black px-4 py-1 transform rotate-2 shadow-[3px_3px_0_0_#000]">
                        <span className="text-sm font-black">V.1.0</span>
                    </div>

                    <h2 className="text-2xl font-black mb-2 uppercase">Enter Arena</h2>
                    <p className="text-sm font-bold text-gray-500 mb-6 font-mono">
                        // authenticate to continue
                    </p>

                    {error && (
                        <div className="bg-red-100 border-3 border-red-500 text-red-700 p-3 mb-4 font-bold text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleEmailLogin} className="space-y-4">
                        <div>
                            <label htmlFor="email" className="block text-xs font-black uppercase mb-2 font-mono">
                                [ EMAIL ]
                            </label>
                            <input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full border-3 border-black p-3 font-bold focus:outline-none focus:shadow-[4px_4px_0_0_#457B9D] transition-all"
                                placeholder="warrior@productivity.go"
                                required
                            />
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-xs font-black uppercase mb-2 font-mono">
                                [ PASSWORD ]
                            </label>
                            <input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full border-3 border-black p-3 font-bold focus:outline-none focus:shadow-[4px_4px_0_0_#457B9D] transition-all"
                                placeholder="••••••••"
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-[#E63946] border-3 border-black p-4 font-black uppercase text-white shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all disabled:opacity-50"
                        >
                            {loading ? '[ AUTHENTICATING... ]' : '[ ENTER BATTLE ]'}
                        </button>
                    </form>

                    <div className="relative my-6">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t-2 border-dashed border-black"></div>
                        </div>
                        <div className="relative flex justify-center">
                            <span className="bg-white px-4 text-xs font-black uppercase font-mono">OR</span>
                        </div>
                    </div>

                    <button
                        onClick={handleGoogleLogin}
                        disabled={loading}
                        className="w-full bg-white border-3 border-black p-4 font-bold shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-3 disabled:opacity-50"
                    >
                        <svg className="w-5 h-5" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                        <span>CONTINUE WITH GOOGLE</span>
                    </button>

                    <div className="mt-6 text-center">
                        <p className="text-xs font-mono text-gray-500">
                            new challenger? <a href="#" className="text-[#E63946] font-bold underline">create account</a>
                        </p>
                    </div>
                </div>

                {/* Footer text */}
                <div className="text-center mt-8">
                    <p className="text-xs font-mono font-bold text-gray-500">
                        [© 2025 PRODUCTIVITYGO - ALL RIGHTS RESERVED]
                    </p>
                </div>
            </motion.div>
        </div>
    );
}
