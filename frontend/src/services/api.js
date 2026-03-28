import axios from 'axios'
import { mockEvents } from '../data/mockEvents'
import { academicCalendarSeed } from '../data/mockCalendar'

const api = axios.create({
    baseURL: '/api',
    timeout: 5000,
})

let eventsStore = [...mockEvents]
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

const toFrontendEvent = (event) => {
    const dateTime = toIso(event?.date, event?.start_time)
    const deadline = new Date(dateTime)
    deadline.setDate(deadline.getDate() - 1)
    deadline.setHours(23, 59, 0, 0)

    return {
        id: String(event?.id ?? `ev-${Date.now()}`),
        title: event?.title || 'Untitled Event',
        description: event?.description || '',
        clubName: event?.campus ? `${event.campus} Campus` : 'Campus Events',
        dateTime,
        location: event?.campus ? `${event.campus} Campus` : 'Main Campus',
        mode: 'offline',
        type: inferType(event?.tags),
        posterUrl: defaultPosterUrl,
        registrations: 0,
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
        await sleep()
        const newEvent = {
            ...eventPayload,
            id: `ev-${Date.now()}`,
            registrations: 0,
        }
        eventsStore = [newEvent, ...eventsStore]
        return { data: newEvent, status: 201, request: api.defaults }
    },

    async updateEvent(eventId, payload) {
        await sleep()
        eventsStore = eventsStore.map((event) =>
            event.id === eventId ? { ...event, ...payload } : event,
        )
        const updated = eventsStore.find((event) => event.id === eventId)
        return { data: updated, status: 200, request: api.defaults }
    },

    async deleteEvent(eventId) {
        await sleep()
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
