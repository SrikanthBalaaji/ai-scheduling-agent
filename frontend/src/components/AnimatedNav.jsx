import { useEffect, useRef, useState } from 'react'
import { NavLink } from 'react-router-dom'

export const AnimatedNav = ({ links }) => {
    const containerRef = useRef(null)
    const [bubbleStyle, setBubbleStyle] = useState({})
    const [activeIndex, setActiveIndex] = useState(0)

    useEffect(() => {
        const updateBubble = () => {
            if (!containerRef.current) return

            const buttons = containerRef.current.querySelectorAll('[data-nav-item]')
            if (buttons.length === 0) return

            const activeButton = buttons[activeIndex]
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
    }, [activeIndex])

    return (
        <div ref={containerRef} className="animated-nav-container relative flex flex-wrap items-center gap-0 rounded-full bg-slate-100 p-1">
            <div
                className="animated-nav-bubble absolute rounded-full bg-gradient-to-r from-amber-300 to-amber-400 shadow-md transition-all duration-300 ease-out"
                style={bubbleStyle}
            />
            {links.map((link, index) => (
                <NavLink
                    key={link.path}
                    to={link.path}
                    data-nav-item
                    className="animated-nav-item relative z-10 rounded-full px-4 py-2 text-sm font-semibold text-slate-700 transition-all duration-300 hover:text-slate-900"
                    onClick={() => setActiveIndex(index)}
                >
                    {link.label}
                </NavLink>
            ))}
        </div>
    )
}
