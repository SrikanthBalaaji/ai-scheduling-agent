import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import { ProtectedRoute } from './components/ProtectedRoute'
import { useAppContext } from './context/AppContext'
import { BillboardPage } from './pages/BillboardPage'
import { CalendarPage } from './pages/CalendarPage'
import { ChatPage } from './pages/ChatPage'
import { ClubDashboardPage } from './pages/ClubDashboardPage'
import { LoginPage } from './pages/LoginPage'
import { NotFoundPage } from './pages/NotFoundPage'

const AppRoutes = () => {
  const { role } = useAppContext()
  const location = useLocation()

  if (!role && location.pathname !== '/login') {
    return <Navigate to="/login" replace />
  }

  return (
    <Routes>
      <Route path="/login" element={role ? <Navigate to="/billboard" replace /> : <LoginPage />} />

      <Route
        path="/billboard"
        element={
          <ProtectedRoute roles={['student', 'club']}>
            <BillboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat"
        element={
          <ProtectedRoute roles={['student', 'club']}>
            <ChatPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/calendar"
        element={
          <ProtectedRoute roles={['student', 'club']}>
            <CalendarPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/club"
        element={
          <ProtectedRoute roles={['club']}>
            <ClubDashboardPage />
          </ProtectedRoute>
        }
      />

      <Route path="/" element={<Navigate to={role ? '/billboard' : '/login'} replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

function App() {
  const { role } = useAppContext()

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      {role && <Navbar />}
      <AppRoutes />
    </div>
  )
}

export default App
