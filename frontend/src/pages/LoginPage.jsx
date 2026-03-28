import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { interestOptions } from '../data/mockEvents'
import { AnimatedRoleSwitcher } from '../components/AnimatedRoleSwitcher'
import { useAppContext } from '../context/AppContext'
import { usersApi } from '../services/api'

export const LoginPage = () => {
    const navigate = useNavigate()
    const { login } = useAppContext()
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [role, setRole] = useState('student')
    const [interests, setInterests] = useState(['hackathon', 'guest talk'])
    const [isRegistering, setIsRegistering] = useState(false)
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const toggleInterest = (interest) => {
        setInterests((prev) =>
            prev.includes(interest)
                ? prev.filter((item) => item !== interest)
                : [...prev, interest],
        )
    }

    const handleRegister = async (e) => {
        e.preventDefault()
        setError('')

        if (!username || !password || !name) {
            setError('All fields are required')
            return
        }

        if (password.length < 4) {
            setError('Password must be at least 4 characters')
            return
        }

        setLoading(true)
        try {
            const response = await usersApi.register(username, password, name, role, interests)
            if (response.success) {
                login(response.user)
                navigate(role === 'club' ? '/club' : '/billboard')
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed')
        } finally {
            setLoading(false)
        }
    }

    const handleLogin = async (e) => {
        e.preventDefault()
        setError('')

        if (!username || !password) {
            setError('Username and password are required')
            return
        }

        setLoading(true)
        try {
            const response = await usersApi.login(username, password)
            if (response.success) {
                login(response.user)
                navigate(response.user.role === 'club' ? '/club' : '/billboard')
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed')
        } finally {
            setLoading(false)
        }
    }

    const handleSubmit = isRegistering ? handleRegister : handleLogin

    return (
        <main className="login-shell relative min-h-screen overflow-hidden px-4 py-14 transition-colors duration-300">
            <div className="login-card mx-auto w-full max-w-md rounded-3xl border border-amber-200 bg-white/85 p-6 shadow-2xl backdrop-blur">
                <h1 className="login-title text-3xl font-black tracking-tight text-slate-900">
                    Planora
                </h1>
                <p className="login-subtitle mt-2 text-sm text-slate-600">
                    Discover events. Plan smarter. Never miss what matters.
                </p>

                {error && (
                    <div className="mt-4 rounded-xl bg-rose-100 px-3 py-2 text-sm text-rose-700 border border-rose-200">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                    <label className="login-label block space-y-1 text-sm font-semibold text-slate-700">
                        Username
                        <input
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter username"
                            className="login-input w-full rounded-xl border border-slate-300 px-3 py-2"
                        />
                    </label>

                    <label className="login-label block space-y-1 text-sm font-semibold text-slate-700">
                        Password
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter password"
                            className="login-input w-full rounded-xl border border-slate-300 px-3 py-2"
                        />
                    </label>

                    {isRegistering && (
                        <>
                            <label className="login-label block space-y-1 text-sm font-semibold text-slate-700">
                                Full Name
                                <input
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="Enter your full name"
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
                        </>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="login-submit w-full rounded-xl px-4 py-2.5 text-sm font-semibold disabled:opacity-60"
                    >
                        {loading ? 'Loading...' : isRegistering ? 'Create Account' : 'Login'}
                    </button>
                </form>

                <button
                    onClick={() => {
                        setIsRegistering(!isRegistering)
                        setError('')
                    }}
                    className="mt-4 w-full text-center text-sm text-amber-600 hover:text-amber-700 font-semibold"
                >
                    {isRegistering ? 'Already have an account? Login' : "Don't have an account? Register"}
                </button>
            </div>
        </main>
    )
}