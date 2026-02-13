import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Target, Zap, Trophy, Coffee, Github, Twitter, ArrowRight } from 'lucide-react';

export default function Design1() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#FF6B6B]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
      {/* Hero Section */}
      <section className="min-h-screen relative overflow-hidden flex items-center justify-center">
        {/* Geometric Background */}
        <div className="absolute inset-0">
          <div className="absolute top-20 left-10 w-96 h-96 bg-[#4ECDC4] border-8 border-black rotate-12 -z-10" />
          <div className="absolute bottom-20 right-10 w-80 h-80 bg-[#FFE66D] border-8 border-black -rotate-6 -z-10" />
          <div className="absolute top-40 right-20 w-64 h-64 bg-[#95E1D3] border-8 border-black rotate-45 -z-10" />
          <div className="absolute bottom-40 left-20 w-72 h-72 bg-[#F38181] border-8 border-black -rotate-12 -z-10" />
        </div>

        <div className="max-w-6xl mx-auto px-6 relative z-10">
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-7xl md:text-9xl font-bold text-black mb-6 tracking-tighter">
              PRODUCTIVITY<span className="text-white">GO</span>
            </h1>
            <p className="text-2xl md:text-3xl text-black mb-12 max-w-3xl mx-auto leading-relaxed">
              Turn your to-do list into an epic adventure
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/login')}
              className="bg-black text-white text-xl font-bold px-12 py-5 border-4 border-black hover:bg-white hover:text-black transition-all"
            >
              START YOUR QUEST <ArrowRight className="inline ml-2" />
            </motion.button>
          </motion.div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 animate-bounce">
          <div className="w-8 h-12 border-4 border-black rounded-full flex items-start justify-center p-2 bg-[#FFE66D]">
            <div className="w-2 h-2 bg-black rounded-full" />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6 bg-[#FFE66D]">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-5xl font-bold text-black mb-16 text-center tracking-tighter">
            LEVEL UP YOUR LIFE
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: Target, title: "SLAY MONSTERS", desc: "Defeat task monsters by completing your daily goals", bgColor: "#FF6B6B" },
              { icon: Zap, title: "BATTLE RIVALS", desc: "Challenge friends to productivity duels", bgColor: "#4ECDC4" },
              { icon: Trophy, title: "EARN REWARDS", desc: "Unlock achievements and level up", bgColor: "#95E1D3" }
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ y: 50, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                transition={{ delay: i * 0.2 }}
                viewport={{ once: true }}
                className="bg-white border-4 border-black p-8 hover:shadow-[8px_8px_0_0_#000] transition-shadow"
              >
                <div
                  className="w-20 h-20 border-4 border-black flex items-center justify-center mb-6"
                  style={{ backgroundColor: feature.bgColor }}
                >
                  <feature.icon className="w-10 h-10 text-black" />
                </div>
                <h3 className="text-2xl font-bold text-black mb-4 tracking-tighter">{feature.title}</h3>
                <p className="text-lg text-black/80">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* About Section */}
      <section className="py-24 px-6 bg-[#4ECDC4] relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#FF6B6B] border-8 border-black rotate-45 translate-x-48 -translate-y-48 -z-10" />
        
        <div className="max-w-4xl mx-auto relative z-10">
          <motion.div
            initial={{ x: -100, opacity: 0 }}
            whileInView={{ x: 0, opacity: 1 }}
            viewport={{ once: true }}
            className="bg-white border-4 border-black p-12 shadow-[12px_12px_0_0_#000]"
          >
            <div className="flex flex-col md:flex-row gap-8 items-center">
              <div className="w-48 h-48 bg-[#FFE66D] border-4 border-black flex items-center justify-center flex-shrink-0">
                <div className="text-center">
                  <div className="text-6xl font-bold text-black">99</div>
                  <div className="text-sm font-bold text-black">LVL</div>
                </div>
              </div>
              <div className="flex-1">
                <h2 className="text-4xl font-bold text-black mb-6 tracking-tighter">ABOUT THE CREATOR</h2>
                <p className="text-xl text-black/90 mb-6 leading-relaxed">
                  Hey there! I'm the indie developer behind ProductivityGO. I built this platform because I believe productivity shouldn't be boring—it should be an adventure!
                </p>
                <div className="flex flex-wrap gap-3">
                  {["JavaScript", "React", "Python", "FastAPI", "Supabase"].map((skill) => (
                    <span key={skill} className="bg-black text-white px-4 py-2 text-sm font-bold">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Buy Me a Coffee Section */}
      <section className="py-24 px-6 bg-[#95E1D3]">
        <div className="max-w-2xl mx-auto text-center">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            whileInView={{ scale: 1, opacity: 1 }}
            viewport={{ once: true }}
            className="bg-white border-4 border-black p-12 shadow-[12px_12px_0_0_#000]"
          >
            <Coffee className="w-20 h-20 mx-auto mb-6 text-[#FF6B6B]" />
            <h2 className="text-4xl font-bold text-black mb-6 tracking-tighter">SUPPORT THE QUEST</h2>
            <p className="text-xl text-black/90 mb-8">
              Love ProductivityGO? Buy me a coffee to keep the adventure going!
            </p>
            <a
              href="https://www.buymeacoffee.com/yourusername"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block bg-[#FF6B6B] text-white text-xl font-bold px-10 py-5 border-4 border-black hover:bg-black hover:text-white transition-all"
            >
              BUY ME A COFFEE <Coffee className="inline ml-2" />
            </a>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black text-white py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="text-2xl font-bold">PRODUCTIVITYGO</div>
          <div className="flex items-center gap-6">
            <a href="#" className="hover:text-[#FFE66D] transition-colors">
              <Github className="w-8 h-8" />
            </a>
            <a href="#" className="hover:text-[#FFE66D] transition-colors">
              <Twitter className="w-8 h-8" />
            </a>
          </div>
          <div className="text-lg">© 2025 ALL RIGHTS RESERVED</div>
        </div>
      </footer>
    </div>
  );
}
