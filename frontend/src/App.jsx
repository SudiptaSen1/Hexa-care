import { createBrowserRouter, RouterProvider } from "react-router-dom"
import { ThemeProvider } from "../components/ThemeProvider"
import { AuthProvider } from "./context/AuthContext"
import { Landing } from "../pages/Landing"
import MainLayout from "../layout/MainLayout"
import { Dashboard } from "../pages/Dashboard"
import Login from "../pages/Login"
import Chat from "../pages/Chat"
import Notification from "../pages/Notification"
import Upload from "../pages/Upload"
import MedicationTracking from "../pages/MedicationTracking"

const appRouter = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        path: '/',
        element: <Landing />
      },
      {
        path: '/login',
        element: <Login />
      },
      {
        path: '/dashboard',
        element: <Dashboard />
      },
      {
        path: '/chat',
        element: <Chat />
      },
      {
        path: '/notification',
        element: <Notification />
      },
      {
        path: '/upload',
        element: <Upload />
      },
      {
        path: '/medication-tracking',
        element: <MedicationTracking />
      }
    ]
  }
])

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <RouterProvider router={appRouter} />
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App