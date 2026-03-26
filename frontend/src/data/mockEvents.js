const buildDate = (dayOffset, hour, minute = 0) => {
    const d = new Date()
    d.setDate(d.getDate() + dayOffset)
    d.setHours(hour, minute, 0, 0)
    return d.toISOString()
}

export const mockEvents = [
    {
        id: 'ev-101',
        title: 'CodeSprint 24H Hackathon',
        description: 'Build, pitch, and deploy in 24 hours with mentors on-site.',
        clubName: 'Coding Nexus',
        dateTime: buildDate(3, 9),
        location: 'Innovation Lab A',
        mode: 'offline',
        type: 'hackathon',
        posterUrl:
            'https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&w=1200&q=80',
        registrations: 212,
        registrationDeadline: buildDate(2, 18),
    },
    {
        id: 'ev-102',
        title: 'Generative AI Guest Talk',
        description: 'Industry experts discuss AI agents, tooling, and careers.',
        clubName: 'AI Circle',
        dateTime: buildDate(5, 16, 30),
        location: 'Seminar Hall 2',
        mode: 'offline',
        type: 'guest talk',
        posterUrl:
            'https://images.unsplash.com/photo-1677442135722-5f7eaf4d1a14?auto=format&fit=crop&w=1200&q=80',
        registrations: 160,
        registrationDeadline: buildDate(4, 23),
    },
    {
        id: 'ev-103',
        title: 'Cultural Night 2026',
        description: 'Music, dance, stand-up, and open mic under the stars.',
        clubName: 'Cultural Council',
        dateTime: buildDate(12, 18),
        location: 'Main Quadrangle',
        mode: 'offline',
        type: 'culturals',
        posterUrl:
            'https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=1200&q=80',
        registrations: 340,
        registrationDeadline: buildDate(10, 20),
    },
    {
        id: 'ev-104',
        title: 'Open Source Bootcamp',
        description: 'Hands-on onboarding to contribute to open source projects.',
        clubName: 'Dev Guild',
        dateTime: buildDate(8, 10),
        location: 'Online Meeting Room',
        mode: 'online',
        type: 'workshop',
        posterUrl:
            'https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=1200&q=80',
        registrations: 121,
        registrationDeadline: buildDate(7, 17),
    },
    {
        id: 'ev-105',
        title: 'Robotics Expo',
        description: 'Showcase autonomous bots and embedded innovation demos.',
        clubName: 'Mecha Minds',
        dateTime: buildDate(15, 11),
        location: 'Mechanical Block Atrium',
        mode: 'offline',
        type: 'expo',
        posterUrl:
            'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=1200&q=80',
        registrations: 98,
        registrationDeadline: buildDate(14, 16),
    },
    {
        id: 'ev-106',
        title: 'Product Design Jam',
        description: 'Rapid ideation and UX prototyping challenge for teams.',
        clubName: 'Design Spectrum',
        dateTime: buildDate(6, 14),
        location: 'Studio B',
        mode: 'offline',
        type: 'competition',
        posterUrl:
            'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1200&q=80',
        registrations: 188,
        registrationDeadline: buildDate(5, 19),
    },
    {
        id: 'ev-107',
        title: 'Career Prep Sprint',
        description: 'Resume reviews, mock interviews, and networking circles.',
        clubName: 'Placement Cell',
        dateTime: buildDate(2, 15),
        location: 'Online Meeting Room',
        mode: 'online',
        type: 'career',
        posterUrl:
            'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1200&q=80',
        registrations: 264,
        registrationDeadline: buildDate(1, 20),
    },
    {
        id: 'ev-108',
        title: 'Past Event Placeholder',
        description: 'Used to verify past events are hidden from billboard.',
        clubName: 'Archive Club',
        dateTime: buildDate(-2, 9),
        location: 'Old Hall',
        mode: 'offline',
        type: 'guest talk',
        posterUrl:
            'https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=1200&q=80',
        registrations: 77,
        registrationDeadline: buildDate(-3, 18),
    },
]

export const interestOptions = [
    'hackathon',
    'guest talk',
    'culturals',
    'workshop',
    'expo',
    'competition',
    'career',
]

export const mockUser = {
    id: 'user-1',
    name: 'Student User',
    role: 'student',
    interests: ['hackathon', 'guest talk', 'workshop'],
}
