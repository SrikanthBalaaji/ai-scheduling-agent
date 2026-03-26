export const Modal = ({ isOpen, title, onClose, children }) => {
    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 p-4">
            <div className="w-full max-w-lg rounded-2xl border border-amber-100 bg-white p-6 shadow-2xl">
                <div className="mb-3 flex items-center justify-between">
                    <h3 className="text-xl font-semibold text-slate-900">{title}</h3>
                    <button
                        className="rounded-lg bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700 hover:bg-slate-200"
                        onClick={onClose}
                    >
                        Close
                    </button>
                </div>
                {children}
            </div>
        </div>
    )
}
