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
    registrationFields: ['name', 'srn', 'semester'],
    customFields: [],
}

const registrationFieldOptions = [
    { value: 'name', label: 'Name' },
    { value: 'srn', label: 'SRN' },
    { value: 'semester', label: 'Semester' },
]

const toIsoFromDateOnly = (dateString, hour = 12, minute = 0) => {
    if (!dateString) return ''
    const [year, month, day] = dateString.split('-').map(Number)
    return new Date(year, month - 1, day, hour, minute, 0, 0).toISOString()
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
    const [customFieldDraft, setCustomFieldDraft] = useState({
        label: '',
        type: 'text',
        required: true,
    })
    const [editCustomFieldDraft, setEditCustomFieldDraft] = useState({
        label: '',
        type: 'text',
        required: true,
    })

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

    const toggleRegistrationField = (field) => {
        setForm((prev) => {
            const next = prev.registrationFields.includes(field)
                ? prev.registrationFields.filter((item) => item !== field)
                : [...prev.registrationFields, field]

            return {
                ...prev,
                registrationFields: next.length ? next : ['name'],
            }
        })
    }

    const addCustomFieldToCreateForm = () => {
        const label = customFieldDraft.label.trim()
        if (!label) return

        const id = `custom-${Date.now()}-${Math.random().toString(16).slice(2, 7)}`
        setForm((prev) => ({
            ...prev,
            customFields: [
                ...(prev.customFields || []),
                {
                    id,
                    key: id,
                    label,
                    type: customFieldDraft.type,
                    required: customFieldDraft.required,
                    placeholder: `Enter ${label.toLowerCase()}`,
                },
            ],
        }))
        setCustomFieldDraft({ label: '', type: 'text', required: true })
    }

    const removeCustomFieldFromCreateForm = (fieldId) => {
        setForm((prev) => ({
            ...prev,
            customFields: (prev.customFields || []).filter((field) => field.id !== fieldId),
        }))
    }

    const addCustomFieldToEditForm = () => {
        const label = editCustomFieldDraft.label.trim()
        if (!label || !editing) return

        const id = `custom-${Date.now()}-${Math.random().toString(16).slice(2, 7)}`
        setEditing((prev) => ({
            ...prev,
            customFields: [
                ...(prev.customFields || []),
                {
                    id,
                    key: id,
                    label,
                    type: editCustomFieldDraft.type,
                    required: editCustomFieldDraft.required,
                    placeholder: `Enter ${label.toLowerCase()}`,
                },
            ],
        }))
        setEditCustomFieldDraft({ label: '', type: 'text', required: true })
    }

    const removeCustomFieldFromEditForm = (fieldId) => {
        setEditing((prev) => ({
            ...prev,
            customFields: (prev.customFields || []).filter((field) => field.id !== fieldId),
        }))
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

                    <div className="grid grid-cols-2 gap-2">
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
                            required
                            type="date"
                            value={form.registrationDeadline ? form.registrationDeadline.slice(0, 10) : ''}
                            onChange={(e) =>
                                setForm((prev) => ({
                                    ...prev,
                                    registrationDeadline: toIsoFromDateOnly(e.target.value, 23, 59),
                                }))
                            }
                            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-800 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
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

                    <fieldset className="space-y-2 rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-emerald-50/60 p-3 dark:border-slate-700 dark:bg-gradient-to-br dark:from-slate-900 dark:to-emerald-950/40">
                        <legend className="px-2 text-sm font-semibold text-slate-800 dark:bg-slate-900 dark:text-slate-100">Registration Form Fields</legend>
                        <p className="text-xs text-slate-600 dark:text-slate-300">
                            Select fields students must fill while registering for this event.
                        </p>
                        <div className="flex flex-wrap gap-2 pt-1">
                            {registrationFieldOptions.map((option) => {
                                const isSelected = form.registrationFields.includes(option.value)
                                return (
                                    <button
                                        key={option.value}
                                        type="button"
                                        onClick={() => toggleRegistrationField(option.value)}
                                        className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${isSelected
                                            ? 'bg-emerald-600 text-white shadow-sm'
                                            : 'bg-white text-slate-700 ring-1 ring-slate-300 dark:bg-slate-900 dark:text-slate-200 dark:ring-slate-600'
                                            }`}
                                    >
                                        {option.label}
                                    </button>
                                )
                            })}
                        </div>
                    </fieldset>

                    <fieldset className="space-y-2 rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-sky-50/60 p-3 dark:border-slate-700 dark:bg-gradient-to-br dark:from-slate-900 dark:to-sky-950/40">
                        <legend className="px-2 text-sm font-semibold text-slate-800 dark:bg-slate-900 dark:text-slate-100">Custom Registration Fields</legend>
                        <p className="text-xs text-slate-600 dark:text-slate-300">
                            Add event-specific questions (for example: Branch, Section, Team Size).
                        </p>
                        <div className="grid grid-cols-1 gap-2 sm:grid-cols-[1.5fr_1fr_auto] sm:items-center">
                            <input
                                value={customFieldDraft.label}
                                onChange={(e) => setCustomFieldDraft((prev) => ({ ...prev, label: e.target.value }))}
                                placeholder="Field label"
                                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                            />
                            <select
                                value={customFieldDraft.type}
                                onChange={(e) => setCustomFieldDraft((prev) => ({ ...prev, type: e.target.value }))}
                                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                            >
                                <option value="text">Text</option>
                                <option value="number">Number</option>
                                <option value="email">Email</option>
                            </select>
                            <button
                                type="button"
                                onClick={addCustomFieldToCreateForm}
                                className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white"
                            >
                                Add
                            </button>
                        </div>
                        <label className="inline-flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
                            <input
                                type="checkbox"
                                checked={customFieldDraft.required}
                                onChange={(e) =>
                                    setCustomFieldDraft((prev) => ({ ...prev, required: e.target.checked }))
                                }
                            />
                            Required field
                        </label>

                        {(form.customFields || []).length > 0 && (
                            <div className="flex flex-wrap gap-2 pt-1">
                                {form.customFields.map((field) => (
                                    <span
                                        key={field.id}
                                        className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-300 dark:bg-slate-900 dark:text-slate-200 dark:ring-slate-600"
                                    >
                                        {field.label} ({field.type}){field.required ? ' *' : ''}
                                        <button
                                            type="button"
                                            onClick={() => removeCustomFieldFromCreateForm(field.id)}
                                            className="text-rose-600"
                                        >
                                            x
                                        </button>
                                    </span>
                                ))}
                            </div>
                        )}
                    </fieldset>

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
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        />
                        <textarea
                            value={editing.description}
                            onChange={(e) =>
                                setEditing((prev) => ({ ...prev, description: e.target.value }))
                            }
                            className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        />
                        <fieldset className="space-y-2 rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-emerald-50/60 p-3 dark:border-slate-700 dark:bg-gradient-to-br dark:from-slate-900 dark:to-emerald-950/40">
                            <legend className="px-2 text-sm font-semibold text-slate-800 dark:bg-slate-900 dark:text-slate-100">Registration Form Fields</legend>
                            <div className="flex flex-wrap gap-2">
                                {registrationFieldOptions.map((option) => {
                                    const fields = editing.registrationFields || ['name', 'srn', 'semester']
                                    const isSelected = fields.includes(option.value)
                                    return (
                                        <button
                                            key={option.value}
                                            type="button"
                                            onClick={() => {
                                                setEditing((prev) => {
                                                    const current = prev.registrationFields || ['name', 'srn', 'semester']
                                                    const next = current.includes(option.value)
                                                        ? current.filter((item) => item !== option.value)
                                                        : [...current, option.value]

                                                    return {
                                                        ...prev,
                                                        registrationFields: next.length ? next : ['name'],
                                                    }
                                                })
                                            }}
                                            className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${isSelected
                                                ? 'bg-emerald-600 text-white shadow-sm'
                                                : 'bg-white text-slate-700 ring-1 ring-slate-300 dark:bg-slate-900 dark:text-slate-200 dark:ring-slate-600'
                                                }`}
                                        >
                                            {option.label}
                                        </button>
                                    )
                                })}
                            </div>
                        </fieldset>
                        <fieldset className="space-y-2 rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-sky-50/60 p-3 dark:border-slate-700 dark:bg-gradient-to-br dark:from-slate-900 dark:to-sky-950/40">
                            <legend className="px-2 text-sm font-semibold text-slate-800 dark:bg-slate-900 dark:text-slate-100">Custom Registration Fields</legend>
                            <div className="grid grid-cols-1 gap-2 sm:grid-cols-[1.5fr_1fr_auto] sm:items-center">
                                <input
                                    value={editCustomFieldDraft.label}
                                    onChange={(e) =>
                                        setEditCustomFieldDraft((prev) => ({ ...prev, label: e.target.value }))
                                    }
                                    placeholder="Field label"
                                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                                />
                                <select
                                    value={editCustomFieldDraft.type}
                                    onChange={(e) =>
                                        setEditCustomFieldDraft((prev) => ({ ...prev, type: e.target.value }))
                                    }
                                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
                                >
                                    <option value="text">Text</option>
                                    <option value="number">Number</option>
                                    <option value="email">Email</option>
                                </select>
                                <button
                                    type="button"
                                    onClick={addCustomFieldToEditForm}
                                    className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white"
                                >
                                    Add
                                </button>
                            </div>
                            <label className="inline-flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
                                <input
                                    type="checkbox"
                                    checked={editCustomFieldDraft.required}
                                    onChange={(e) =>
                                        setEditCustomFieldDraft((prev) => ({ ...prev, required: e.target.checked }))
                                    }
                                />
                                Required field
                            </label>

                            {(editing.customFields || []).length > 0 && (
                                <div className="flex flex-wrap gap-2 pt-1">
                                    {editing.customFields.map((field) => (
                                        <span
                                            key={field.id}
                                            className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-300 dark:bg-slate-900 dark:text-slate-200 dark:ring-slate-600"
                                        >
                                            {field.label} ({field.type}){field.required ? ' *' : ''}
                                            <button
                                                type="button"
                                                onClick={() => removeCustomFieldFromEditForm(field.id)}
                                                className="text-rose-600"
                                            >
                                                x
                                            </button>
                                        </span>
                                    ))}
                                </div>
                            )}
                        </fieldset>
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
