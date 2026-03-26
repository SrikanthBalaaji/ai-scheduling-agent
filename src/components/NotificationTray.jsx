import { useAppContext } from '../context/AppContext'

export const NotificationTray = () => {
    const { notifications, clearNotification } = useAppContext()

    if (!notifications.length) {
        return (
            <aside className="rounded-2xl border border-emerald-100 bg-white/90 p-4 shadow-sm">
                <p className="text-sm text-slate-600">No active alerts.</p>
            </aside>
        )
    }

    return (
        <aside className="space-y-2 rounded-2xl border border-emerald-100 bg-white/90 p-4 shadow-sm">
            {notifications.map((item) => (
                <div
                    key={item.id}
                    className="rounded-xl bg-emerald-50 px-3 py-2 ring-1 ring-emerald-200"
                >
                    <div className="flex items-start justify-between gap-2">
                        <div>
                            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
                                {item.type}
                            </p>
                            <p className="text-sm text-slate-700">{item.message}</p>
                        </div>
                        <button
                            onClick={() => clearNotification(item.id)}
                            className="text-xs font-semibold text-emerald-700"
                        >
                            Dismiss
                        </button>
                    </div>
                </div>
            ))}
        </aside>
    )
}
