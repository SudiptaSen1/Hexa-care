import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Calendar,
  Pill,
  MessageSquare,
  Loader2
} from 'lucide-react';
import { useAuth } from '../src/context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { apiCall, API_ENDPOINTS } from '../src/config/api';

const MedicationTracking = () => {
  const [patientName, setPatientName] = useState('');
  const [adherenceData, setAdherenceData] = useState(null);
  const [confirmations, setConfirmations] = useState([]);
  const [todayStatus, setTodayStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    if (user?.username) {
      setPatientName(user.username);
      // Auto-load data for current user
      fetchAllData(user.username);
    }
  }, [isAuthenticated, user, navigate]);

  const fetchAllData = async (name) => {
    if (!name.trim()) return;
    
    setLoading(true);
    try {
      await Promise.all([
        fetchAdherenceData(name),
        fetchConfirmations(name),
        fetchTodayStatus(name)
      ]);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAdherenceData = async (name) => {
    try {
      const response = await apiCall(`${API_ENDPOINTS.MEDICATIONS.ADHERENCE}/${name}?days=7`);
      if (response.status === 'success') {
        setAdherenceData(response);
      }
    } catch (error) {
      console.error('Error fetching adherence data:', error);
    }
  };

  const fetchConfirmations = async (name) => {
    try {
      const response = await apiCall(`${API_ENDPOINTS.MEDICATIONS.CONFIRMATIONS}/${name}`);
      if (response.status === 'success') {
        setConfirmations(response.confirmations);
      }
    } catch (error) {
      console.error('Error fetching confirmations:', error);
    }
  };

  const fetchTodayStatus = async (name) => {
    try {
      const response = await apiCall(`${API_ENDPOINTS.MEDICATIONS.STATUS}/${name}`);
      if (response.status === 'success') {
        setTodayStatus(response);
      }
    } catch (error) {
      console.error('Error fetching today status:', error);
    }
  };

  const handleSearch = () => {
    fetchAllData(patientName);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'taken': return 'text-green-600';
      case 'missed': return 'text-red-600';
      case 'pending': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'taken': return <CheckCircle className="h-4 w-4" />;
      case 'missed': return <XCircle className="h-4 w-4" />;
      case 'pending': return <Clock className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="space-y-6 px-4 md:px-10 py-5">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Medication Tracking</h1>
        <p className="mt-1">Monitor medication adherence and patient responses</p>
      </div>

      {/* Search */}
      <Card>
        <CardHeader>
          <CardTitle>Patient Search</CardTitle>
          <CardDescription>Enter patient name to view medication tracking data</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <Label htmlFor="patientName">Patient Name</Label>
              <Input
                id="patientName"
                value={patientName}
                onChange={(e) => setPatientName(e.target.value)}
                placeholder="Enter patient name"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <div className="flex items-end">
              <Button onClick={handleSearch} disabled={loading || !patientName.trim()}>
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Loading...
                  </>
                ) : (
                  'Search'
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Today's Status */}
      {todayStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Today's Medication Status
            </CardTitle>
            <CardDescription>
              {todayStatus.date} - {todayStatus.patient_name}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{todayStatus.today_summary.total}</div>
                <div className="text-sm text-muted-foreground">Total</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{todayStatus.today_summary.taken}</div>
                <div className="text-sm text-muted-foreground">Taken</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{todayStatus.today_summary.missed}</div>
                <div className="text-sm text-muted-foreground">Missed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{todayStatus.today_summary.pending}</div>
                <div className="text-sm text-muted-foreground">Pending</div>
              </div>
            </div>

            {todayStatus.today_logs.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-semibold">Today's Reminders</h4>
                {todayStatus.today_logs.map((log, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className={getStatusColor(log.status)}>
                        {getStatusIcon(log.status)}
                      </div>
                      <div>
                        <div className="font-medium">{log.scheduled_time}</div>
                        <div className="text-sm text-muted-foreground">
                          Sent: {new Date(log.sent_time).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                    <Badge variant={log.status === 'taken' ? 'default' : log.status === 'missed' ? 'destructive' : 'secondary'}>
                      {log.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Adherence Overview */}
      {adherenceData && (
        <div className="grid md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                7-Day Adherence Rate
              </CardTitle>
              <CardDescription>{adherenceData.patient_name}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center mb-4">
                <div className="text-4xl font-bold text-primary">
                  {adherenceData.adherence_rate}%
                </div>
                <div className="text-sm text-muted-foreground">Adherence Rate</div>
              </div>
              
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-green-600">{adherenceData.taken}</div>
                  <div className="text-xs text-muted-foreground">Taken</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">{adherenceData.missed}</div>
                  <div className="text-xs text-muted-foreground">Missed</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-yellow-600">{adherenceData.pending}</div>
                  <div className="text-xs text-muted-foreground">Pending</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Recent Confirmations
              </CardTitle>
              <CardDescription>Latest patient responses</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {confirmations.length > 0 ? (
                  confirmations.map((confirmation, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={confirmation.is_taken ? 'text-green-600' : 'text-red-600'}>
                          {confirmation.is_taken ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                        </div>
                        <div>
                          <div className="font-medium">{confirmation.scheduled_time}</div>
                          <div className="text-sm text-muted-foreground">
                            {new Date(confirmation.confirmation_time).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                      <Badge variant={confirmation.is_taken ? 'default' : 'destructive'}>
                        {confirmation.is_taken ? 'Taken' : 'Missed'}
                      </Badge>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-muted-foreground py-4">
                    No confirmations found
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Detailed Logs */}
      {adherenceData && adherenceData.logs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Detailed Medication Log</CardTitle>
            <CardDescription>Complete history of medication reminders and responses</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {adherenceData.logs.map((log, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={getStatusColor(log.status)}>
                      {getStatusIcon(log.status)}
                    </div>
                    <div>
                      <div className="font-medium">{log.scheduled_time}</div>
                      <div className="text-sm text-muted-foreground">
                        Sent: {new Date(log.sent_time).toLocaleString()}
                        {log.response_time && (
                          <span> • Responded: {new Date(log.response_time).toLocaleString()}</span>
                        )}
                      </div>
                      {log.response_message && (
                        <div className="text-sm italic text-muted-foreground mt-1">
                          "{log.response_message}"
                        </div>
                      )}
                    </div>
                  </div>
                  <Badge variant={log.status === 'taken' ? 'default' : log.status === 'missed' ? 'destructive' : 'secondary'}>
                    {log.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Data State */}
      {!loading && !adherenceData && !todayStatus && patientName && (
        <Card>
          <CardContent className="text-center py-8">
            <Pill className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Medication Data Found</h3>
            <p className="text-muted-foreground mb-4">
              No medication tracking data found for "{patientName}". 
              Make sure you have uploaded prescriptions and set up medication reminders.
            </p>
            <Button onClick={() => navigate('/upload')}>
              Upload Prescription
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MedicationTracking;