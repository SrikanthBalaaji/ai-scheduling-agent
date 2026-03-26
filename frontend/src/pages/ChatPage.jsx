import { useMemo, useState } from 'react'
import { ChatBubble } from '../components/ChatBubble'
import { useAppContext } from '../context/AppContext'
import { sendChatMessage } from '../services/chatService'

const getEventByMessage = (events, message) => {
    const lowered = message.toLowerCase()
    return events.find((event) => lowered.includes(event.title.toLowerCase()))
}

export const ChatPage = () => {
    const { events, addCalendarEntry } = useAppContext()
    const [messages, setMessages] = useState([
        {
            id: 'welcome',
            sender: 'bot',
            message:
                'Hi, I can schedule events and add them to your calendar. Try: "Add CodeSprint 24H Hackathon to my calendar".',
        },
    ])
    const [input, setInput] = useState('')
    const [remindMe, setRemindMe] = useState(true)

    const sortedMessages = useMemo(() => messages, [messages])

    const handleSend = async () => {
        const message = input.trim()
        if (!message) return

        setMessages((prev) => [...prev, { id: `${Date.now()}-u`, sender: 'user', message }])
        setInput('')

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

            setMessages((prev) => [...prev, { id: `${Date.now()}-b`, sender: 'bot', message: followUp }])
            return
        }

        const response = await sendChatMessage(message)
        const reply = remindMe ? `${response.reply} Reminder: ON.` : response.reply

        setMessages((prev) => [...prev, { id: `${Date.now()}-b`, sender: 'bot', message: reply }])
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
                <div className="flex-1 space-y-3 overflow-y-auto pr-1">
                    {sortedMessages.map((item) => (
                        <ChatBubble key={item.id} sender={item.sender} message={item.message} />
                    ))}
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
                        placeholder="Type your message..."
                        className="flex-1 rounded-xl border border-slate-300 px-3 py-2"
                    />
                    <button
                        onClick={handleSend}
                        className="rounded-xl bg-slate-900 px-4 py-2 font-semibold text-white hover:bg-slate-800"
                    >
                        Send
                    </button>
                </div>
            </section>
        </main>
    )
}
