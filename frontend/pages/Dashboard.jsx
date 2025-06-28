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
  Lock
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

  const recentSessions = [
    {
      id: '1',
      title: 'Cardiology Checkup',
      status: 'active',
      lastMessage: 'Your ECG report shows improvement...',
      timestamp: '2 hours ago'
    },
    {
      id: '2',
      title: 'Diabetes Consultation',
      status: 'completed',
      lastMessage: 'HbA1c levels are stable...',
      timestamp: '1 day ago'
    },
    {
      id: '3',
      title: 'General Health Review',
      status: 'active',
      lastMessage: 'Continue with your current medication...',
      timestamp: '2 days ago'
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
          <Button onClick={() => navigate('/checkup')} variant="outline">
            <Syringe className="mr-2 h-4 w-4" />
            Health Checkup
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return stat.isPremium && !isSubscribed ? (
            <Card key={index} className="relative overflow-hidden  group">
              <div className="pointer-events-none">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium ">
                    {stat.title}
                  </CardTitle>
                  <Icon className="h-4 w-4 " />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold ">{stat.value}</div>
                  <p className="text-xs text-muted-foreground">
                    <span className="">{stat.change}</span> from last check
                  </p>
                </CardContent>
              </div>
              <div className="absolute inset-0 flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300  backdrop-blur-sm">
                <Lock className="h-8 w-8  drop-shadow-lg mb-3" />
                <Button size="sm" onClick={() => navigate('/settings?tab=account')}>
                  Upgrade to Pro
                </Button>
              </div>
            </Card>
          ) : (
            <Card key={index} className="relative overflow-hidden">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium ">
                  {stat.title}
                </CardTitle>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">
                  <span className="text-pink-600">{stat.change}</span> from last check
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Recent Consultations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Recent Consultations</CardTitle>
              <CardDescription>Your latest health check sessions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentSessions.map((session) => (
                  <div
                    key={session.id}
                    className="flex items-center justify-between p-4 border rounded-lg  transition-colors cursor-pointer"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <Stethoscope className="h-8 w-8 text-red-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {session.title}
                        </p>
                        <p className="text-sm  truncate">
                          {session.lastMessage}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant={session.status === 'active' ? 'default' : 'secondary'}>
                        {session.status === 'active' ? (
                          <Clock className="mr-1 h-3 w-3" />
                        ) : (
                          <CheckCircle className="mr-1 h-3 w-3" />
                        )}
                        {session.status}
                      </Badge>
                      <span className="text-xs ">{session.timestamp}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
