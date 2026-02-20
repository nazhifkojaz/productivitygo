import { Swords, Mail, Loader } from 'lucide-react';

export interface BattleStationProps {
    searchEmail: string;
    setSearchEmail: (email: string) => void;
    startDate: string | null;
    setStartDate: (date: string | null) => void;
    duration: number;
    setDuration: (duration: number) => void;
    dateOptions: Date[];
    handleInvite: () => void;
    isSending: boolean;
    isValid: boolean;
}

export function BattleStation({ searchEmail, setSearchEmail, startDate, setStartDate, duration, setDuration, dateOptions, handleInvite, isSending, isValid }: BattleStationProps) {
    return (
        <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
            <div className="bg-[#E63946] text-white p-4 border-b-4 border-black">
                <h2 className="text-xl font-black uppercase flex items-center gap-2">
                    <Swords className="w-6 h-6" /> Battle Station
                </h2>
                <p className="text-sm font-mono opacity-80">[ INITIATE PVP COMBAT ]</p>
            </div>

            <div className="p-6 grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                    <div>
                        <label className="block text-xs font-black uppercase font-mono mb-2">
                            [ START DATE ]
                        </label>
                        <select
                            className="w-full border-3 border-black p-3 font-bold bg-white focus:outline-none focus:shadow-[4px_4px_0_0_#E63946]"
                            value={startDate || ''}
                            onChange={(e) => setStartDate(e.target.value)}
                        >
                            <option value="">Select Date</option>
                            {dateOptions.map(date => (
                                <option key={date.toISOString()} value={date.toISOString().split('T')[0]}>
                                    {date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="pt-3">
                        <label className="block text-xs font-black uppercase font-mono mb-2">
                            [ DURATION ]
                        </label>
                        <div className="flex gap-2">
                            {[3, 4, 5].map(d => (
                                <button
                                    key={d}
                                    onClick={() => setDuration(d)}
                                    className={`flex-1 border-3 border-black p-3 font-black transition-all ${
                                        duration === d
                                            ? 'bg-[#E63946] text-white shadow-[3px_3px_0_0_#000]'
                                            : 'bg-white hover:bg-gray-100'
                                    }`}
                                >
                                    {d}D
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="space-y-11">
                    <div>
                        <label className="block text-xs font-black uppercase font-mono mb-2">
                            [ CHALLENGE EMAIL ]
                        </label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                            <input
                                type="email"
                                placeholder="rival@productivity.go"
                                className="w-full border-3 border-black p-3 pl-10 font-bold focus:outline-none focus:shadow-[4px_4px_0_0_#E63946]"
                                value={searchEmail}
                                onChange={(e) => setSearchEmail(e.target.value)}
                            />
                        </div>
                    </div>

                    <button
                        onClick={handleInvite}
                        disabled={isSending || !isValid}
                        className={`w-full border-3 border-black p-3 font-black uppercase text-white shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2 ${
                            isSending || !isValid
                                ? 'bg-gray-300 cursor-not-allowed'
                                : 'bg-[#E63946]'
                        }`}
                    >
                        {isSending ? <Loader className="w-4 h-4 animate-spin" /> : <Swords className="w-5 h-5" />}
                        {isSending ? 'SENDING...' : 'SEND CHALLENGE'}
                    </button>
                </div>
            </div>
        </div>
    );
}
