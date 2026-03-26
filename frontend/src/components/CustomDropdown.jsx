import { useEffect, useRef, useState } from 'react'

export const CustomDropdown = ({ options, value, onChange, icon: IconComponent }) => {
    const [isOpen, setIsOpen] = useState(false)
    const containerRef = useRef(null)

    const selectedLabel = options.find((opt) => opt.value === value)?.label || 'Select'

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) {
                setIsOpen(false)
            }
        }

        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    const handleSelect = (optionValue) => {
        onChange(optionValue)
        setIsOpen(false)
    }

    return (
        <div ref={containerRef} className="custom-dropdown relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="custom-dropdown-trigger w-full rounded-xl border border-slate-300/90 bg-white/90 px-10 py-2.5 text-sm font-semibold text-slate-800 shadow-sm transition-all duration-200 hover:border-slate-400 focus:border-amber-300 focus:outline-none focus:ring-2 focus:ring-amber-200/80 flex items-center justify-between"
                aria-expanded={isOpen}
                aria-haspopup="listbox"
            >
                <div className="flex items-center gap-2">
                    {IconComponent && (
                        <IconComponent className="h-4 w-4 text-slate-400" />
                    )}
                    <span>{selectedLabel}</span>
                </div>
                <svg
                    viewBox="0 0 20 20"
                    aria-hidden="true"
                    className={`h-4 w-4 text-slate-500 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}
                >
                    <path fill="currentColor" d="M5.23 7.21 10 11.98l4.77-4.77 1.42 1.42L10 14.82 3.81 8.63z" />
                </svg>
            </button>

            {isOpen && (
                <div
                    className="custom-dropdown-menu absolute top-full left-0 right-0 z-50 mt-2 rounded-xl border border-slate-200 bg-white shadow-lg overflow-hidden"
                >
                    <ul role="listbox" className="py-1">
                        {options.map((option) => (
                            <li key={option.value}>
                                <button
                                    onClick={() => handleSelect(option.value)}
                                    role="option"
                                    aria-selected={value === option.value}
                                    className={`custom-dropdown-item w-full px-4 py-2.5 text-left text-sm font-medium transition-all duration-150 ${value === option.value
                                            ? 'bg-gradient-to-r from-amber-300 to-amber-400 text-slate-900'
                                            : 'text-slate-700 hover:bg-slate-50'
                                        }`}
                                >
                                    {option.label}
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    )
}
