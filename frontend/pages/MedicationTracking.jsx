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
  Loader2,
  Activity,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../src/context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { apiCall, API_ENDPOINTS } from '../src/config/api';

const MedicationTracking = () => {
  const [patientName, setPatientName] = useState('');
  const [adherenceData, setAdherenceData] = useState(null);
  const [confirmations, setConfirmations] = useState([]);
  const [todayStatus, setTodayStatus] = useState(null);
  const [activeMedications, setActiveMedications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
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
    setError(null);
    try {
      await Promise.all([
        fetchAdherenceData(name),
        fetchConfirmations(name),
        fetchTodayStatus(name),
        fetchActiveMedications(name)
      ]);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to load medication data');
    } finally {
      setLoading(false);
    }
  };

  const fetchAdherenceData = async (name) => {
    try {
      const response = await apiCall(`${API_ENDPOINTS.MEDICATIONS.ADHERENCE}/${encodeURIComponent(name)}?days=7`);
      if (response.status === 'success') {
        setAdherenceData(response);
      }
    } catch (error) {
      console.error('Error fetching adherence data:', error);
      setAdherenceData(null);
    }
  };

  const fetchConfirmations = async (name) => {
    try {
      const response = await apiCall(`${API_ENDPOINTS.MEDICATIONS.CONFIRMATIONS}/${encodeURIComponent(name)}`);
      if (response.status === 'success') {
        setConfirmations(response.confirmations);
      }
    } catch (error) {
      console.error('Error fetching confirmations:', error);
      setConfirmations([]);
    }
  };

  const fetchTodayStatus = async (name) => {
    try {
      const response = await apiCall(`${API_ENDPOINTS.MEDICATIONS.STATUS}/${encodeURIComponent(name)}`);
      if (response.status === 'success') {
        setTodayStatus(response);
      }
    } catch (error) {
      console.error('Error fetching today status:', error);
      setTodayStatus(null);
    }
  };

  const fetchActiveMedications = async (name) => {
    try {
      const response = await apiCall(`${API_ENDPOINTS.PRESCRIPTIONS.GET_ACTIVE}/${encodeURIComponent(name)}`);
      if (response.status === 'success') {
        setActiveMedications(response.active_medications);
      }
    } catch (error) {
      console.error('Error fetching active medications:', error);
      setActiveMedications([]);
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
    <div className="space-y-6 px-4 md:px-10 py-5 bg-background min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Medication Tracking</h1>
          <p className="mt-1 text-muted-foreground">Monitor medication adherence and patient responses</p>
        </div>
        <Button onClick={() => fetchAllData(patientName)} variant="outline" size="sm" disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Data
        </Button>
      </div>

      {/* Error Message */}
      {error && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <p className="text-red-700 dark:text-red-200">{error}</p>
            </div>
            <Button onClick={() => fetchAllData(patientName)} variant="outline" size="sm" className="mt-2">
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-card-foreground">Patient Search</CardTitle>
          <CardDescription>Enter patient name to view medication tracking data</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <Label htmlFor="patientName" className="text-card-foreground">Patient Name</Label>
              <Input
                id="patientName"
                value={patientName}
                onChange={(e) => setPatientName(e.target.value)}
                placeholder="Enter patient name"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="bg-background text-foreground border-border"
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

      {/* Active Medications Overview */}
      {activeMedications.length > 0 && (
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-card-foreground">
              <Activity className="h-5 w-5" />
              Active Medications ({activeMedications.length})
            </CardTitle>
            <CardDescription>
              Currently prescribed medications for {patientName}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3">
              {activeMedications.map((medication, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div>
                    <div className="font-medium text-card-foreground">{medication.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {medication.dosage} • Times: {medication.times?.join(', ')}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Until: {new Date(medication.end_date).toLocaleDateString()}
                    </div>
                  </div>
                  <Badge variant="secondary">
                    {medication.duration_days} days
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Today's Status */}
      {todayStatus && (
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-card-foreground">
              <Calendar className="h-5 w-5" />
              Today's Medication Status
            </CardTitle>
            <CardDescription>
              {todayStatus.date} - {todayStatus.patient_name}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center p-3 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-card-foreground">{todayStatus.today_summary.total}</div>
                <div className="text-sm text-muted-foreground">Total</div>
              </div>
              <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{todayStatus.today_summary.taken}</div>
                <div className="text-sm text-muted-foreground">Taken</div>
              </div>
              <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{todayStatus.today_summary.missed}</div>
                <div className="text-sm text-muted-foreground">Missed</div>
              </div>
              <div className="text-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">{todayStatus.today_summary.pending}</div>
                <div className="text-sm text-muted-foreground">Pending</div>
              </div>
            </div>

            {todayStatus.today_logs && todayStatus.today_logs.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-semibold text-card-foreground">Today's Reminders</h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {todayStatus.today_logs.map((log, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={getStatusColor(log.status)}>
                          {getStatusIcon(log.status)}
                        </div>
                        <div>
                          <div className="font-medium text-card-foreground">{log.scheduled_time}</div>
                          {log.sent_time && (
                            <div className="text-sm text-muted-foreground">
                              Sent: {new Date(log.sent_time).toLocaleTimeString()}
                            </div>
                          )}
                          {log.response_message && (
                            <div className="text-xs italic text-muted-foreground">
                              Response: "{log.response_message}"
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
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Adherence Overview */}
      {adherenceData && (
        <div className="grid md:grid-cols-2 gap-6">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-card-foreground">
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
                <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{adherenceData.taken}</div>
                  <div className="text-xs text-muted-foreground">Taken</div>
                </div>
                <div className="p-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">{adherenceData.missed}</div>
                  <div className="text-xs text-muted-foreground">Missed</div>
                </div>
                <div className="p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">{adherenceData.pending}</div>
                  <div className="text-xs text-muted-foreground">Pending</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-card-foreground">
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
                          <div className="font-medium text-card-foreground">{confirmation.scheduled_time}</div>
                          <div className="text-sm text-muted-foreground">
                            {new Date(confirmation.confirmation_time).toLocaleDateString()}
                          </div>
                          {confirmation.response_message && (
                            <div className="text-xs italic text-muted-foreground">
                              "{confirmation.response_message}"
                            </div>
                          )}
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
      {adherenceData && adherenceData.logs && adherenceData.logs.length > 0 && (
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-card-foreground">Detailed Medication Log</CardTitle>
            <CardDescription>Complete history of medication reminders and responses</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {adherenceData.logs.map((log, index) => (
                <div key={index} className="flex items-center justify-between p-3 border border-border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={getStatusColor(log.status)}>
                      {getStatusIcon(log.status)}
                    </div>
                    <div>
                      <div className="font-medium text-card-foreground">{log.scheduled_time}</div>
                      <div className="text-sm text-muted-foreground">
                        {log.sent_time && (
                          <span>Sent: {new Date(log.sent_time).toLocaleString()}</span>
                        )}
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
      {!loading && !adherenceData && !todayStatus && patientName && !error && (
        <Card className="bg-card border-border">
          <CardContent className="text-center py-8">
            <Pill className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2 text-card-foreground">No Medication Data Found</h3>
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