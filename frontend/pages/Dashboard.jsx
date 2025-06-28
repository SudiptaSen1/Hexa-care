import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/Badge';
import { useNavigate } from 'react-router-dom';
import {
  Stethoscope,
  HeartPulse,
  FileHeart,
  Clock,
  DollarSign,
  CheckCircle,
  Syringe,
  Lock,
  Brain
} from 'lucide-react';

export const Dashboard = () => {
  const navigate = useNavigate();
  const [isSubscribed, setIsSubscribed] = useState(false); // Mock subscription status

  const stats = [
    {
      title: 'Consultation Savings',
      value: '$420',
      change: '+8%',
      icon: DollarSign,
      color: 'text-green-600',
      isPremium: false,
    },
    {
      title: 'Active Appointments',
      value: '2',
      change: '+1',
      icon: Stethoscope,
      color: 'text-blue-600',
      isPremium: false,
    },
    {
      title: 'Reports Reviewed',
      value: '14',
      change: '+6',
      icon: FileHeart,
      color: 'text-purple-600',
      isPremium: true,
    },
    {
      title: 'Vital Improvements',
      value: '5',
      change: '+2',
      icon: HeartPulse,
      color: 'text-rose-600',
      isPremium: true,
    }
  ];



  return (
    <div className="space-y-8 px-10 py-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold  flex">Dashboard</h1>
          <p className=" mt-1">Welcome back! Here's your health monitoring overview.</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => navigate('/checkup')} >
            <Syringe className="mr-2 h-4 w-4" />
            Health Checkup
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {/* Services We Offer */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Services We Offer</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

          {/* Chat Service */}
          <Card
            onClick={() => navigate('/chat')}
            className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-medium">AI Health Assistant</CardTitle>
              <Brain className="h-5 w-5 text-primary" /> {/* Use Lucide's Brain icon if available */}
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Talk to our AI chatbot for health queries, tips, and personalized assistance.
              </p>
            </CardContent>
          </Card>


          {/* Upload Reports */}
          <Card
            onClick={() => navigate('/upload')}
            className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-medium">Upload Reports</CardTitle>
              <FileHeart className="h-5 w-5 text-primary" />
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Upload your health documents for review by our team.
              </p>
            </CardContent>
          </Card>

          {/* Health Timeline (Locked) */}
          <Card className="relative overflow-hidden group">
            <div className="pointer-events-none">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg font-medium">Health Timeline</CardTitle>
                <Clock className="h-5 w-5 text-primary" />
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Track your long-term health journey over time.
                </p>
              </CardContent>
            </div>
            <div className="absolute inset-0 flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 backdrop-blur-sm bg-black/30">
              <Lock className="h-8 w-8 mb-3 text-white" />
              <Button size="sm" onClick={() => navigate('/settings?tab=account')}>
                Upgrade to Pro
              </Button>
            </div>
          </Card>

          {/* RAG Summary (Locked) */}
          <Card className="relative overflow-hidden group">
            <div className="pointer-events-none">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg font-medium">RAG-based Summary</CardTitle>
                <CheckCircle className="h-5 w-5 text-primary" />
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  AI-driven Red-Amber-Green health status summary.
                </p>
              </CardContent>
            </div>
            <div className="absolute inset-0 flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 backdrop-blur-sm bg-black/30">
              <Lock className="h-8 w-8 mb-3 text-white" />
              <Button size="sm" onClick={() => navigate('/settings?tab=account')}>
                Upgrade to Pro
              </Button>
            </div>
          </Card>
        </div>
      </div>


    </div>
  );
};
