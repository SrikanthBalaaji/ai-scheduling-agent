const today = new Date().toISOString().slice(0, 10)

const fieldBaseClass =
    'filter-field w-full rounded-xl border border-slate-300/90 bg-white/90 px-10 py-2.5 text-sm text-slate-800 shadow-sm transition-all duration-200 focus:border-amber-300 focus:outline-none focus:ring-2 focus:ring-amber-200/80'

const labelBaseClass = 'filter-label space-y-1.5 text-sm font-semibold text-slate-700'

export const FilterBar = ({
    filters,
    onChange,
    eventTypes,
}) => {
    return (
        <div className="filter-bar grid gap-3 rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-amber-50/40 p-4 shadow-sm md:grid-cols-4">
            <label className={labelBaseClass}>
                <span className="block text-xs uppercase tracking-wide text-slate-500">Event Type</span>
                <div className="relative">
                    <svg
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                        className="filter-leading-icon pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                    >
                        <path fill="currentColor" d="M5 4h14v2H5zm0 7h14v2H5zm0 7h14v2H5z" />
                    </svg>
                    <select
                        value={filters.type}
                        onChange={(e) => onChange('type', e.target.value)}
                        className={`${fieldBaseClass} appearance-none`}
                    >
                        <option value="all">All</option>
                        {eventTypes.map((type) => (
                            <option key={type} value={type}>
                                {type}
                            </option>
                        ))}
                    </select>
                    <svg
                        viewBox="0 0 20 20"
                        aria-hidden="true"
                        className="filter-trailing-icon pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500"
                    >
                        <path fill="currentColor" d="M5.23 7.21 10 11.98l4.77-4.77 1.42 1.42L10 14.82 3.81 8.63z" />
                    </svg>
                </div>
            </label>

            <label className={labelBaseClass}>
                <span className="block text-xs uppercase tracking-wide text-slate-500">Date</span>
                <div className="relative">
                    <svg
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                        className="filter-leading-icon pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                    >
                        <path fill="currentColor" d="M19 4h-1V2h-2v2H8V2H6v2H5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2m0 15H5V10h14z" />
                    </svg>
                    <input
                        type="date"
                        min={today}
                        value={filters.date}
                        onChange={(e) => onChange('date', e.target.value)}
                        className={fieldBaseClass}
                    />
                </div>
            </label>

            <label className={labelBaseClass}>
                <span className="block text-xs uppercase tracking-wide text-slate-500">Popularity</span>
                <div className="relative">
                    <svg
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                        className="filter-leading-icon pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                    >
                        <path fill="currentColor" d="M12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61z" />
                    </svg>
                    <select
                        value={filters.popularity}
                        onChange={(e) => onChange('popularity', e.target.value)}
                        className={`${fieldBaseClass} appearance-none`}
                    >
                        <option value="all">All</option>
                        <option value="high">High (150+)</option>
                        <option value="medium">Medium (100+)</option>
                        <option value="low">Low (&lt;100)</option>
                    </select>
                    <svg
                        viewBox="0 0 20 20"
                        aria-hidden="true"
                        className="filter-trailing-icon pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500"
                    >
                        <path fill="currentColor" d="M5.23 7.21 10 11.98l4.77-4.77 1.42 1.42L10 14.82 3.81 8.63z" />
                    </svg>
                </div>
            </label>

            <label className={labelBaseClass}>
                <span className="block text-xs uppercase tracking-wide text-slate-500">Mode</span>
                <div className="relative">
                    <svg
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                        className="filter-leading-icon pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                    >
                        <path fill="currentColor" d="M4 6h16v10H4zm7 11h2v2h-2z" />
                    </svg>
                    <select
                        value={filters.mode}
                        onChange={(e) => onChange('mode', e.target.value)}
                        className={`${fieldBaseClass} appearance-none`}
                    >
                        <option value="all">All</option>
                        <option value="online">Online</option>
                        <option value="offline">Offline</option>
                    </select>
                    <svg
                        viewBox="0 0 20 20"
                        aria-hidden="true"
                        className="filter-trailing-icon pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500"
                    >
                        <path fill="currentColor" d="M5.23 7.21 10 11.98l4.77-4.77 1.42 1.42L10 14.82 3.81 8.63z" />
                    </svg>
                </div>
            </label>
        </div>
    )
}
