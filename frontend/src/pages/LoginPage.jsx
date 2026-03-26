import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { interestOptions } from '../data/mockEvents'
import { AnimatedRoleSwitcher } from '../components/AnimatedRoleSwitcher'
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
                    Planora
                </h1>
                <p className="login-subtitle mt-2 text-sm text-slate-600">
                    Discover events. Plan smarter. Never miss what matters.
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
                        <div role="radiogroup" aria-label="Select role">
                            <AnimatedRoleSwitcher value={role} onChange={setRole} />
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
                        className="login-submit w-full rounded-xl px-4 py-2.5 text-sm font-semibold"
                    >
                        Continue
                    </button>
                </form>
            </div>
        </main>
    )
}
