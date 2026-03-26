const buildDate = (dayOffset, hour, minute = 0) => {
    const d = new Date()
    d.setDate(d.getDate() + dayOffset)
    d.setHours(hour, minute, 0, 0)
    return d.toISOString()
}

const buildFixedDate = (dateString, hour, minute = 0) => {
    const d = new Date(`${dateString}T00:00:00`)
    d.setHours(hour, minute, 0, 0)
    return d.toISOString()
}

export const academicCalendarSeed = [
    {
        id: 'fixed-25-1',
        title: 'Project Check-in',
        category: 'academic',
        dateTime: buildFixedDate('2026-03-25', 11, 0),
        durationHours: 1,
        location: 'Block B, Room 118',
    },
    {
        id: 'fixed-25-2',
        title: 'AI Club Briefing',
        category: 'events',
        dateTime: buildFixedDate('2026-03-25', 16, 30),
        durationHours: 1.5,
        location: 'Innovation Hub',
    },
    {
        id: 'fixed-26-1',
        title: 'Networks Quiz',
        category: 'exams',
        dateTime: buildFixedDate('2026-03-26', 9, 30),
        durationHours: 1,
        location: 'Exam Hall 2',
    },
    {
        id: 'fixed-26-2',
        title: 'Hackathon Prep Session',
        category: 'events',
        dateTime: buildFixedDate('2026-03-26', 15, 0),
        durationHours: 2,
        location: 'Online Meeting Room',
    },
    {
        id: 'ac-1',
        title: 'DSA Lecture',
        category: 'academic',
        dateTime: buildDate(1, 10),
        durationHours: 1.5,
        location: 'Block C, Room 204',
    },
    {
        id: 'ac-2',
        title: 'Database Lab',
        category: 'academic',
        dateTime: buildDate(3, 14),
        durationHours: 2,
        location: 'Lab 4',
    },
    {
        id: 'ex-1',
        title: 'Operating Systems Midterm',
        category: 'exams',
        dateTime: buildDate(9, 9),
        durationHours: 2,
        location: 'Exam Hall 1',
    },
]
