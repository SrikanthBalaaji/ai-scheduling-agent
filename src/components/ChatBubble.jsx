export const ChatBubble = ({ message, sender }) => {
    const isUser = sender === 'user'

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm md:text-base ${isUser
                        ? 'bg-slate-900 text-white'
                        : 'bg-amber-100 text-slate-900 ring-1 ring-amber-200'
                    }`}
            >
                {message}
            </div>
        </div>
    )
}
