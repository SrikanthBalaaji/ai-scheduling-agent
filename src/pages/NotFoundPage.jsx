import { Link } from 'react-router-dom'

export const NotFoundPage = () => {
    return (
        <main className="flex min-h-[70vh] flex-col items-center justify-center gap-3 px-4 text-center">
            <h1 className="text-3xl font-black text-slate-900">Page Not Found</h1>
            <p className="text-sm text-slate-600">The page you are looking for does not exist.</p>
            <Link
                to="/billboard"
                className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            >
                Go Home
            </Link>
        </main>
    )
}
