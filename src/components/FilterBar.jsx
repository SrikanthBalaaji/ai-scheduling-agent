const today = new Date().toISOString().slice(0, 10)

export const FilterBar = ({
    filters,
    onChange,
    eventTypes,
}) => {
    return (
        <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-4">
            <label className="space-y-1 text-sm font-medium text-slate-700">
                Event Type
                <select
                    value={filters.type}
                    onChange={(e) => onChange('type', e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
                >
                    <option value="all">All</option>
                    {eventTypes.map((type) => (
                        <option key={type} value={type}>
                            {type}
                        </option>
                    ))}
                </select>
            </label>

            <label className="space-y-1 text-sm font-medium text-slate-700">
                Date
                <input
                    type="date"
                    min={today}
                    value={filters.date}
                    onChange={(e) => onChange('date', e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
                />
            </label>

            <label className="space-y-1 text-sm font-medium text-slate-700">
                Popularity
                <select
                    value={filters.popularity}
                    onChange={(e) => onChange('popularity', e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
                >
                    <option value="all">All</option>
                    <option value="high">High (150+)</option>
                    <option value="medium">Medium (100+)</option>
                    <option value="low">Low (&lt;100)</option>
                </select>
            </label>

            <label className="space-y-1 text-sm font-medium text-slate-700">
                Mode
                <select
                    value={filters.mode}
                    onChange={(e) => onChange('mode', e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
                >
                    <option value="all">All</option>
                    <option value="online">Online</option>
                    <option value="offline">Offline</option>
                </select>
            </label>
        </div>
    )
}
