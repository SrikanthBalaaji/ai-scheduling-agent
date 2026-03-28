import { useMemo, useState } from 'react'
import { EventCard } from '../components/EventCard'
import { FilterBar } from '../components/FilterBar'
import { NotificationTray } from '../components/NotificationTray'
import { useAppContext } from '../context/AppContext'

const isFutureEvent = (event) => new Date(event.dateTime).getTime() >= Date.now()

const passPopularity = (event, popularity) => {
    if (popularity === 'all') return true
    if (popularity === 'high') return event.registrations >= 150
    if (popularity === 'medium') return event.registrations >= 100
    return event.registrations < 100
}

export const BillboardPage = () => {
    const { events, user, registeredEventIds, role } = useAppContext()
    const [confirmation, setConfirmation] = useState('')
    const [filters, setFilters] = useState({
        type: 'all',
        date: '',
        popularity: 'all',
        mode: 'all',
    })

    const handleFilterChange = (key, value) => {
        setFilters((prev) => ({ ...prev, [key]: value }))
    }

    const allUpcoming = useMemo(
        () => events.filter((event) => isFutureEvent(event)).sort((a, b) => b.registrations - a.registrations),
        [events],
    )

    const eventTypes = useMemo(
        () => [...new Set(allUpcoming.map((event) => event.type))],
        [allUpcoming],
    )

    const filtered = useMemo(() => {
        return allUpcoming.filter((event) => {
            const matchesType = filters.type === 'all' || event.type === filters.type
            const matchesMode = filters.mode === 'all' || event.mode === filters.mode
            const matchesPopularity = passPopularity(event, filters.popularity)
            const matchesDate =
                !filters.date || event.dateTime.slice(0, 10) === filters.date

            return matchesType && matchesMode && matchesPopularity && matchesDate
        })
    }, [allUpcoming, filters])

    const recommended = useMemo(() => {
        if (!user?.interests?.length) return []
        return filtered
            .filter((event) => user.interests.includes(event.type))
            .slice(0, 4)
    }, [filtered, user])

    const trending = useMemo(() => filtered.slice(0, 4), [filtered])

    const handleRegisterClick = (event) => {
        if (!event.googleFormUrl) {
            setConfirmation('Google Form link is not available for this event yet.')
            setTimeout(() => setConfirmation(''), 2500)
            return
        }

        window.open(event.googleFormUrl, '_blank', 'noopener,noreferrer')
        setConfirmation('Opening registration form in a new tab.')
        setTimeout(() => setConfirmation(''), 2500)
    }

    return (
        <main className="mx-auto w-full max-w-7xl space-y-6 px-4 py-6">
            <section className="grid gap-4 md:grid-cols-[2fr_1fr]">
                <div className="rounded-3xl bg-[linear-gradient(135deg,#0f172a,#1e293b,#334155)] p-6 text-white shadow-xl">
                    <p className="text-xs uppercase tracking-[0.2em] text-amber-300">Campus Pulse</p>
                    <h1 className="mt-2 text-3xl font-black">Upcoming Opportunities</h1>
                    <p className="mt-1 text-sm text-slate-200">
                        Filter events, discover recommendations, and register in one click.
                    </p>
                    {confirmation && (
                        <p className="mt-4 rounded-xl bg-emerald-300/20 px-3 py-2 text-sm text-emerald-200 ring-1 ring-emerald-200/40">
                            {confirmation}
                        </p>
                    )}
                </div>
                <NotificationTray />
            </section>

            <FilterBar filters={filters} onChange={handleFilterChange} eventTypes={eventTypes} />

            <section className="space-y-3">
                <h2 className="text-xl font-black text-slate-900">All Events</h2>
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                    {filtered.map((event) => (
                        <EventCard
                            key={event.id}
                            event={event}
                            canRegister={role === 'student'}
                            isRegistered={registeredEventIds.has(event.id)}
                            onRegister={handleRegisterClick}
                        />
                    ))}
                </div>
            </section>

            <section className="space-y-3">
                <h2 className="text-xl font-black text-slate-900">Recommended Events</h2>
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                    {recommended.length ? (
                        recommended.map((event) => (
                            <EventCard
                                key={`rec-${event.id}`}
                                event={event}
                                canRegister={role === 'student'}
                                isRegistered={registeredEventIds.has(event.id)}
                                onRegister={handleRegisterClick}
                            />
                        ))
                    ) : (
                        <p className="text-sm text-slate-600">Pick interests to get better recommendations.</p>
                    )}
                </div>
            </section>

            <section className="space-y-3">
                <h2 className="text-xl font-black text-slate-900">Trending Events</h2>
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                    {trending.map((event) => (
                        <EventCard
                            key={`trend-${event.id}`}
                            event={event}
                            canRegister={role === 'student'}
                            isRegistered={registeredEventIds.has(event.id)}
                            onRegister={handleRegisterClick}
                        />
                    ))}
                </div>
            </section>
        </main>
    )
}
