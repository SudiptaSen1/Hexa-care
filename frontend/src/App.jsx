import { createBrowserRouter, RouterProvider } from "react-router-dom"
import Home from "../components/Home"
import { ThemeProvider } from "../components/ThemeProvider"
import { Landing } from "../pages/Landing"
import MainLayout from "../layout/MainLayout"
import { Dashboard } from "../pages/Dashboard"
import Login from "../pages/Login"
import { Chat } from "../pages/Chat"
import Notification from "../pages/Notification"

const appRouter = createBrowserRouter([
	{
		path: '/',
		element: <MainLayout />,
    children: [
      {
        path: '/',
        element: 
          <>
            <Landing />
          </>
      },
      {
        path: '/login',
        element: 
          <>
            <Login />
          </>
      },
      {
        path: '/dashboard',
        element:
          <>
            <Dashboard />
          </>
      },
      {
        path: '/chat',
        element:
          <>
            <Chat />
          </>
      },
      {
        path: '/notification',
        element:
          <>
            <Notification />
          </>
      }
    ]
	}
])

function App() {

  return (
    <>
      <ThemeProvider>

        <RouterProvider router={appRouter} />

      </ThemeProvider>
      
    </>
  )
}

export default App
