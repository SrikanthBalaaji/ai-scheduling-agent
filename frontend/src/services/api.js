import axios from 'axios'
import { academicCalendarSeed } from '../data/mockCalendar'

const api = axios.create({
    baseURL: '/api',
    timeout: 5000,
})

let eventsStore = []
let calendarStore = [...academicCalendarSeed]
let registrationMap = {}
let registrationDetailsStore = {}

const sleep = (ms = 250) => new Promise((resolve) => setTimeout(resolve, ms))

const byDate = (a, b) => new Date(a.dateTime) - new Date(b.dateTime)

const defaultPosterUrl =
    'https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=1200&q=80'

const toIso = (date, time = '09:00') => {
    if (!date) return new Date().toISOString()
    const safeTime = time && /^\d{2}:\d{2}$/.test(time) ? time : '09:00'
    return `${date}T${safeTime}:00`
}

const inferType = (tags) => {
    if (!Array.isArray(tags) || tags.length === 0) return 'event'
    return String(tags[0]).toLowerCase()
}

const formatDate = (dateObj) => {
    const year = dateObj.getFullYear()
    const month = String(dateObj.getMonth() + 1).padStart(2, '0')
    const day = String(dateObj.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
}

const formatTime = (dateObj) => {
    const hours = String(dateObj.getHours()).padStart(2, '0')
    const minutes = String(dateObj.getMinutes()).padStart(2, '0')
    return `${hours}:${minutes}`
}

const toBackendEventPayload = (eventPayload) => {
    const start = new Date(eventPayload.dateTime || Date.now())
    const end = new Date(start.getTime() + 2 * 60 * 60 * 1000)

    return {
        title: eventPayload.title,
        date: formatDate(start),
        start_time: formatTime(start),
        end_time: formatTime(end),
        tags: [eventPayload.type || 'event'],
        campus: eventPayload.clubName || 'Main',
        description: eventPayload.description || '',
        club_name: eventPayload.clubName || '',
        location: eventPayload.location || 'Main Campus',
        mode: eventPayload.mode || 'offline',
        event_type: eventPayload.type || 'event',
        poster_url: eventPayload.posterUrl || defaultPosterUrl,
        google_form_url: eventPayload.googleFormUrl || '',
    }
}

const toFrontendEvent = (event) => {
    const dateTime = toIso(event?.date, event?.start_time)
    const deadline = new Date(dateTime)
    deadline.setDate(deadline.getDate() - 1)
    deadline.setHours(23, 59, 0, 0)

    return {
        id: String(event?.id ?? `ev-${Date.now()}`),
        title: event?.title || 'Untitled Event',
        description: event?.description || '',
        clubName: event?.club_name || event?.campus || 'Campus Events',
        dateTime,
        location: event?.location || '',
        campus: event?.campus || 'Main',
        mode: event?.mode || 'offline',
        type: event?.event_type || inferType(event?.tags),
        posterUrl: event?.poster_url || defaultPosterUrl,
        registrations: 0,
        googleFormUrl: event?.google_form_url || '',
        registrationDeadline: deadline.toISOString(),
        registrationFields: ['name', 'srn', 'semester'],
        customFields: [],
    }
}

export const eventsApi = {
    async getEvents() {
        try {
            const response = await api.get('/events')
            const normalized = (response.data || []).map(toFrontendEvent).sort(byDate)
            eventsStore = normalized
            return { data: normalized, status: response.status, request: response.request || api.defaults }
        } catch (_error) {
            await sleep()
            return { data: [...eventsStore].sort(byDate), status: 200, request: api.defaults }
        }
    },

    async createEvent(eventPayload) {
        const backendPayload = toBackendEventPayload(eventPayload)
        const response = await api.post('/events', backendPayload)
        const normalized = toFrontendEvent(response.data)
        eventsStore = [normalized, ...eventsStore.filter((event) => event.id !== normalized.id)]
        return { data: normalized, status: response.status, request: response.request || api.defaults }
    },

    async updateEvent(eventId, payload) {
        const backendPayload = toBackendEventPayload(payload)
        const response = await api.put(`/events/${eventId}`, backendPayload)
        const normalized = toFrontendEvent(response.data)
        eventsStore = eventsStore.map((event) =>
            event.id === eventId ? normalized : event,
        )
        return { data: normalized, status: response.status, request: response.request || api.defaults }
    },

    async deleteEvent(eventId) {
        await api.delete(`/events/${eventId}`)
        eventsStore = eventsStore.filter((event) => event.id !== eventId)
        calendarStore = calendarStore.filter((entry) => entry.sourceEventId !== eventId)
        return { data: { success: true }, status: 200, request: api.defaults }
    },

    async register(eventId, userId, formPayload = {}) {
        await sleep()
        const targetEvent = eventsStore.find((event) => event.id === eventId)
        if (!targetEvent) {
            throw new Error('Event not found')
        }

        registrationMap[userId] = registrationMap[userId] || new Set()
        if (!registrationMap[userId].has(eventId)) {
            registrationMap[userId].add(eventId)
            targetEvent.registrations += 1
            registrationDetailsStore[eventId] = registrationDetailsStore[eventId] || []
            registrationDetailsStore[eventId].push({
                userId,
                submittedAt: new Date().toISOString(),
                formPayload,
            })

            calendarStore.push({
                id: `cal-${Date.now()}`,
                sourceEventId: targetEvent.id,
                title: targetEvent.title,
                category: 'events',
                dateTime: targetEvent.dateTime,
                durationHours: 2,
                location: targetEvent.location,
            })
        }

        return {
            data: {
                success: true,
                event: targetEvent,
                registration: registrationDetailsStore[eventId]?.find((item) => item.userId === userId),
            },
            status: 200,
            request: api.defaults,
        }
    },

    async getCalendar() {
        await sleep()
        return { data: [...calendarStore].sort(byDate), status: 200, request: api.defaults }
    },
}
