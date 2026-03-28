const API_BASE_URL = 'http://127.0.0.1:8000'
const DEFAULT_USER_ID = 'demo'

const normalizeChatResponse = (data) => ({
    reply:
        typeof data?.reply === 'string' && data.reply.trim()
            ? data.reply
            : 'I can help you schedule events and manage your calendar.',
    action: data?.action || 'clarify',
    recommendations: Array.isArray(data?.recommendations) ? data.recommendations : [],
    requires_confirmation: Boolean(data?.requires_confirmation),
    confirmation_token:
        data?.confirmation_token !== undefined && data?.confirmation_token !== null
            ? String(data.confirmation_token)
            : null,
    event_to_add: data?.event_to_add || null,
})

export const sendChatMessage = async ({ userId, message }) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId || DEFAULT_USER_ID,
                message,
            }),
        })

        let data = null
        try {
            data = await response.json()
        } catch {
            data = null
        }

        if (!response.ok) {
            return normalizeChatResponse({
                action: 'error',
                reply: typeof data?.detail === 'string' ? data.detail : 'Chat request failed.',
            })
        }

        return normalizeChatResponse(data)
    } catch {
        return normalizeChatResponse({
            action: 'error',
            reply: 'Unable to reach backend chat service. Ensure backend is running on port 8000.',
        })
    }
}
