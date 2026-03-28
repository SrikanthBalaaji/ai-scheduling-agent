import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { mockUser } from '../data/mockEvents'
import { eventsApi } from '../services/api'

const AppContext = createContext(null)

const HOURS_24 = 24 * 60 * 60 * 1000

const buildNotifications = (events) => {
    const now = Date.now()

    return events
        .flatMap((event) => {
            const eventTime = new Date(event.dateTime).getTime()
            const deadlineTime = new Date(event.registrationDeadline).getTime()
            const notifications = []

            if (eventTime > now && eventTime - now <= HOURS_24) {
                notifications.push({
                    id: `start-${event.id}`,
                    type: 'Event starts soon',
                    message: `${event.title} starts within 24 hours.`,
                })
            }

            if (deadlineTime > now && deadlineTime - now <= HOURS_24) {
                notifications.push({
                    id: `deadline-${event.id}`,
                    type: 'Registration closing',
                    message: `Registration for ${event.title} closes soon.`,
                })
            }

            return notifications
        })
        .slice(0, 6)
}

export const AppProvider = ({ children }) => {
    const [user, setUser] = useState(null)
    const [events, setEvents] = useState([])
    const [calendarEntries, setCalendarEntries] = useState([])
    const [registeredEventIds, setRegisteredEventIds] = useState(new Set())
    const [notifications, setNotifications] = useState([])
    const [loading, setLoading] = useState(false)
    const [theme, setTheme] = useState(() => {
        const stored = localStorage.getItem('planner-theme')
        if (stored === 'dark' || stored === 'light') {
            return stored
        }

        return window.matchMedia('(prefers-color-scheme: dark)').matches
            ? 'dark'
            : 'light'
    })

    const role = user?.role || null

    const refreshData = async () => {
        setLoading(true)
        try {
            const [eventsResponse, calendarResponse] = await Promise.all([
                eventsApi.getEvents(),
                eventsApi.getCalendar(),
            ])

            setEvents(eventsResponse.data)
            setCalendarEntries(calendarResponse.data)
            setNotifications(buildNotifications(eventsResponse.data))
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        refreshData()
    }, [])

    useEffect(() => {
        document.documentElement.classList.toggle('dark', theme === 'dark')
        localStorage.setItem('planner-theme', theme)
    }, [theme])

    const MOCK_USERS = [
        { username: 'alice', password: 'pass123', role: 'student' },
        { username: 'bob', password: 'club456', role: 'club' },
    ]

    const login = (payload) => {
        // Preferred path: user object returned by backend auth APIs.
        if (payload?.id) {
            setUser({
                id: payload.id,
                name: payload.name,
                role: payload.role || 'student',
                interests: payload.interests || [],
            })
            return { success: true, role: payload.role || 'student' }
        }

        // Backward compatibility path: local mock credential object.
        if (payload?.username && payload?.password) {
            const match = MOCK_USERS.find(
                (u) => u.username === payload.username && u.password === payload.password,
            )

            if (!match) {
                return { success: false, error: 'Invalid username or password.' }
            }

            setUser({
                ...mockUser,
                name: match.username,
                role: match.role,
                interests: payload.interests || [],
                id: `user-${Date.now()}`,
            })
            return { success: true, role: match.role }
        }

        // Fallback shape support.
        setUser({
            ...mockUser,
            name: payload?.name || 'User',
            role: payload?.role || 'student',
            interests: payload?.interests || [],
            id: `user-${Date.now()}`,
        })
        return { success: true, role: payload?.role || 'student' }
    }

    const logout = () => {
        setUser(null)
        setRegisteredEventIds(new Set())
    }

    const registerForEvent = async (eventId, formPayload = {}) => {
        if (!user) return { success: false }

        await eventsApi.register(eventId, user.id, formPayload)
        setRegisteredEventIds((prev) => new Set([...prev, eventId]))
        await refreshData()
        return { success: true }
    }

    const createClubEvent = async (payload) => {
        const response = await eventsApi.createEvent(payload)
        setEvents((prev) => [response.data, ...prev])
        await refreshData()
    }

    const updateClubEvent = async (eventId, payload) => {
        await eventsApi.updateEvent(eventId, payload)
        await refreshData()
    }

    const deleteClubEvent = async (eventId) => {
        await eventsApi.deleteEvent(eventId)
        await refreshData()
    }

    const duplicateClubEvent = async (event) => {
        const sourceDeadline = event.registrationDeadline || event.dateTime
        const duplicated = {
            ...event,
            title: `${event.title} (Copy)`,
            dateTime: new Date(new Date(event.dateTime).getTime() + HOURS_24).toISOString(),
            registrationDeadline: new Date(
                new Date(sourceDeadline).getTime() + HOURS_24,
            ).toISOString(),
        }

        delete duplicated.id
        await createClubEvent(duplicated)
    }

    const addCalendarEntry = async (entry) => {
        setCalendarEntries((prev) => [entry, ...prev])
    }

    const clearNotification = (notificationId) => {
        setNotifications((prev) => prev.filter((item) => item.id !== notificationId))
    }

    const toggleTheme = () => {
        setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
    }

    const value = useMemo(
        () => ({
            user,
            role,
            events,
            calendarEntries,
            registeredEventIds,
            notifications,
            loading,
            theme,
            login,
            logout,
            refreshData,
            registerForEvent,
            createClubEvent,
            updateClubEvent,
            deleteClubEvent,
            duplicateClubEvent,
            addCalendarEntry,
            clearNotification,
            toggleTheme,
        }),
        [
            user,
            role,
            events,
            calendarEntries,
            registeredEventIds,
            notifications,
            loading,
            theme,
        ],
    )

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export const useAppContext = () => {
    const context = useContext(AppContext)
    if (!context) {
        throw new Error('useAppContext must be used within AppProvider')
    }
    return context
}
