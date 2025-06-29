import { ScanHeart, LogOut, User } from 'lucide-react'
import React from 'react'
import DarkMode from '../src/DarkMode'
import { useAuth } from '../src/context/AuthContext'
import { Button } from './ui/button'
import { useNavigate } from 'react-router-dom'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu'

const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="border-b backdrop-blur-md">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div 
          className="flex items-center space-x-2 cursor-pointer"
          onClick={() => navigate('/')}
        >
          <ScanHeart className="h-8 w-8 text-primary" />
          <span className="text-2xl font-bold bg-primary bg-clip-text text-transparent">
            HexaCare
          </span>
        </div>
        
        <div className="flex items-center space-x-4">
          <DarkMode />
          
          {isAuthenticated ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <User className="h-4 w-4 mr-2" />
                  {user?.username}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => navigate('/dashboard')}>
                  Dashboard
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/upload')}>
                  Upload Prescription
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/chat')}>
                  AI Assistant
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/medication-tracking')}>
                  Medication Tracking
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="h-4 w-4 mr-2" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={() => navigate('/login')}>
                Sign In
              </Button>
              <Button size="sm" onClick={() => navigate('/login')}>
                Sign Up
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

export default Navbar