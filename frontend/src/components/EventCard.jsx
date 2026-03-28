import { useMemo } from 'react'

const toDateTime = (value) =>
    new Date(value).toLocaleString([], {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })

export const EventCard = ({ event, onRegister, isRegistered, canRegister = true }) => {
    const isPastEvent = useMemo(
        () => new Date(event.dateTime).getTime() < Date.now(),
        [event.dateTime],
    )
    const hasFormLink = Boolean(event.googleFormUrl)
    const isDisabled = !canRegister || isPastEvent || isRegistered || !hasFormLink

    return (
        <article className="event-card group relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm ring-1 ring-amber-100/60 transition-all duration-300">
            <img
                src={event.posterUrl}
                alt={event.title}
                className="h-40 w-full object-cover transition-transform duration-500 group-hover:scale-105"
                loading="lazy"
            />
            <div className="space-y-3 p-4">
                <div className="flex items-center justify-between gap-2">
                    <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-800">
                        {event.type}
                    </span>
                    <span className="text-xs font-semibold uppercase text-slate-500">
                        {event.mode}
                    </span>
                </div>

                <div>
                    <h3 className="line-clamp-2 text-lg font-bold text-slate-900 transition-colors duration-300 group-hover:text-amber-700">{event.title}</h3>
                    <p className="text-sm text-slate-600">{event.clubName}</p>
                </div>

                <dl className="space-y-1 text-sm text-slate-700">
                    <div className="flex justify-between gap-2">
                        <dt className="font-semibold">Date & Time</dt>
                        <dd className="text-right">{toDateTime(event.dateTime)}</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                        <dt className="font-semibold">Location</dt>
                        <dd className="text-right">{event.location}</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                        <dt className="font-semibold">Campus</dt>
                        <dd className="text-right">{event.campus}</dd>
                    </div>
                </dl>

                <a
                    href={hasFormLink ? event.googleFormUrl : '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(evt) => {
                        if (isDisabled) {
                            evt.preventDefault()
                            return
                        }
                        onRegister(event)
                    }}
                    aria-disabled={isDisabled}
                    className={`block w-full rounded-xl px-4 py-2 text-center text-sm font-semibold text-white transition ${isDisabled
                        ? 'cursor-not-allowed bg-slate-300'
                        : 'bg-emerald-600 hover:bg-emerald-700'
                        }`}
                >
                    {isRegistered
                        ? 'Registered'
                        : !hasFormLink
                            ? 'Form Not Available'
                            : isPastEvent
                                ? 'Event Closed'
                                : 'Register'}
                </a>
            </div>
        </article>
    )
}
