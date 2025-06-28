import { ScanHeart } from 'lucide-react'
import React from 'react'
import DarkMode from '../src/DarkMode'

const Navbar = () => {
  return (
    <header className="border-b backdrop-blur-md">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ScanHeart className="h-8 w-8 text-primary" />
            <span className="text-2xl font-bold bg-primary bg-clip-text text-transparent">
              HexaCare
            </span>
          </div>
          <div className="flex items-center space-x-4">
            <DarkMode />
          </div>
        </div>
      </header>
  )
}

export default Navbar
