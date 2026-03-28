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

const toIsoFromDayMonthYear = (day, month, year, hour = 10, minute = 0) => {
    if (!day || !month || !year) return ''
    const d = Number(day)
    const m = Number(month)
    const y = Number(year)
    if (!d || !m || !y) return ''
    return new Date(y, m - 1, d, hour, minute, 0, 0).toISOString()
}

const getDateComponents = (isoString) => {
    if (!isoString) {
        const now = new Date()
        return {
            day: String(now.getDate()).padStart(2, '0'),
            month: String(now.getMonth() + 1).padStart(2, '0'),
            year: String(now.getFullYear()),
        }
    }
    const date = new Date(isoString)
    return {
        day: String(date.getDate()).padStart(2, '0'),
        month: String(date.getMonth() + 1).padStart(2, '0'),
        year: String(date.getFullYear()),
    }
}

const getDaysInMonth = (month, year) => {
    return new Date(year, month, 0).getDate()
}

const getCurrentYear = () => new Date().getFullYear()

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
const MONTH_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const getMonthLabel = (monthNum) => {
    const m = Number(monthNum)
    if (!m || m < 1 || m > 12) return ''
    return MONTH_SHORT[m - 1]
}

const parseMonthInput = (input) => {
    if (!input) return ''
    const inputLower = input.toLowerCase()
    const matched = MONTHS.findIndex(m => m.toLowerCase().startsWith(inputLower))
    if (matched !== -1) return String(matched + 1).padStart(2, '0')

    const shortMatched = MONTH_SHORT.findIndex(m => m.toLowerCase().startsWith(inputLower))
    if (shortMatched !== -1) return String(shortMatched + 1).padStart(2, '0')

    const num = Number(input)
    if (num >= 1 && num <= 12) return String(num).padStart(2, '0')
    return ''
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
    const [dateInputs, setDateInputs] = useState({ day: '', month: '', year: '' })
    const [editDateInputs, setEditDateInputs] = useState({ day: '', month: '', year: '' })

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

                    <div className="grid grid-cols-3 gap-2">
                        {/* Day Input */}
                        <div>
                            <input
                                required
                                type="text"
                                inputMode="numeric"
                                maxLength="2"
                                value={dateInputs.day}
                                onChange={(e) => {
                                    const day = e.target.value.replace(/[^0-9]/g, '')
                                    setDateInputs((prev) => ({ ...prev, day }))
                                    if (day && day >= 1 && day <= 31) {
                                        const { month, year } = getDateComponents(form.dateTime)
                                        setForm((prev) => ({
                                            ...prev,
                                            dateTime: toIsoFromDayMonthYear(day, month, year),
                                        }))
                                    }
                                }}
                                onFocus={(e) => {
                                    if (!dateInputs.day) {
                                        setDateInputs((prev) => ({ ...prev, day: getDateComponents(form.dateTime).day }))
                                    }
                                }}
                                placeholder="Day"
                                className="w-full rounded-lg border border-slate-300 px-3 py-2"
                            />
                        </div>

                        {/* Month Input with filtering */}
                        <div>
                            <input
                                required
                                type="text"
                                value={dateInputs.month}
                                onChange={(e) => {
                                    const input = e.target.value
                                    setDateInputs((prev) => ({ ...prev, month: input }))
                                    const parsed = parseMonthInput(input)
                                    if (parsed) {
                                        const { day, year } = getDateComponents(form.dateTime)
                                        setForm((prev) => ({
                                            ...prev,
                                            dateTime: toIsoFromDayMonthYear(day, parsed, year),
                                        }))
                                    }
                                }}
                                onFocus={(e) => {
                                    if (!dateInputs.month) {
                                        setDateInputs((prev) => ({ ...prev, month: getMonthLabel(getDateComponents(form.dateTime).month) }))
                                    }
                                }}
                                placeholder="Month (Jan-Dec or type A, M, etc.)"
                                list="months-list"
                                className="w-full rounded-lg border border-slate-300 px-3 py-2"
                            />
                            <datalist id="months-list">
                                {MONTH_SHORT.map((month, i) => (
                                    <option key={i} value={month} />
                                ))}
                            </datalist>
                        </div>

                        {/* Year Input */}
                        <div>
                            <input
                                required
                                type="text"
                                inputMode="numeric"
                                maxLength="4"
                                value={dateInputs.year}
                                onChange={(e) => {
                                    const year = e.target.value.replace(/[^0-9]/g, '')
                                    setDateInputs((prev) => ({ ...prev, year }))
                                    if (year && year >= 2025 && year <= 2035) {
                                        const { day, month } = getDateComponents(form.dateTime)
                                        setForm((prev) => ({
                                            ...prev,
                                            dateTime: toIsoFromDayMonthYear(day, month, year),
                                        }))
                                    }
                                }}
                                onFocus={(e) => {
                                    if (!dateInputs.year) {
                                        setDateInputs((prev) => ({ ...prev, year: getDateComponents(form.dateTime).year }))
                                    }
                                }}
                                placeholder="Year"
                                className="w-full rounded-lg border border-slate-300 px-3 py-2"
                            />
                        </div>
                    </div>

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
                        <div className="grid grid-cols-3 gap-2">
                            {/* Day Input */}
                            <div>
                                <input
                                    type="text"
                                    inputMode="numeric"
                                    maxLength="2"
                                    value={editDateInputs.day}
                                    onChange={(e) => {
                                        const day = e.target.value.replace(/[^0-9]/g, '')
                                        setEditDateInputs((prev) => ({ ...prev, day }))
                                        if (day && day >= 1 && day <= 31) {
                                            const { month, year } = getDateComponents(editing.dateTime)
                                            setEditing((prev) => ({
                                                ...prev,
                                                dateTime: toIsoFromDayMonthYear(day, month, year),
                                            }))
                                        }
                                    }}
                                    onFocus={(e) => {
                                        if (!editDateInputs.day) {
                                            setEditDateInputs((prev) => ({ ...prev, day: getDateComponents(editing.dateTime).day }))
                                        }
                                    }}
                                    placeholder="Day"
                                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                                />
                            </div>

                            {/* Month Input with filtering */}
                            <div>
                                <input
                                    type="text"
                                    value={editDateInputs.month}
                                    onChange={(e) => {
                                        const input = e.target.value
                                        setEditDateInputs((prev) => ({ ...prev, month: input }))
                                        const parsed = parseMonthInput(input)
                                        if (parsed) {
                                            const { day, year } = getDateComponents(editing.dateTime)
                                            setEditing((prev) => ({
                                                ...prev,
                                                dateTime: toIsoFromDayMonthYear(day, parsed, year),
                                            }))
                                        }
                                    }}
                                    onFocus={(e) => {
                                        if (!editDateInputs.month) {
                                            setEditDateInputs((prev) => ({ ...prev, month: getMonthLabel(getDateComponents(editing.dateTime).month) }))
                                        }
                                    }}
                                    placeholder="Month (Jan-Dec or type A, M, etc.)"
                                    list="months-list-edit"
                                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                                />
                                <datalist id="months-list-edit">
                                    {MONTH_SHORT.map((month, i) => (
                                        <option key={i} value={month} />
                                    ))}
                                </datalist>
                            </div>

                            {/* Year Input */}
                            <div>
                                <input
                                    type="text"
                                    inputMode="numeric"
                                    maxLength="4"
                                    value={editDateInputs.year}
                                    onChange={(e) => {
                                        const year = e.target.value.replace(/[^0-9]/g, '')
                                        setEditDateInputs((prev) => ({ ...prev, year }))
                                        if (year && year >= 2025 && year <= 2035) {
                                            const { day, month } = getDateComponents(editing.dateTime)
                                            setEditing((prev) => ({
                                                ...prev,
                                                dateTime: toIsoFromDayMonthYear(day, month, year),
                                            }))
                                        }
                                    }}
                                    onFocus={(e) => {
                                        if (!editDateInputs.year) {
                                            setEditDateInputs((prev) => ({ ...prev, year: getDateComponents(editing.dateTime).year }))
                                        }
                                    }}
                                    placeholder="Year"
                                    className="w-full rounded-lg border border-slate-300 px-3 py-2"
                                />
                            </div>
                        </div>
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
