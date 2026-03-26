import { useEffect, useRef, useState } from 'react'

export const AnimatedRoleSwitcher = ({ value, onChange }) => {
    const containerRef = useRef(null)
    const [bubbleStyle, setBubbleStyle] = useState({})

    const roles = [
        {
            value: 'student',
            label: 'Student',
            icon: (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
                    <path d="M15 20v-1a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v1" />
                    <circle cx="9" cy="7" r="4" />
                </svg>
            ),
        },
        {
            value: 'club',
            label: 'Club Member',
            icon: (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
                    <path d="M12 3l7 4v5c0 5-3.5 8-7 9-3.5-1-7-4-7-9V7l7-4z" />
                    <path d="m9.2 12.3 1.8 1.8 3.8-3.8" />
                </svg>
            ),
        },
    ]

    useEffect(() => {
        const updateBubble = () => {
            if (!containerRef.current) return

            const buttons = containerRef.current.querySelectorAll('[data-role-option]')
            if (buttons.length === 0) return

            const activeButton = Array.from(buttons).find((btn) => btn.getAttribute('data-role-option') === value)
            if (!activeButton) return

            const containerRect = containerRef.current.getBoundingClientRect()
            const buttonRect = activeButton.getBoundingClientRect()

            setBubbleStyle({
                width: `${buttonRect.width}px`,
                height: `${buttonRect.height}px`,
                left: `${buttonRect.left - containerRect.left}px`,
                top: `${buttonRect.top - containerRect.top}px`,
            })
        }

        updateBubble()
        window.addEventListener('resize', updateBubble)
        return () => window.removeEventListener('resize', updateBubble)
    }, [value])

    return (
        <div ref={containerRef} className="animated-role-container relative inline-flex items-center gap-0 rounded-full border border-amber-200 bg-amber-50 p-1">
            <div
                className="animated-role-bubble absolute rounded-full bg-gradient-to-r from-amber-300 to-amber-400 shadow-md transition-all duration-300 ease-out"
                style={bubbleStyle}
            />
            {roles.map((role) => (
                <button
                    key={role.value}
                    type="button"
                    role="radio"
                    data-role-option={role.value}
                    aria-checked={value === role.value}
                    onClick={() => onChange(role.value)}
                    className="animated-role-item relative z-10 flex items-center justify-center gap-2 rounded-full px-4 py-2.5 font-semibold transition-all duration-300"
                    style={{
                        color: value === role.value ? '#000000' : '#7c5a2a',
                    }}
                >
                    {role.icon}
                    <span>{role.label}</span>
                </button>
            ))}
        </div>
    )
}
