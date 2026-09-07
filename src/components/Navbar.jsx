import { useEffect, useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { LayoutDashboard, MapPinned, TrainFront, BrainCircuit, Menu, X, Gauge } from 'lucide-react';

const navItems = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'Trains', to: '/trains', icon: TrainFront },
  { label: 'Delay Intelligence', to: '/delay-intelligence', icon: BrainCircuit },
  { label: 'Simulation', to: '/simulation', icon: Gauge },
];

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [connection, setConnection] = useState('connecting');
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const handleConnection = (event) => setConnection(event.detail);
    window.addEventListener('arriva:connection', handleConnection);
    const timer = window.setInterval(() => setTime(new Date()), 1000);
    return () => {
      window.removeEventListener('arriva:connection', handleConnection);
      window.clearInterval(timer);
    };
  }, []);

  return (
    <header className="border-b border-slate-800/80 bg-[#07111f]/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link to="/dashboard" className="flex items-center gap-3" aria-label="ARRIVA dashboard">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-sky-400/30 bg-sky-400/10 text-sky-300">
            <MapPinned className="h-5 w-5" />
          </div>
          <div>
            <div className="text-lg font-bold tracking-[0.2em] text-slate-50">ARRIVA</div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400">AI railway intelligence</div>
          </div>
        </Link>

        <nav className="hidden items-center gap-2 md:flex" aria-label="Primary navigation">
          {navItems.map(({ label, to, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? 'bg-sky-400/15 text-sky-200 ring-1 ring-sky-400/30'
                    : 'text-slate-400 hover:bg-slate-800/70 hover:text-slate-100'
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-4 lg:flex">
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-slate-400">
            <span className={`live-pulse h-2 w-2 rounded-full ${connection === 'connected' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
            {connection === 'connected' ? 'System live' : 'Reconnecting'}
          </div>
          <time className="font-mono text-xs text-slate-500">{time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</time>
        </div>
        <button
          type="button"
          className="inline-flex items-center justify-center rounded-full border border-slate-200 p-2 text-slate-700 md:hidden dark:border-slate-700 dark:text-slate-200"
          aria-label="Toggle menu"
          onClick={() => setMobileOpen((open) => !open)}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {mobileOpen && (
        <nav className="border-t border-slate-200 px-4 py-3 dark:border-slate-800 md:hidden" aria-label="Mobile navigation">
          <div className="grid gap-2">
            {navItems.map(({ label, to, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `inline-flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium ${
                    isActive
                      ? 'bg-sky-400/15 text-sky-200'
                      : 'text-slate-400 hover:bg-slate-800'
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                {label}
              </NavLink>
            ))}
          </div>
        </nav>
      )}
    </header>
  );
}
