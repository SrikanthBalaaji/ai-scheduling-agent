import { useMemo, useState } from 'react'
import { Modal } from '../components/Modal'
import { useAppContext } from '../context/AppContext'

const categoryColor = {
    academic: 'bg-blue-100 text-blue-900 ring-blue-200',
    events: 'bg-emerald-100 text-emerald-900 ring-emerald-200',
    exams: 'bg-rose-100 text-rose-900 ring-rose-200',
}

const toDayKey = (dateTime) => new Date(dateTime).toISOString().slice(0, 10)

const humanDate = (dateTime) =>
    new Date(dateTime).toLocaleString([], {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
    })

export const CalendarPage = () => {
    const { calendarEntries } = useAppContext()
    const [viewMode, setViewMode] = useState('daily')
    const [selected, setSelected] = useState(null)
    const [selectedDay, setSelectedDay] = useState(() => new Date().toISOString().slice(0, 10))

    const sorted = useMemo(
        () => [...calendarEntries].sort((a, b) => new Date(a.dateTime) - new Date(b.dateTime)),
        [calendarEntries],
    )

    const upcoming = useMemo(
        () => sorted.filter((entry) => new Date(entry.dateTime).getTime() >= Date.now()).slice(0, 8),
        [sorted],
    )

    const groupedByDay = useMemo(() => {
        return sorted.reduce((acc, entry) => {
            const key = toDayKey(entry.dateTime)
            acc[key] = acc[key] || []
            acc[key].push(entry)
            return acc
        }, {})
    }, [sorted])

    const freeBlocks = useMemo(
        () => [
            'Mon 5:00 PM - 7:00 PM',
            'Wed 8:00 AM - 10:00 AM',
            'Fri 4:00 PM - 6:00 PM',
            'Sun 10:00 AM - 1:00 PM',
        ],
        [],
    )

    const dayKeys = Object.keys(groupedByDay)
    const dailyEntries = groupedByDay[selectedDay] || []

    return (
        <main className="mx-auto w-full max-w-7xl space-y-6 px-4 py-6">
            <section className="rounded-3xl bg-[linear-gradient(135deg,#0f766e,#14b8a6,#a7f3d0)] p-6 shadow-lg">
                <h1 className="text-3xl font-black text-slate-900">My Calendar</h1>
                <p className="text-sm text-slate-800">Monthly, weekly, and daily snapshots with category colors.</p>
            </section>

            <section className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="space-x-2">
                    <button
                        onClick={() => setViewMode('daily')}
                        className={`rounded-full px-4 py-2 text-sm font-semibold ${viewMode === 'daily' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700'
                            }`}
                    >
                        Daily View
                    </button>
                    <button
                        onClick={() => setViewMode('weekly')}
                        className={`rounded-full px-4 py-2 text-sm font-semibold ${viewMode === 'weekly' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700'
                            }`}
                    >
                        Weekly View
                    </button>
                    <button
                        onClick={() => setViewMode('monthly')}
                        className={`rounded-full px-4 py-2 text-sm font-semibold ${viewMode === 'monthly' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700'
                            }`}
                    >
                        Monthly View
                    </button>
                </div>
            </section>

            <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
                <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                    <h2 className="text-xl font-black text-slate-900">
                        {viewMode === 'monthly'
                            ? 'Monthly Timeline'
                            : viewMode === 'weekly'
                                ? 'Weekly Timeline'
                                : 'Daily Timeline'}
                    </h2>

                    {viewMode === 'daily' && (
                        <div className="flex flex-wrap items-center gap-2 rounded-xl bg-slate-100 p-3">
                            <label className="text-sm font-semibold text-slate-700" htmlFor="calendar-day-picker">
                                Select Day
                            </label>
                            <input
                                id="calendar-day-picker"
                                type="date"
                                value={selectedDay}
                                onChange={(e) => setSelectedDay(e.target.value)}
                                className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700"
                            />
                        </div>
                    )}

                    {viewMode === 'daily' ? (
                        <div className="space-y-3">
                            {dailyEntries.length ? (
                                dailyEntries.map((entry) => (
                                    <button
                                        key={`daily-${entry.id}`}
                                        onClick={() => setSelected(entry)}
                                        className={`w-full rounded-lg px-3 py-3 text-left text-sm ring-1 ${categoryColor[entry.category]}`}
                                    >
                                        <p className="font-semibold">{entry.title}</p>
                                        <p className="text-xs">
                                            {new Date(entry.dateTime).toLocaleTimeString([], {
                                                hour: '2-digit',
                                                minute: '2-digit',
                                            })}{' '}
                                            | {entry.location}
                                        </p>
                                    </button>
                                ))
                            ) : (
                                <p className="text-sm text-slate-600">No entries for this day.</p>
                            )}
                        </div>
                    ) : (
                        <div className={viewMode === 'monthly' ? 'grid gap-3 md:grid-cols-2' : 'space-y-3'}>
                            {dayKeys.length ? (
                                dayKeys.map((day) => (
                                    <div key={day} className="rounded-xl border border-slate-200 p-3">
                                        <h3 className="text-sm font-bold text-slate-700">{day}</h3>
                                        <div className="mt-2 space-y-2">
                                            {groupedByDay[day].map((entry) => (
                                                <button
                                                    key={entry.id}
                                                    onClick={() => setSelected(entry)}
                                                    className={`w-full rounded-lg px-3 py-2 text-left text-sm ring-1 ${categoryColor[entry.category]}`}
                                                >
                                                    <p className="font-semibold">{entry.title}</p>
                                                    <p className="text-xs">{new Date(entry.dateTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <p className="text-sm text-slate-600">No entries in your calendar.</p>
                            )}
                        </div>
                    )}
                </div>

                <div className="space-y-4">
                    <aside className="calendar-side-card calendar-upcoming rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                        <h3 className="text-lg font-black text-slate-900">Upcoming Events</h3>
                        <ul className="mt-3 space-y-2 text-sm">
                            {upcoming.map((item) => (
                                <li key={`up-${item.id}`} className="calendar-upcoming-item rounded-lg bg-slate-100 px-3 py-2 text-slate-700">
                                    <p className="font-semibold">{item.title}</p>
                                    <p>{humanDate(item.dateTime)}</p>
                                </li>
                            ))}
                        </ul>
                    </aside>

                    <aside className="calendar-side-card calendar-freetime rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                        <h3 className="text-lg font-black text-slate-900">Free Time Blocks</h3>
                        <ul className="mt-3 space-y-2 text-sm text-slate-700">
                            {freeBlocks.map((slot) => (
                                <li key={slot} className="calendar-freetime-item rounded-lg bg-emerald-50 px-3 py-2 ring-1 ring-emerald-200">
                                    {slot}
                                </li>
                            ))}
                        </ul>
                    </aside>
                </div>
            </section>

            <Modal isOpen={Boolean(selected)} onClose={() => setSelected(null)} title="Event Details">
                {selected && (
                    <div className="space-y-2 text-sm text-slate-700">
                        <p>
                            <span className="font-semibold">Title:</span> {selected.title}
                        </p>
                        <p>
                            <span className="font-semibold">Category:</span> {selected.category}
                        </p>
                        <p>
                            <span className="font-semibold">When:</span> {humanDate(selected.dateTime)}
                        </p>
                        <p>
                            <span className="font-semibold">Location:</span> {selected.location}
                        </p>
                    </div>
                )}
            </Modal>
        </main>
    )
}
