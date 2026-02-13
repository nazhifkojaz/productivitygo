import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Target, Zap, Trophy, Coffee, Github, Twitter, ArrowRight } from 'lucide-react';

export default function Design1() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-landing-coral" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
      {/* Hero Section */}
      <section className="min-h-screen relative overflow-hidden flex items-center justify-center">
        {/* Geometric Background */}
        <div className="absolute inset-0">
          <div className="absolute top-10 left-5 w-40 sm:w-56 md:w-72 lg:w-96 h-40 sm:h-56 md:h-72 lg:h-96 bg-landing-teal border-4 sm:border-6 md:border-8 border-black rotate-12 -z-10" />
          <div className="absolute bottom-10 right-5 w-32 sm:w-48 md:w-64 lg:w-80 h-32 sm:h-48 md:h-64 lg:h-80 bg-landing-yellow border-4 sm:border-6 md:border-8 border-black -rotate-6 -z-10" />
          <div className="hidden sm:block absolute top-20 right-10 w-24 sm:w-40 md:w-52 lg:w-64 h-24 sm:h-40 md:h-52 lg:h-64 bg-landing-mint border-4 sm:border-6 md:border-8 border-black rotate-45 -z-10" />
          <div className="absolute bottom-20 left-5 w-28 sm:w-44 md:w-60 lg:w-72 h-28 sm:h-44 md:h-60 lg:h-72 bg-landing-salmon border-4 sm:border-6 md:border-8 border-black -rotate-12 -z-10" />
        </div>

        <div className="max-w-6xl mx-auto px-4 sm:px-6 relative z-10">
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-9xl font-bold text-black mb-4 sm:mb-6 tracking-tight sm:tracking-tighter">
              PRODUCTIVITY<span className="text-white">GO</span>
            </h1>
            <p className="text-lg sm:text-xl md:text-2xl lg:text-3xl text-black mb-8 sm:mb-10 md:mb-12 max-w-2xl sm:max-w-3xl mx-auto leading-relaxed">
              Turn your to-do list into an epic adventure
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/login')}
              className="bg-black text-white text-base sm:text-lg md:text-xl font-bold px-6 sm:px-8 md:px-10 lg:px-12 py-3 sm:py-4 md:py-5 border-4 border-black hover:bg-white hover:text-black transition-all"
            >
              START YOUR QUEST <ArrowRight className="inline ml-2" />
            </motion.button>
          </motion.div>
        </div>

        {/* Scroll Indicator */}
        <div className="hidden sm:block absolute bottom-6 sm:bottom-8 md:bottom-10 left-1/2 -translate-x-1/2 animate-bounce" aria-hidden="true">
          <div className="w-8 h-12 border-4 border-black rounded-full flex items-start justify-center p-2 bg-landing-yellow">
            <div className="w-2 h-2 bg-black rounded-full" />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 sm:py-20 md:py-24 px-4 sm:px-6 bg-landing-yellow">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl sm:text-5xl font-bold text-black mb-8 sm:mb-12 md:mb-16 text-center tracking-tighter">
            LEVEL UP YOUR LIFE
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 md:gap-8">
            {[
              { icon: Target, title: "SLAY MONSTERS", desc: "Defeat task monsters by completing your daily goals", bgColor: "var(--color-landing-coral)" },
              { icon: Zap, title: "BATTLE RIVALS", desc: "Challenge friends to productivity duels", bgColor: "var(--color-landing-teal)" },
              { icon: Trophy, title: "EARN REWARDS", desc: "Unlock achievements and level up", bgColor: "var(--color-landing-mint)" }
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ y: 50, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                transition={{ delay: i * 0.2 }}
                viewport={{ once: true }}
                className="bg-white border-4 border-black p-4 sm:p-6 md:p-8 hover:shadow-[8px_8px_0_0_#000] transition-shadow"
              >
                <div
                  className="w-16 h-16 sm:w-18 sm:h-18 md:w-20 md:h-20 border-4 border-black flex items-center justify-center mb-4 sm:mb-6"
                  style={{ backgroundColor: feature.bgColor }}
                >
                  <feature.icon className="w-8 h-8 sm:w-9 sm:h-9 md:w-10 md:h-10 text-black" />
                </div>
                <h3 className="text-xl sm:text-2xl font-bold text-black mb-3 sm:mb-4 tracking-tighter">{feature.title}</h3>
                <p className="text-base sm:text-lg text-black/80">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* About Section */}
      <section className="py-16 sm:py-20 md:py-24 px-4 sm:px-6 bg-landing-teal relative overflow-hidden">
        <div className="absolute top-0 right-0 w-40 sm:w-64 md:w-80 lg:w-96 h-40 sm:h-64 md:h-80 lg:h-96 bg-landing-coral border-4 sm:border-6 md:border-8 border-black rotate-45 translate-x-1/2 sm:translate-x-48 -translate-y-1/2 sm:-translate-y-48 -z-10" />

        <div className="max-w-4xl mx-auto relative z-10">
          <motion.div
            initial={{ x: -100, opacity: 0 }}
            whileInView={{ x: 0, opacity: 1 }}
            viewport={{ once: true }}
            className="bg-white border-4 border-black p-6 sm:p-8 md:p-12 shadow-[8px_8px_0_0_#000] sm:shadow-[10px_10px_0_0_#000] md:shadow-[12px_12px_0_0_#000]"
          >
            <div className="flex flex-col md:flex-row gap-6 md:gap-8 items-center">
              <div className="w-32 h-32 sm:w-40 sm:h-40 md:w-48 md:h-48 bg-landing-yellow border-4 border-black flex items-center justify-center flex-shrink-0">
                <div className="text-center">
                  <div className="text-4xl sm:text-5xl md:text-6xl font-bold text-black">99</div>
                  <div className="text-xs sm:text-sm font-bold text-black">LVL</div>
                </div>
              </div>
              <div className="flex-1">
                <h2 className="text-3xl sm:text-4xl font-bold text-black mb-4 sm:mb-6 tracking-tighter">ABOUT THE CREATOR</h2>
                <p className="text-base sm:text-lg md:text-xl text-black/90 mb-4 sm:mb-6 leading-relaxed">
                  Hey there! I'm the indie developer behind ProductivityGO. I built this platform because I believe productivity shouldn't be boring—it should be an adventure!
                </p>
                <div className="flex flex-wrap gap-2 sm:gap-3">
                  {["JavaScript", "React", "Python", "FastAPI", "Supabase"].map((skill) => (
                    <span key={skill} className="bg-black text-white px-3 sm:px-4 py-1 sm:py-2 text-xs sm:text-sm font-bold">
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
      <section className="py-16 sm:py-20 md:py-24 px-4 sm:px-6 bg-landing-mint">
        <div className="max-w-2xl mx-auto text-center">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            whileInView={{ scale: 1, opacity: 1 }}
            viewport={{ once: true }}
            className="bg-white border-4 border-black p-6 sm:p-8 md:p-12 shadow-[8px_8px_0_0_#000] sm:shadow-[12px_12px_0_0_#000]"
          >
            <Coffee className="w-14 h-14 sm:w-16 sm:h-16 md:w-20 md:h-20 mx-auto mb-4 sm:mb-6 text-landing-coral" />
            <h2 className="text-3xl sm:text-4xl font-bold text-black mb-4 sm:mb-6 tracking-tighter">SUPPORT THE QUEST</h2>
            <p className="text-base sm:text-lg md:text-xl text-black/90 mb-6 sm:mb-8">
              Love ProductivityGO? Buy me a coffee to keep the adventure going!
            </p>
            <a
              href="https://www.buymeacoffee.com/yourusername"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block bg-landing-coral text-white text-base sm:text-lg md:text-xl font-bold px-6 sm:px-8 md:px-10 py-3 sm:py-4 md:py-5 border-4 border-black hover:bg-black hover:text-white transition-all"
            >
              BUY ME A COFFEE <Coffee className="inline ml-2" />
            </a>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black text-white py-8 sm:py-10 md:py-12 px-4 sm:px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 sm:gap-6">
          <div className="text-xl sm:text-2xl font-bold">PRODUCTIVITYGO</div>
          <div className="flex items-center gap-4 sm:gap-6">
            <a href="#" className="hover:text-landing-yellow transition-colors" aria-label="GitHub">
              <Github className="w-6 h-6 sm:w-7 sm:h-7 md:w-8 md:h-8" />
            </a>
            <a href="#" className="hover:text-landing-yellow transition-colors" aria-label="Twitter">
              <Twitter className="w-6 h-6 sm:w-7 sm:h-7 md:w-8 md:h-8" />
            </a>
          </div>
          <div className="text-base sm:text-lg">© {new Date().getFullYear()} ALL RIGHTS RESERVED</div>
        </div>
      </footer>
    </div>
  );
}
