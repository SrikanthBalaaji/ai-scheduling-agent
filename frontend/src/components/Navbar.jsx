import { useAppContext } from '../context/AppContext'
import { ThemeToggle } from './ThemeToggle'
import { AnimatedNav } from './AnimatedNav'

export const Navbar = () => {
    const { role, user, logout } = useAppContext()

    if (!role) return null

    const navLinks = [
        { path: '/billboard', label: 'Home' },
        { path: '/calendar', label: 'My Calendar' },
        { path: '/chat', label: 'Chat Assistant' },
        ...(role === 'club' ? [{ path: '/club', label: 'Club Panel' }] : []),
    ]

    return (
        <header className="sticky top-0 z-20 border-b border-amber-200/80 bg-white/90 backdrop-blur transition-colors duration-300">
            <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Student AI Planner
                    </p>
                    <p className="text-sm text-slate-700">{user?.name}</p>
                </div>

                <nav>
                    <AnimatedNav links={navLinks} />
                </nav>

                <div className="flex items-center gap-2">
                    <ThemeToggle />
                    <button
                        onClick={logout}
                        className="rounded-full bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition-all duration-300 hover:bg-rose-700"
                    >
                        Logout
                    </button>
                </div>
            </div>
        </header>
    )
}
