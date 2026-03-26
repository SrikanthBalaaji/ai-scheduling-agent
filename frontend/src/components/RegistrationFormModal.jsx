import { useEffect, useMemo, useState } from 'react'
import { Modal } from './Modal'

const FIELD_CONFIG = {
    name: {
        label: 'Name',
        placeholder: 'Enter your full name',
        type: 'text',
    },
    srn: {
        label: 'SRN',
        placeholder: 'Enter your SRN',
        type: 'text',
    },
    semester: {
        label: 'Semester',
        placeholder: 'Enter your semester (e.g. 5)',
        type: 'text',
    },
}

const DEFAULT_FIELDS = ['name', 'srn', 'semester']

export const RegistrationFormModal = ({ isOpen, event, onClose, onSubmit }) => {
    const [formData, setFormData] = useState({})
    const [submitting, setSubmitting] = useState(false)

    const formFields = useMemo(() => {
        const predefined = (event?.registrationFields?.length
            ? event.registrationFields
            : DEFAULT_FIELDS
        )
            .filter((field) => FIELD_CONFIG[field])
            .map((field) => ({
                key: field,
                label: FIELD_CONFIG[field].label,
                placeholder: FIELD_CONFIG[field].placeholder,
                type: FIELD_CONFIG[field].type,
                required: true,
            }))

        const custom = (event?.customFields || []).map((field) => ({
            key: field.key || field.id || field.label,
            label: field.label,
            placeholder: field.placeholder || `Enter ${String(field.label || 'value').toLowerCase()}`,
            type: field.type || 'text',
            required: field.required !== false,
        }))

        return [...predefined, ...custom]
    }, [event])

    useEffect(() => {
        if (!isOpen) return
        const initialValues = formFields.reduce((acc, field) => {
            acc[field.key] = ''
            return acc
        }, {})
        setFormData(initialValues)
    }, [isOpen, formFields])

    const handleChange = (field, value) => {
        setFormData((prev) => ({ ...prev, [field]: value }))
    }

    const handleClose = () => {
        if (submitting) return
        setFormData({})
        onClose()
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setSubmitting(true)
        try {
            const payload = formFields.reduce((acc, field) => {
                acc[field.key] = (formData[field.key] || '').trim()
                return acc
            }, {})

            await onSubmit(payload)
            setFormData({})
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <Modal isOpen={isOpen} onClose={handleClose} title="Event Registration Form">
            {event && (
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2">
                        <p className="text-sm font-semibold text-slate-900">{event.title}</p>
                        <p className="text-xs text-slate-600">Please fill in the details to complete your registration.</p>
                    </div>

                    {formFields.map((field) => {
                        return (
                            <label key={field.key} className="block space-y-1 text-sm font-medium text-slate-700">
                                <span>
                                    {field.label} {field.required ? <span className="text-rose-600">*</span> : null}
                                </span>
                                <input
                                    type={field.type}
                                    value={formData[field.key] || ''}
                                    onChange={(evt) => handleChange(field.key, evt.target.value)}
                                    placeholder={field.placeholder}
                                    required={field.required}
                                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-amber-300 focus:outline-none focus:ring-2 focus:ring-amber-200"
                                />
                            </label>
                        )
                    })}

                    <div className="flex items-center justify-end gap-2 pt-2">
                        <button
                            type="button"
                            onClick={handleClose}
                            disabled={submitting}
                            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={submitting}
                            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-emerald-400"
                        >
                            {submitting ? 'Submitting...' : 'Submit Registration'}
                        </button>
                    </div>
                </form>
            )}
        </Modal>
    )
}
