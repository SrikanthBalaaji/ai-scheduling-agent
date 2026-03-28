import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { interestOptions } from '../data/mockEvents'
import { AnimatedRoleSwitcher } from '../components/AnimatedRoleSwitcher'
import { useAppContext } from '../context/AppContext'

export const LoginPage = () => {
    const navigate = useNavigate()
    const { login } = useAppContext()
    const [role, setRole] = useState('student')
    const [interests, setInterests] = useState(['hackathon', 'guest talk'])
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const toggleInterest = (interest) => {
        setInterests((prev) =>
            prev.includes(interest)
                ? prev.filter((item) => item !== interest)
                : [...prev, interest],
        )
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        const result = await login({ username, password, interests })
        setLoading(false)

        if (!result.success) {
            setError(result.error)
            return
        }
        navigate(result.role === 'club' ? '/club' : '/billboard')
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
                        Username
                        <input
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter your username"
                            className="login-input w-full rounded-xl border border-slate-300 px-3 py-2"
                        />
                    </label>

                    <label className="login-label block space-y-1 text-sm font-semibold text-slate-700">
                        Password
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            className="login-input w-full rounded-xl border border-slate-300 px-3 py-2"
                        />
                    </label>

                    {error && (
                        <p className="text-sm font-medium text-red-500">{error}</p>
                    )}

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
                                        className={`interest-chip rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide transition-all duration-200 ${
                                            interests.includes(interest)
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
                        disabled={loading}
                        className="login-submit w-full rounded-xl px-4 py-2.5 text-sm font-semibold disabled:opacity-50"
                    >
                        {loading ? 'Checking...' : 'Continue'}
                    </button>
                </form>
            </div>
        </main>
    )
}