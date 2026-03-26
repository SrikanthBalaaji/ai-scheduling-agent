import { CustomDropdown } from './CustomDropdown'

const today = new Date().toISOString().slice(0, 10)

const labelBaseClass = 'filter-label space-y-1.5 text-sm font-semibold text-slate-700'

const fieldBaseClass =
    'filter-field w-full rounded-xl border border-slate-300/90 bg-white/90 px-10 py-2.5 text-sm text-slate-800 shadow-sm transition-all duration-200 focus:border-amber-300 focus:outline-none focus:ring-2 focus:ring-amber-200/80'

// Icon components
const EventTypeIcon = (props) => (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
        <path d="M5 4h14v2H5zm0 7h14v2H5zm0 7h14v2H5z" />
    </svg>
)

const PopularityIcon = (props) => (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
        <path d="M12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61z" />
    </svg>
)

const ModeIcon = (props) => (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
        <path d="M4 6h16v10H4zm7 11h2v2h-2z" />
    </svg>
)

export const FilterBar = ({
    filters,
    onChange,
    eventTypes,
}) => {
    return (
        <div className="filter-bar grid gap-3 rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-amber-50/40 p-4 shadow-sm md:grid-cols-4">
            <label className={labelBaseClass}>
                <span className="block text-xs uppercase tracking-wide text-slate-500">Event Type</span>
                <CustomDropdown
                    options={[
                        { value: 'all', label: 'All' },
                        ...eventTypes.map((type) => ({ value: type, label: type })),
                    ]}
                    value={filters.type}
                    onChange={(value) => onChange('type', value)}
                    icon={EventTypeIcon}
                />
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
                <CustomDropdown
                    options={[
                        { value: 'all', label: 'All' },
                        { value: 'high', label: 'High (150+)' },
                        { value: 'medium', label: 'Medium (100+)' },
                        { value: 'low', label: 'Low (<100)' },
                    ]}
                    value={filters.popularity}
                    onChange={(value) => onChange('popularity', value)}
                    icon={PopularityIcon}
                />
            </label>

            <label className={labelBaseClass}>
                <span className="block text-xs uppercase tracking-wide text-slate-500">Mode</span>
                <CustomDropdown
                    options={[
                        { value: 'all', label: 'All' },
                        { value: 'online', label: 'Online' },
                        { value: 'offline', label: 'Offline' },
                    ]}
                    value={filters.mode}
                    onChange={(value) => onChange('mode', value)}
                    icon={ModeIcon}
                />
            </label>
        </div>
    )
}
