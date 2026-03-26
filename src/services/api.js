import axios from 'axios'
import { mockEvents } from '../data/mockEvents'
import { academicCalendarSeed } from '../data/mockCalendar'

const api = axios.create({
    baseURL: '/api',
    timeout: 1000,
})

let eventsStore = [...mockEvents]
let calendarStore = [...academicCalendarSeed]
let registrationMap = {}

const sleep = (ms = 250) => new Promise((resolve) => setTimeout(resolve, ms))

const byDate = (a, b) => new Date(a.dateTime) - new Date(b.dateTime)

export const eventsApi = {
    async getEvents() {
        await sleep()
        return { data: [...eventsStore].sort(byDate), status: 200, request: api.defaults }
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

    async register(eventId, userId) {
        await sleep()
        const targetEvent = eventsStore.find((event) => event.id === eventId)
        if (!targetEvent) {
            throw new Error('Event not found')
        }

        registrationMap[userId] = registrationMap[userId] || new Set()
        if (!registrationMap[userId].has(eventId)) {
            registrationMap[userId].add(eventId)
            targetEvent.registrations += 1

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

        return { data: { success: true, event: targetEvent }, status: 200, request: api.defaults }
    },

    async getCalendar() {
        await sleep()
        return { data: [...calendarStore].sort(byDate), status: 200, request: api.defaults }
    },
}
