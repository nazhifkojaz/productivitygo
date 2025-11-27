import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
            navigate('/dashboard');
        }
    };

    const handleGoogleLogin = async () => {
        const { error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${window.location.origin}${import.meta.env.BASE_URL}dashboard`,
            },
        });
        if (error) setError(error.message);
    };

    return (
        <div className="min-h-screen bg-neo-bg flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-md bg-neo-white border-3 border-black shadow-neo p-8 relative">
                {/* Decorative Badge */}
                <div className="absolute -top-4 -right-4 bg-neo-accent border-3 border-black p-2 px-4 transform rotate-3 shadow-sm font-bold">
                    BETA ACCESS
                </div>

                <div className="flex justify-center mb-4">
                    <img src={`${import.meta.env.BASE_URL}logo.svg`} alt="ProductivityGo Logo" className="w-24 h-24" />
                </div>
                <h1 className="text-4xl font-black italic uppercase mb-2 text-center">
                    Productivity<span className="text-neo-primary">GO</span>
                </h1>
                <p className="text-center text-gray-600 font-bold mb-8">
                    Gamify your daily grind.
                </p>

                {error && (
                    <div className="bg-red-100 border-3 border-red-500 text-red-700 p-3 mb-4 font-bold text-sm">
                        {error}
                    </div>
                )}

                <button
                    onClick={handleGoogleLogin}
                    className="w-full bg-white border-3 border-black p-3 flex items-center justify-center gap-3 font-bold hover:bg-gray-50 transition-all shadow-neo-sm mb-6"
                >
                    <img src="https://www.svgrepo.com/show/475656/google-color.svg" className="w-6 h-6" alt="Google" />
                    Continue with Google
                </button>

                <div className="relative flex py-5 items-center">
                    <div className="flex-grow border-t-3 border-black"></div>
                    <span className="flex-shrink mx-4 text-gray-400 font-bold">OR</span>
                    <div className="flex-grow border-t-3 border-black"></div>
                </div>

                <form onSubmit={handleEmailLogin} className="space-y-4">
                    <div>
                        <label className="block font-black uppercase text-sm mb-1">Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full border-3 border-black p-3 font-bold focus:outline-none focus:shadow-neo-sm transition-all"
                            placeholder="warrior@example.com"
                        />
                    </div>
                    <div>
                        <label className="block font-black uppercase text-sm mb-1">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full border-3 border-black p-3 font-bold focus:outline-none focus:shadow-neo-sm transition-all"
                            placeholder="••••••••"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-neo-primary border-3 border-black p-3 font-black uppercase text-white shadow-neo hover:translate-x-1 hover:translate-y-1 hover:shadow-none transition-all disabled:opacity-50"
                    >
                        {loading ? 'Loading...' : 'Enter the Arena'}
                    </button>
                </form>
            </div>
        </div>
    );
}
