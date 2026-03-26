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
    registrationDeadline: '',
    posterUrl: '',
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

    const handleEditSave = async () => {
        if (!editing) return
        await updateClubEvent(editing.id, editing)
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
                        type="datetime-local"
                        value={form.dateTime}
                        onChange={(e) =>
                            setForm((prev) => ({ ...prev, dateTime: new Date(e.target.value).toISOString() }))
                        }
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    />

                    <input
                        required
                        value={form.location}
                        onChange={(e) => setForm((prev) => ({ ...prev, location: e.target.value }))}
                        placeholder="Location"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                    />

                    <div className="grid grid-cols-2 gap-2">
                        <select
                            value={form.mode}
                            onChange={(e) => setForm((prev) => ({ ...prev, mode: e.target.value }))}
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        >
                            <option value="offline">Offline</option>
                            <option value="online">Online</option>
                        </select>

                        <input
                            required
                            type="datetime-local"
                            value={form.registrationDeadline}
                            onChange={(e) =>
                                setForm((prev) => ({
                                    ...prev,
                                    registrationDeadline: new Date(e.target.value).toISOString(),
                                }))
                            }
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        />
                    </div>

                    <input
                        value={form.type}
                        onChange={(e) => setForm((prev) => ({ ...prev, type: e.target.value }))}
                        placeholder="Event Type"
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

                    <button className="w-full rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
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
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        />
                        <textarea
                            value={editing.description}
                            onChange={(e) =>
                                setEditing((prev) => ({ ...prev, description: e.target.value }))
                            }
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        />
                        <button
                            onClick={handleEditSave}
                            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
                        >
                            Save Changes
                        </button>
                    </div>
                )}
            </Modal>
        </main>
    )
}
