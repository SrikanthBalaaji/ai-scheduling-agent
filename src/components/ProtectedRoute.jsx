import { Navigate } from 'react-router-dom'
import { useAppContext } from '../context/AppContext'

export const ProtectedRoute = ({ children, roles }) => {
    const { role } = useAppContext()

    if (!role) {
        return <Navigate to="/login" replace />
    }

    if (roles && !roles.includes(role)) {
        return <Navigate to="/billboard" replace />
    }

    return children
}
