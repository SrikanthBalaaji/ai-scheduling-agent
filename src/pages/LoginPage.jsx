import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { interestOptions } from '../data/mockEvents'
import { useAppContext } from '../context/AppContext'

export const LoginPage = () => {
    const navigate = useNavigate()
    const { login } = useAppContext()
    const [name, setName] = useState('')
    const [role, setRole] = useState('student')
    const [interests, setInterests] = useState(['hackathon', 'guest talk'])

    const toggleInterest = (interest) => {
        setInterests((prev) =>
            prev.includes(interest)
                ? prev.filter((item) => item !== interest)
                : [...prev, interest],
        )
    }

    const handleSubmit = (e) => {
        e.preventDefault()
        login({
            role,
            name: name.trim() || (role === 'student' ? 'Student User' : 'Club Member'),
            interests,
        })

        navigate(role === 'club' ? '/club' : '/billboard')
    }

    return (
        <main className="login-shell relative min-h-screen overflow-hidden px-4 py-14 transition-colors duration-300">
            <div className="login-card mx-auto w-full max-w-md rounded-3xl border border-amber-200 bg-white/85 p-6 shadow-2xl backdrop-blur">
                <h1 className="login-title text-3xl font-black tracking-tight text-slate-900">
                    Student AI Planner
                </h1>
                <p className="login-subtitle mt-2 text-sm text-slate-600">
                    One login for students and club organizers.
                </p>

                <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                    <label className="login-label block space-y-1 text-sm font-semibold text-slate-700">
                        Name
                        <input
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Enter your name"
                            className="login-input w-full rounded-xl border border-slate-300 px-3 py-2"
                        />
                    </label>

                    <fieldset className="space-y-2">
                        <legend className="login-label text-sm font-semibold text-slate-700">Role</legend>
                        <div className="role-switch" role="radiogroup" aria-label="Select role">
                            <button
                                type="button"
                                role="radio"
                                aria-checked={role === 'student'}
                                onClick={() => setRole('student')}
                                className={`role-option ${role === 'student' ? 'role-option-active' : ''}`}
                            >
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
                                    <path d="M15 20v-1a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v1" />
                                    <circle cx="9" cy="7" r="4" />
                                </svg>
                                <span>Student</span>
                            </button>

                            <button
                                type="button"
                                role="radio"
                                aria-checked={role === 'club'}
                                onClick={() => setRole('club')}
                                className={`role-option ${role === 'club' ? 'role-option-active' : ''}`}
                            >
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
                                    <path d="M12 3l7 4v5c0 5-3.5 8-7 9-3.5-1-7-4-7-9V7l7-4z" />
                                    <path d="m9.2 12.3 1.8 1.8 3.8-3.8" />
                                </svg>
                                <span>Club Member</span>
                            </button>
                        </div>
                    </fieldset>

                    {role === 'student' && (
                        <fieldset className="space-y-2">
                            <legend className="login-label text-sm font-semibold text-slate-700">
                                Interests (for recommendations)
                            </legend>
                            <div className="flex flex-wrap gap-2">
                                {interestOptions.map((interest) => (
                                    <button
                                        type="button"
                                        key={interest}
                                        onClick={() => toggleInterest(interest)}
                                        className={`interest-chip rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide transition-all duration-200 ${interests.includes(interest)
                                            ? 'interest-chip-active bg-amber-400 text-slate-900 ring-2 ring-amber-300'
                                            : 'interest-chip-idle bg-amber-100 text-amber-900 hover:bg-amber-200'
                                            }`}
                                    >
                                        {interest}
                                    </button>
                                ))}
                            </div>
                        </fieldset>
                    )}

                    <button
                        type="submit"
                        className="login-submit w-full rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-900"
                    >
                        Continue
                    </button>
                </form>
            </div>
        </main>
    )
}
