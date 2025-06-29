import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/Badge';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../src/context/AuthContext';
import { apiCall, API_ENDPOINTS } from '../src/config/api';
import {
  Stethoscope,
  HeartPulse,
  FileHeart,
  Clock,
  DollarSign,
  CheckCircle,
  Syringe,
  Lock,
  Brain,
  Upload,
  MessageSquare,
  Activity,
  Calendar,
  TrendingUp
} from 'lucide-react';

export const Dashboard = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const [dashboardData, setDashboardData] = useState({
    prescriptions: [],
    activeMedications: [],
    medicationStatus: null,
    chatSessions: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated && user) {
      loadDashboardData();
    }
  }, [isAuthenticated, user]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load user's prescriptions
      const prescriptionsResponse = await apiCall(
        `${API_ENDPOINTS.PRESCRIPTIONS.GET_USER}/${user.username}`
      );
      
      // Load active medications
      const medicationsResponse = await apiCall(
        `${API_ENDPOINTS.PRESCRIPTIONS.GET_ACTIVE}/${user.username}`
      );
      
      // Load medication status
      const statusResponse = await apiCall(
        `${API_ENDPOINTS.MEDICATIONS.STATUS}/${user.username}`
      );
      
      // Load chat sessions
      const sessionsResponse = await apiCall(
        `${API_ENDPOINTS.CHAT.GET_SESSIONS}/${user.user_id}`
      );

      setDashboardData({
        prescriptions: prescriptionsResponse.prescriptions || [],
        activeMedications: medicationsResponse.active_medications || [],
        medicationStatus: statusResponse,
        chatSessions: sessionsResponse.sessions || []
      });
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="w-96">
          <CardHeader>
            <CardTitle>Access Required</CardTitle>
            <CardDescription>Please sign in to view your dashboard</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => navigate('/login')} className="w-full">
              Sign In
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const stats = [
    {
      title: 'Total Prescriptions',
      value: dashboardData.prescriptions.length.toString(),
      change: '+' + dashboardData.prescriptions.filter(p => {
        const uploadDate = new Date(p.upload_date);
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        return uploadDate > weekAgo;
      }).length,
      icon: FileHeart,
      color: 'text-blue-600',
    },
    {
      title: 'Active Medications',
      value: dashboardData.activeMedications.length.toString(),
      change: 'Active',
      icon: Syringe,
      color: 'text-green-600',
    },
    {
      title: 'Chat Sessions',
      value: dashboardData.chatSessions.length.toString(),
      change: '+' + dashboardData.chatSessions.filter(s => {
        const createdDate = new Date(s.created_at);
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        return createdDate > weekAgo;
      }).length,
      icon: MessageSquare,
      color: 'text-purple-600',
    },
    {
      title: "Today's Status",
      value: dashboardData.medicationStatus?.today_summary?.taken || '0',
      change: `${dashboardData.medicationStatus?.today_summary?.total || 0} total`,
      icon: CheckCircle,
      color: 'text-rose-600',
    }
  ];

  return (
    <div className="space-y-8 px-4 md:px-10 py-5">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Welcome back, {user?.username}!</h1>
          <p className="mt-1">Here's your health monitoring overview.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => navigate('/upload')} size="sm">
            <Upload className="mr-2 h-4 w-4" />
            Upload Prescription
          </Button>
          <Button onClick={() => navigate('/chat')} variant="outline" size="sm">
            <MessageSquare className="mr-2 h-4 w-4" />
            AI Assistant
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow duration-200">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">{stat.change}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* Upload Prescription */}
          <Card
            onClick={() => navigate('/upload')}
            className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-medium">Upload Prescription</CardTitle>
              <Upload className="h-5 w-5 text-primary" />
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Upload and process new prescription documents with AI analysis.
              </p>
            </CardContent>
          </Card>

          {/* AI Chat */}
          <Card
            onClick={() => navigate('/chat')}
            className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-medium">AI Health Assistant</CardTitle>
              <Brain className="h-5 w-5 text-primary" />
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Chat with AI about your prescriptions and get personalized health insights.
              </p>
            </CardContent>
          </Card>

          {/* Medication Tracking */}
          <Card
            onClick={() => navigate('/medication-tracking')}
            className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-medium">Medication Tracking</CardTitle>
              <Activity className="h-5 w-5 text-primary" />
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Monitor medication adherence and view detailed analytics.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Recent Prescriptions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileHeart className="h-5 w-5" />
              Recent Prescriptions
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-4">Loading...</div>
            ) : dashboardData.prescriptions.length > 0 ? (
              <div className="space-y-3">
                {dashboardData.prescriptions.slice(0, 3).map((prescription, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div>
                      <div className="font-medium">{prescription.patient_name}</div>
                      <div className="text-sm text-muted-foreground">
                        {new Date(prescription.upload_date).toLocaleDateString()}
                      </div>
                    </div>
                    <Badge variant="secondary">
                      {prescription.parsed_data?.medicines?.length || 0} meds
                    </Badge>
                  </div>
                ))}
                {dashboardData.prescriptions.length > 3 && (
                  <Button variant="outline" size="sm" className="w-full">
                    View All Prescriptions
                  </Button>
                )}
              </div>
            ) : (
              <div className="text-center py-4 text-muted-foreground">
                No prescriptions uploaded yet
              </div>
            )}
          </CardContent>
        </Card>

        {/* Today's Medication Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Today's Medications
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-4">Loading...</div>
            ) : dashboardData.medicationStatus ? (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {dashboardData.medicationStatus.today_summary.taken}
                    </div>
                    <div className="text-xs text-muted-foreground">Taken</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-red-600">
                      {dashboardData.medicationStatus.today_summary.missed}
                    </div>
                    <div className="text-xs text-muted-foreground">Missed</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-yellow-600">
                      {dashboardData.medicationStatus.today_summary.pending}
                    </div>
                    <div className="text-xs text-muted-foreground">Pending</div>
                  </div>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full"
                  onClick={() => navigate('/medication-tracking')}
                >
                  View Detailed Tracking
                </Button>
              </div>
            ) : (
              <div className="text-center py-4 text-muted-foreground">
                No medication data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};