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
  TrendingUp,
  Eye,
  BarChart3
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
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isAuthenticated && user) {
      loadDashboardData();
    }
  }, [isAuthenticated, user]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const promises = [];
      
      // Load user's prescriptions
      promises.push(
        apiCall(`${API_ENDPOINTS.PRESCRIPTIONS.GET_USER}/${encodeURIComponent(user.username)}`)
          .catch(err => {
            console.error('Error loading prescriptions:', err);
            return { prescriptions: [] };
          })
      );
      
      // Load active medications
      promises.push(
        apiCall(`${API_ENDPOINTS.PRESCRIPTIONS.GET_ACTIVE}/${encodeURIComponent(user.username)}`)
          .catch(err => {
            console.error('Error loading active medications:', err);
            return { active_medications: [] };
          })
      );
      
      // Load medication status
      promises.push(
        apiCall(`${API_ENDPOINTS.MEDICATIONS.STATUS}/${encodeURIComponent(user.username)}`)
          .catch(err => {
            console.error('Error loading medication status:', err);
            return null;
          })
      );
      
      // Load chat sessions
      promises.push(
        apiCall(`${API_ENDPOINTS.CHAT.GET_SESSIONS}/${user.user_id}`)
          .catch(err => {
            console.error('Error loading chat sessions:', err);
            return { sessions: [] };
          })
      );

      const [prescriptionsResponse, medicationsResponse, statusResponse, sessionsResponse] = await Promise.all(promises);

      setDashboardData({
        prescriptions: prescriptionsResponse?.prescriptions || [],
        activeMedications: medicationsResponse?.active_medications || [],
        medicationStatus: statusResponse,
        chatSessions: sessionsResponse?.sessions || []
      });
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError('Failed to load dashboard data');
      // Set empty data on error to prevent crashes
      setDashboardData({
        prescriptions: [],
        activeMedications: [],
        medicationStatus: null,
        chatSessions: []
      });
    } finally {
      setLoading(false);
    }
  };

  const handleViewPrescription = (prescription) => {
    // Navigate to a detailed view or show modal
    console.log('Viewing prescription:', prescription);
    // For now, navigate to upload page or create a detailed view
    navigate('/upload');
  };

  const handleViewAllPrescriptions = () => {
    // Navigate to prescriptions list page
    navigate('/upload'); // Or create a dedicated prescriptions page
  };

  const handleViewMedicationDetails = () => {
    navigate('/medication-tracking');
  };

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="w-96">
          <CardHeader>
            <CardTitle className="text-foreground">Access Required</CardTitle>
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
        const uploadDate = new Date(p.upload_date || p.created_at);
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        return uploadDate > weekAgo;
      }).length + ' this week',
      icon: FileHeart,
      color: 'text-blue-600',
      onClick: handleViewAllPrescriptions
    },
    {
      title: 'Active Medications',
      value: dashboardData.activeMedications.length.toString(),
      change: 'Currently active',
      icon: Syringe,
      color: 'text-green-600',
      onClick: () => navigate('/medication-tracking')
    },
    {
      title: 'Chat Sessions',
      value: dashboardData.chatSessions.length.toString(),
      change: '+' + dashboardData.chatSessions.filter(s => {
        const createdDate = new Date(s.created_at);
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        return createdDate > weekAgo;
      }).length + ' this week',
      icon: MessageSquare,
      color: 'text-purple-600',
      onClick: () => navigate('/chat')
    },
    {
      title: "Today's Taken",
      value: dashboardData.medicationStatus?.today_summary?.taken || '0',
      change: `${dashboardData.medicationStatus?.today_summary?.total || 0} total today`,
      icon: CheckCircle,
      color: 'text-rose-600',
      onClick: handleViewMedicationDetails
    }
  ];

  return (
    <div className="space-y-8 px-4 md:px-10 py-5">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Welcome back, {user?.username}!</h1>
          <p className="mt-1 text-muted-foreground">Here's your health monitoring overview.</p>
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

      {/* Error Message */}
      {error && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardContent className="pt-6">
            <p className="text-red-700 dark:text-red-200">{error}</p>
            <Button onClick={loadDashboardData} variant="outline" size="sm" className="mt-2">
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <Card 
            key={index} 
            className="hover:shadow-lg transition-shadow duration-200 cursor-pointer"
            onClick={stat.onClick}
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-foreground">{stat.title}</CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{stat.value}</div>
              <p className="text-xs text-muted-foreground">{stat.change}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold mb-4 text-foreground">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* Upload Prescription */}
          <Card
            onClick={() => navigate('/upload')}
            className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-medium text-foreground">Upload Prescription</CardTitle>
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
              <CardTitle className="text-lg font-medium text-foreground">AI Health Assistant</CardTitle>
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
              <CardTitle className="text-lg font-medium text-foreground">Medication Tracking</CardTitle>
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
            <CardTitle className="flex items-center gap-2 text-foreground">
              <FileHeart className="h-5 w-5" />
              Recent Prescriptions
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-4 text-muted-foreground">Loading...</div>
            ) : dashboardData.prescriptions.length > 0 ? (
              <div className="space-y-3">
                {dashboardData.prescriptions.slice(0, 3).map((prescription, index) => (
                  <div 
                    key={index} 
                    className="flex items-center justify-between p-3 bg-muted rounded-lg hover:bg-muted/80 cursor-pointer transition-colors"
                    onClick={() => handleViewPrescription(prescription)}
                  >
                    <div className="flex-1">
                      <div className="font-medium text-foreground">
                        {prescription.patient_name || 'Unknown Patient'}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {prescription.upload_date ? new Date(prescription.upload_date).toLocaleDateString() : 'Unknown Date'}
                      </div>
                      {prescription.parsed_data?.diagnosis && (
                        <div className="text-xs text-muted-foreground truncate">
                          {prescription.parsed_data.diagnosis}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">
                        {prescription.parsed_data?.medicines?.length || 0} meds
                      </Badge>
                      <Eye className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>
                ))}
                {dashboardData.prescriptions.length > 3 && (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="w-full"
                    onClick={handleViewAllPrescriptions}
                  >
                    View All {dashboardData.prescriptions.length} Prescriptions
                  </Button>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileHeart className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground mb-4">No prescriptions uploaded yet</p>
                <Button onClick={() => navigate('/upload')} size="sm">
                  Upload Your First Prescription
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Today's Medication Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-foreground">
              <Calendar className="h-5 w-5" />
              Today's Medications
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-4 text-muted-foreground">Loading...</div>
            ) : dashboardData.medicationStatus ? (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div 
                    className="cursor-pointer hover:bg-green-50 dark:hover:bg-green-900/20 p-2 rounded-lg transition-colors"
                    onClick={handleViewMedicationDetails}
                  >
                    <div className="text-2xl font-bold text-green-600">
                      {dashboardData.medicationStatus.today_summary?.taken || 0}
                    </div>
                    <div className="text-xs text-muted-foreground">Taken</div>
                  </div>
                  <div 
                    className="cursor-pointer hover:bg-red-50 dark:hover:bg-red-900/20 p-2 rounded-lg transition-colors"
                    onClick={handleViewMedicationDetails}
                  >
                    <div className="text-2xl font-bold text-red-600">
                      {dashboardData.medicationStatus.today_summary?.missed || 0}
                    </div>
                    <div className="text-xs text-muted-foreground">Missed</div>
                  </div>
                  <div 
                    className="cursor-pointer hover:bg-yellow-50 dark:hover:bg-yellow-900/20 p-2 rounded-lg transition-colors"
                    onClick={handleViewMedicationDetails}
                  >
                    <div className="text-2xl font-bold text-yellow-600">
                      {dashboardData.medicationStatus.today_summary?.pending || 0}
                    </div>
                    <div className="text-xs text-muted-foreground">Pending</div>
                  </div>
                </div>
                
                {/* Today's Medication List */}
                {dashboardData.medicationStatus.today_logs && dashboardData.medicationStatus.today_logs.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-semibold text-sm text-foreground">Today's Schedule</h4>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {dashboardData.medicationStatus.today_logs.slice(0, 3).map((log, index) => (
                        <div key={index} className="flex items-center justify-between text-xs p-2 bg-muted/50 rounded">
                          <span className="text-foreground">{log.scheduled_time}</span>
                          <Badge 
                            variant={log.status === 'taken' ? 'default' : log.status === 'missed' ? 'destructive' : 'secondary'}
                            className="text-xs"
                          >
                            {log.status}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full"
                  onClick={handleViewMedicationDetails}
                >
                  <BarChart3 className="mr-2 h-4 w-4" />
                  View Detailed Tracking
                </Button>
              </div>
            ) : (
              <div className="text-center py-8">
                <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground mb-4">No medication data available</p>
                <Button onClick={() => navigate('/upload')} size="sm">
                  Upload Prescription to Start Tracking
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Active Medications Overview */}
      {dashboardData.activeMedications.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-foreground">
              <Syringe className="h-5 w-5" />
              Active Medications ({dashboardData.activeMedications.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {dashboardData.activeMedications.slice(0, 6).map((medication, index) => (
                <div 
                  key={index} 
                  className="p-3 bg-muted rounded-lg hover:bg-muted/80 cursor-pointer transition-colors"
                  onClick={() => navigate('/medication-tracking')}
                >
                  <div className="font-medium text-foreground text-sm">{medication.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {medication.dosage}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Times: {medication.times?.join(', ')}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Until: {new Date(medication.end_date).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
            {dashboardData.activeMedications.length > 6 && (
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full mt-3"
                onClick={() => navigate('/medication-tracking')}
              >
                View All {dashboardData.activeMedications.length} Active Medications
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};