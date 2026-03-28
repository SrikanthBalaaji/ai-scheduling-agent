import { useMemo, useState } from 'react'
import { ChatBubble } from '../components/ChatBubble'
import { useAppContext } from '../context/AppContext'
import { sendChatMessage } from '../services/chatService'

const formatEventWindow = (event) => {
    if (!event) return ''
    if (event.date && event.start_time && event.end_time) {
        return `${event.date} | ${event.start_time}-${event.end_time}`
    }
    return ''
}

const getEventByMessage = (events, message) => {
    const lowered = message.toLowerCase()
    return events.find((event) => lowered.includes(event.title.toLowerCase()))
}

export const ChatPage = () => {
    const { user, events, addCalendarEntry } = useAppContext()
    const [messages, setMessages] = useState([
        {
            id: 'welcome',
            sender: 'bot',
            message:
                'Hi, I can schedule events and add them to your calendar. Try: "Add CodeSprint 24H Hackathon to my calendar".',
            recommendations: [],
            requiresConfirmation: false,
            confirmationToken: null,
        },
    ])
    const [input, setInput] = useState('')
    const [remindMe, setRemindMe] = useState(true)
    const [isSending, setIsSending] = useState(false)
    const [chatError, setChatError] = useState('')

    const sortedMessages = useMemo(() => messages, [messages])

    const handleSend = async () => {
        const message = input.trim()
        if (!message || isSending) return

        setChatError('')
        setIsSending(true)

        setMessages((prev) => [...prev, { id: `${Date.now()}-u`, sender: 'user', message }])
        setInput('')

        try {
            const mentionedEvent = getEventByMessage(events, message)

            if (mentionedEvent && /add|schedule|register/i.test(message)) {
                await addCalendarEntry({
                    id: `chat-${Date.now()}`,
                    sourceEventId: mentionedEvent.id,
                    title: mentionedEvent.title,
                    category: 'events',
                    dateTime: mentionedEvent.dateTime,
                    durationHours: 2,
                    location: mentionedEvent.location,
                })

                const followUp = remindMe
                    ? `Added ${mentionedEvent.title} to calendar and reminder enabled.`
                    : `Added ${mentionedEvent.title} to calendar.`

                setMessages((prev) => [...prev, {
                    id: `${Date.now()}-b`,
                    sender: 'bot',
                    message: followUp,
                    recommendations: [],
                    requiresConfirmation: false,
                    confirmationToken: null,
                }])
                return
            }

            const response = await sendChatMessage({
                userId: user?.id,
                message,
            })

            if (response?.action === 'error') {
                setChatError(response.reply)
            }

            if (response?.action === 'add_to_calendar' && response?.event_to_add) {
                const event = response.event_to_add
                const start = event.start_time || '09:00'
                const date = event.date || new Date().toISOString().slice(0, 10)
                await addCalendarEntry({
                    id: `chat-${Date.now()}`,
                    sourceEventId: null,
                    title: event.title || 'Untitled Event',
                    category: 'events',
                    dateTime: `${date}T${start}:00`,
                    durationHours: 2,
                    location: 'Calendar',
                })
            }

            const reply = remindMe ? `${response.reply} Reminder: ON.` : response.reply

            setMessages((prev) => [...prev, {
                id: `${Date.now()}-b`,
                sender: 'bot',
                message: reply,
                action: response.action,
                recommendations: response.recommendations || [],
                requiresConfirmation: Boolean(response.requires_confirmation),
                confirmationToken: response.confirmation_token || null,
            }])
        } finally {
            setIsSending(false)
        }
    }

    return (
        <main className="mx-auto flex w-full max-w-5xl flex-col gap-4 px-4 py-6">
            <section className="rounded-3xl bg-[linear-gradient(125deg,#a16207,#f59e0b,#fef3c7)] p-6 shadow-lg">
                <h1 className="text-3xl font-black text-slate-900">AI Assistant</h1>
                <p className="mt-1 text-sm text-slate-800">
                    Schedule events with natural text and manage reminders.
                </p>
            </section>

            <section className="flex min-h-[420px] flex-col gap-3 rounded-3xl border border-amber-200 bg-white p-4 shadow-sm">
                {chatError && (
                    <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                        {chatError}
                    </div>
                )}

                <div className="flex-1 space-y-3 overflow-y-auto pr-1">
                    {sortedMessages.map((item) => {
                        const hasRecommendations =
                            item.sender === 'bot' &&
                            Array.isArray(item.recommendations) &&
                            item.recommendations.length > 0

                        return (
                            <div key={item.id} className="space-y-2">
                                <ChatBubble sender={item.sender} message={item.message} />

                                {hasRecommendations && (
                                    <div className="ml-0 rounded-xl border border-amber-200 bg-amber-50 p-3">
                                        <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">
                                            Recommended events
                                        </p>
                                        <div className="mt-2 space-y-2">
                                            {item.recommendations.map((rec) => {
                                                const ev = rec?.event || {}
                                                const eventId = ev.id || 'N/A'
                                                const windowLabel = formatEventWindow(ev)

                                                return (
                                                    <div
                                                        key={`${item.id}-${eventId}`}
                                                        className="rounded-lg border border-amber-200 bg-white p-3"
                                                    >
                                                        <p className="text-sm font-bold text-slate-900">
                                                            [{eventId}] {ev.title || 'Untitled event'}
                                                        </p>
                                                        {windowLabel && (
                                                            <p className="mt-1 text-xs text-slate-600">{windowLabel}</p>
                                                        )}
                                                        {rec?.reason && (
                                                            <p className="mt-1 text-xs text-slate-700">Reason: {rec.reason}</p>
                                                        )}
                                                        {typeof rec?.score === 'number' && (
                                                            <p className="mt-1 text-xs text-slate-700">
                                                                Score: {rec.score.toFixed(1)}
                                                            </p>
                                                        )}
                                                    </div>
                                                )
                                            })}
                                        </div>

                                        {item.requiresConfirmation && (
                                            <p className="mt-3 text-xs font-semibold text-slate-800">
                                                Confirm by typing: yes &lt;event_id&gt;
                                            </p>
                                        )}
                                    </div>
                                )}
                            </div>
                        )
                    })}

                    {isSending && (
                        <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-slate-700">
                            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-amber-500" />
                            Assistant is thinking...
                        </div>
                    )}
                </div>

                <div className="flex items-center justify-between rounded-xl bg-amber-50 px-3 py-2">
                    <label className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                        <input
                            type="checkbox"
                            checked={remindMe}
                            onChange={(e) => setRemindMe(e.target.checked)}
                        />
                        Remind me
                    </label>
                </div>

                <div className="flex gap-2">
                    <input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        disabled={isSending}
                        placeholder="Type your message..."
                        className="flex-1 rounded-xl border border-slate-300 px-3 py-2 disabled:cursor-not-allowed disabled:opacity-60"
                    />
                    <button
                        onClick={handleSend}
                        disabled={isSending}
                        className="rounded-xl bg-slate-900 px-4 py-2 font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                        {isSending ? 'Sending...' : 'Send'}
                    </button>
                </div>
            </section>
        </main>
    )
}
