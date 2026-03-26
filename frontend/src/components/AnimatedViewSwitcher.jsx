import { useEffect, useRef, useState } from 'react'

export const AnimatedViewSwitcher = ({ options, value, onChange }) => {
    const containerRef = useRef(null)
    const [bubbleStyle, setBubbleStyle] = useState({})

    useEffect(() => {
        const updateBubble = () => {
            if (!containerRef.current) return

            const buttons = containerRef.current.querySelectorAll('[data-view-option]')
            if (buttons.length === 0) return

            const activeButton = Array.from(buttons).find(
                (btn) => btn.getAttribute('data-view-option') === value,
            )
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
        <div ref={containerRef} className="animated-switcher-container relative inline-flex items-center gap-0 rounded-full bg-slate-100 p-1">
            <div
                className="animated-switcher-bubble absolute rounded-full bg-gradient-to-r from-amber-300 to-amber-400 shadow-md transition-all duration-300 ease-out"
                style={bubbleStyle}
            />
            {options.map((option) => (
                <button
                    key={option.value}
                    data-view-option={option.value}
                    data-active={value === option.value}
                    onClick={() => onChange(option.value)}
                    className="animated-switcher-item relative z-10 rounded-full px-4 py-2 text-sm font-semibold text-slate-700 transition-all duration-300 hover:text-slate-900"
                >
                    {option.label}
                </button>
            ))}
        </div>
    )
}
