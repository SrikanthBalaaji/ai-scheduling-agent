const responseMap = [
    {
        match: /schedule|add.*calendar|register/i,
        answer:
            'I can help with that. Mention an event title and I will add it to your calendar if it exists.',
    },
    {
        match: /remind/i,
        answer:
            'Reminder enabled. I will trigger a mock alert before the event starts.',
    },
    {
        match: /hackathon|guest talk|cultural|workshop|expo/i,
        answer:
            'You can find that on Billboard. Use filters for type, date, mode, and popularity.',
    },
]

export const sendChatMessage = async (message) => {
    await new Promise((resolve) => setTimeout(resolve, 250))

    const match = responseMap.find((item) => item.match.test(message))
    return {
        reply:
            match?.answer ||
            'I can help you schedule events, set reminders, and manage calendar entries.',
    }
}
