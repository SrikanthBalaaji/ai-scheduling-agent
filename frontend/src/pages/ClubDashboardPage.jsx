import { useMemo, useState } from 'react'
import { Modal } from '../components/Modal'
import { useAppContext } from '../context/AppContext'

const initialForm = {
    title: '',
    description: '',
    clubName: '',
    dateTime: '',
    location: '',
    mode: 'offline',
    type: 'workshop',
    posterUrl: '',
    googleFormUrl: '',
}

const toIsoFromDateOnly = (dateString, hour = 12, minute = 0) => {
    if (!dateString) return ''
    const [year, month, day] = dateString.split('-').map(Number)
    return new Date(year, month - 1, day, hour, minute, 0, 0).toISOString()
}

const deriveDeadline = (dateTime) => {
    if (!dateTime) return ''
    const deadline = new Date(dateTime)
    deadline.setDate(deadline.getDate() - 1)
    deadline.setHours(23, 59, 0, 0)
    return deadline.toISOString()
}

export const ClubDashboardPage = () => {
    const {
        events,
        createClubEvent,
        updateClubEvent,
        deleteClubEvent,
        duplicateClubEvent,
    } = useAppContext()

    const [form, setForm] = useState(initialForm)
    const [editing, setEditing] = useState(null)

    const clubEvents = useMemo(() => {
        if (!form.clubName.trim()) return events
        return events.filter(
            (event) => event.clubName.toLowerCase() === form.clubName.toLowerCase(),
        )
    }, [events, form.clubName])

    const handleCreate = async (e) => {
        e.preventDefault()
        await createClubEvent({
            ...form,
            registrationDeadline: deriveDeadline(form.dateTime),
            posterUrl:
                form.posterUrl ||
                'https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=1200&q=80',
        })
        setForm(initialForm)
    }

    const handlePosterUpload = (file) => {
        const reader = new FileReader()
        reader.onloadend = () => {
            setForm((prev) => ({ ...prev, posterUrl: reader.result }))
        }
        if (file) reader.readAsDataURL(file)
    }

    const handleEditPosterUpload = (file) => {
        const reader = new FileReader()
        reader.onloadend = () => {
            setEditing((prev) => ({ ...prev, posterUrl: reader.result }))
        }
        if (file) reader.readAsDataURL(file)
    }

    const handleEditSave = async () => {
        if (!editing) return
        await updateClubEvent(editing.id, {
            ...editing,
            registrationDeadline: editing.registrationDeadline || deriveDeadline(editing.dateTime),
        })
        setEditing(null)
    }

    return (
        <main className="mx-auto w-full max-w-7xl space-y-6 px-4 py-6">
            <section className="rounded-3xl bg-[linear-gradient(135deg,#7f1d1d,#b91c1c,#fecaca)] p-6 shadow-lg">
                <h1 className="text-3xl font-black text-white">Club Dashboard</h1>
                <p className="mt-1 text-sm text-rose-100">
                    Create, edit, duplicate, and track registrations for club events.
                </p>
            </section>

            <section className="grid gap-6 lg:grid-cols-[1.1fr_2fr]">
                <form
                    onSubmit={handleCreate}
                    className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
                >
                    <h2 className="text-xl font-black text-slate-900">Create Event</h2>

                    <input
                        required
                        value={form.title}
                        onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
                        placeholder="Title"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    />

                    <textarea
                        required
                        value={form.description}
                        onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
                        placeholder="Description"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    />

                    <input
                        required
                        value={form.clubName}
                        onChange={(e) => setForm((prev) => ({ ...prev, clubName: e.target.value }))}
                        placeholder="Club Name"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    />

                    <input
                        required
                        type="date"
                        value={form.dateTime ? form.dateTime.slice(0, 10) : ''}
                        onChange={(e) =>
                            setForm((prev) => ({ ...prev, dateTime: toIsoFromDateOnly(e.target.value, 10, 0) }))
                        }
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-800 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                    />

                    <input
                        required
                        value={form.location}
                        onChange={(e) => setForm((prev) => ({ ...prev, location: e.target.value }))}
                        placeholder="Location"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    />

                    <div className="relative">
                        <select
                            value={form.mode}
                            onChange={(e) => setForm((prev) => ({ ...prev, mode: e.target.value }))}
                            className="w-full appearance-none rounded-lg border border-slate-300 bg-white px-3 py-2 pr-9 text-slate-800 shadow-sm transition focus:border-amber-300 focus:outline-none focus:ring-2 focus:ring-amber-200 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                        >
                            <option value="offline">Offline</option>
                            <option value="online">Online</option>
                        </select>
                        <svg
                            viewBox="0 0 20 20"
                            aria-hidden="true"
                            className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500 dark:text-slate-300"
                        >
                            <path fill="currentColor" d="M5.23 7.21 10 11.98l4.77-4.77 1.42 1.42L10 14.82 3.81 8.63z" />
                        </svg>
                    </div>

                    <input
                        value={form.type}
                        onChange={(e) => setForm((prev) => ({ ...prev, type: e.target.value }))}
                        placeholder="Event Type"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    />

                    <input
                        required
                        type="url"
                        value={form.googleFormUrl}
                        onChange={(e) => setForm((prev) => ({ ...prev, googleFormUrl: e.target.value }))}
                        placeholder="Google Form Link"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    />

                    <label className="block rounded-lg border border-dashed border-slate-300 px-3 py-2 text-sm text-slate-600">
                        Poster Upload
                        <input
                            type="file"
                            accept="image/*"
                            onChange={(e) => handlePosterUpload(e.target.files?.[0])}
                            className="mt-2 block w-full text-xs"
                        />
                    </label>

                    <button className="w-full rounded-xl bg-gradient-to-r from-amber-400 to-orange-500 px-4 py-2.5 text-sm font-bold text-black shadow-[0_10px_24px_rgba(249,115,22,0.28)] transition-all duration-200 hover:-translate-y-0.5 hover:from-amber-300 hover:to-orange-400 hover:shadow-[0_14px_28px_rgba(249,115,22,0.34)] focus:outline-none focus:ring-2 focus:ring-amber-300 focus:ring-offset-2 focus:ring-offset-transparent">
                        Create Event
                    </button>
                </form>

                <section className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                    <h2 className="text-xl font-black text-slate-900">Manage Events</h2>

                    <div className="space-y-3">
                        {clubEvents.map((event) => (
                            <article
                                key={event.id}
                                className="rounded-xl border border-slate-200 p-3"
                            >
                                <div className="flex flex-wrap items-start justify-between gap-2">
                                    <div>
                                        <h3 className="font-bold text-slate-900">{event.title}</h3>
                                        <p className="text-sm text-slate-600">{event.clubName}</p>
                                    </div>
                                    <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                                        {event.registrations} registrations
                                    </span>
                                </div>

                                <p className="mt-2 text-sm text-slate-700">{event.description}</p>

                                <div className="mt-3 flex flex-wrap gap-2">
                                    <button
                                        onClick={() => setEditing(event)}
                                        className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white"
                                    >
                                        Edit
                                    </button>
                                    <button
                                        onClick={() => deleteClubEvent(event.id)}
                                        className="rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white"
                                    >
                                        Delete
                                    </button>
                                    <button
                                        onClick={() => duplicateClubEvent(event)}
                                        className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white"
                                    >
                                        Duplicate
                                    </button>
                                </div>
                            </article>
                        ))}
                    </div>
                </section>
            </section>

            <Modal
                isOpen={Boolean(editing)}
                title="Edit Event"
                onClose={() => setEditing(null)}
            >
                {editing && (
                    <div className="space-y-3">
                        <input
                            value={editing.title}
                            onChange={(e) => setEditing((prev) => ({ ...prev, title: e.target.value }))}
                            placeholder="Title"
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        />
                        <textarea
                            value={editing.description}
                            onChange={(e) =>
                                setEditing((prev) => ({ ...prev, description: e.target.value }))
                            }
                            placeholder="Description"
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        />
                        <input
                            value={editing.clubName || ''}
                            onChange={(e) => setEditing((prev) => ({ ...prev, clubName: e.target.value }))}
                            placeholder="Club Name"
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        />
                        <input
                            type="date"
                            value={editing.dateTime ? editing.dateTime.slice(0, 10) : ''}
                            onChange={(e) =>
                                setEditing((prev) => ({ ...prev, dateTime: toIsoFromDateOnly(e.target.value, 10, 0) }))
                            }
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        />
                        <input
                            value={editing.location || ''}
                            onChange={(e) => setEditing((prev) => ({ ...prev, location: e.target.value }))}
                            placeholder="Location"
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        />
                        <select
                            value={editing.mode || 'offline'}
                            onChange={(e) => setEditing((prev) => ({ ...prev, mode: e.target.value }))}
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        >
                            <option value="offline">Offline</option>
                            <option value="online">Online</option>
                        </select>
                        <input
                            value={editing.type || ''}
                            onChange={(e) => setEditing((prev) => ({ ...prev, type: e.target.value }))}
                            placeholder="Event Type"
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        />
                        <input
                            type="url"
                            value={editing.googleFormUrl || ''}
                            onChange={(e) => setEditing((prev) => ({ ...prev, googleFormUrl: e.target.value }))}
                            placeholder="Google Form Link"
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        />
                        <label className="block rounded-lg border border-dashed border-slate-300 px-3 py-2 text-sm text-slate-600">
                            Poster Upload
                            <input
                                type="file"
                                accept="image/*"
                                onChange={(e) => handleEditPosterUpload(e.target.files?.[0])}
                                className="mt-2 block w-full text-xs"
                            />
                        </label>
                        <button
                            onClick={handleEditSave}
                            className="w-full rounded-xl bg-gradient-to-r from-amber-400 to-orange-500 px-4 py-2.5 text-sm font-bold text-black shadow-[0_10px_24px_rgba(249,115,22,0.28)] transition-all duration-200 hover:-translate-y-0.5 hover:from-amber-300 hover:to-orange-400 hover:shadow-[0_14px_28px_rgba(249,115,22,0.34)] focus:outline-none focus:ring-2 focus:ring-amber-300 focus:ring-offset-2 focus:ring-offset-transparent"
                        >
                            Save Changes
                        </button>
                    </div>
                )}
            </Modal>
        </main>
    )
}
