import { NavLink } from 'react-router-dom'
import { useAppContext } from '../context/AppContext'
import { ThemeToggle } from './ThemeToggle'

const linkClass = ({ isActive }) =>
    `nav-link rounded-full px-4 py-2 text-sm font-semibold transition-all duration-300 ${isActive
        ? 'nav-link-active bg-amber-400 text-slate-950 ring-2 ring-amber-300 shadow-[0_0_0_2px_rgba(251,191,36,0.25)]'
        : 'text-slate-700'
    }`

export const Navbar = () => {
    const { role, user, logout } = useAppContext()

    if (!role) return null

    return (
        <header className="sticky top-0 z-20 border-b border-amber-200/80 bg-white/90 backdrop-blur">
            <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Student AI Planner
                    </p>
                    <p className="text-sm text-slate-700">{user?.name}</p>
                </div>

                <nav className="flex flex-wrap items-center gap-2">
                    <NavLink to="/billboard" className={linkClass}>
                        Home
                    </NavLink>
                    <NavLink to="/calendar" className={linkClass}>
                        My Calendar
                    </NavLink>
                    <NavLink to="/chat" className={linkClass}>
                        Chat Assistant
                    </NavLink>
                    {role === 'club' && (
                        <NavLink to="/club" className={linkClass}>
                            Club Panel
                        </NavLink>
                    )}
                </nav>

                <div className="flex items-center gap-2">
                    <ThemeToggle />
                    <button
                        onClick={logout}
                        className="rounded-full bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-700"
                    >
                        Logout
                    </button>
                </div>
            </div>
        </header>
    )
}
