import { useAppContext } from '../context/AppContext'

export const ThemeToggle = () => {
    const { theme, toggleTheme } = useAppContext()
    const isDark = theme === 'dark'

    return (
        <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle dark mode"
            title="Toggle dark mode"
            className="theme-toggle group relative flex h-10 w-10 items-center justify-center rounded-full border border-amber-300 bg-white text-slate-800 shadow-sm transition hover:scale-105"
        >
            <span className="sr-only">Toggle dark mode</span>

            <svg
                viewBox="0 0 24 24"
                className={`theme-icon-sun absolute h-5 w-5 transition-all duration-500 ${isDark
                        ? 'translate-y-4 rotate-45 opacity-0'
                        : 'translate-y-0 rotate-0 opacity-100'
                    }`}
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
            >
                <circle cx="12" cy="12" r="4.5" />
                <path d="M12 2.5v2.4M12 19.1v2.4M4.93 4.93l1.7 1.7M17.37 17.37l1.7 1.7M2.5 12h2.4M19.1 12h2.4M4.93 19.07l1.7-1.7M17.37 6.63l1.7-1.7" />
            </svg>

            <svg
                viewBox="0 0 24 24"
                className={`theme-icon-moon absolute h-5 w-5 transition-all duration-500 ${isDark
                        ? 'translate-y-0 rotate-0 opacity-100'
                        : '-translate-y-4 -rotate-45 opacity-0'
                    }`}
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
            >
                <path d="M20 14.8A8.5 8.5 0 1 1 9.2 4a7 7 0 1 0 10.8 10.8Z" />
            </svg>
        </button>
    )
}
