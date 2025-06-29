import React, { useRef, useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { UploadCloud, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../src/context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { API_BASE, API_ENDPOINTS } from '../src/config/api';

const Upload = () => {
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  
  // Restore the user schedule form
  const [userSchedule, setUserSchedule] = useState({
    patient_name: user?.username || '',
    contact_number: '',
    wake_up_time: '07:00',
    breakfast_time: '08:00',
    lunch_time: '13:00',
    dinner_time: '20:00',
    sleep_time: '22:00',
    before_breakfast_offset_minutes: 20,
    after_lunch_offset_minutes: 30,
    before_lunch_offset_minutes: 10,
    after_dinner_offset_minutes: 45
  });

  React.useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  React.useEffect(() => {
    if (user?.username) {
      setUserSchedule(prev => ({
        ...prev,
        patient_name: user.username
      }));
    }
  }, [user]);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png'];

    if (file && allowedTypes.includes(file.type)) {
      setSelectedFile(file);
      setUploadResult(null);
    } else {
      alert('Please upload a valid PDF, JPG, or PNG file.');
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleScheduleChange = (field, value) => {
    setUserSchedule(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      alert('Please select a file to upload.');
      return;
    }

    if (!userSchedule.patient_name || !userSchedule.contact_number) {
      alert('Please fill in patient name and contact number.');
      return;
    }

    setIsUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('user_schedule_json', JSON.stringify(userSchedule));

      const response = await fetch(`${API_BASE}${API_ENDPOINTS.PRESCRIPTIONS.UPLOAD}`, {
        method: 'POST',
        body: formData,
        headers: {
          'ngrok-skip-browser-warning': 'true',
          'X-User-ID': user.user_id
        }
      });

      const result = await response.json();

      if (response.ok) {
        setUploadResult({
          success: true,
          data: result
        });
      } else {
        setUploadResult({
          success: false,
          error: result.detail || 'Upload failed'
        });
      }
    } catch (error) {
      setUploadResult({
        success: false,
        error: 'Network error occurred'
      });
    } finally {
      setIsUploading(false);
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex justify-center items-start mt-10 px-4">
      <div className="w-full max-w-2xl space-y-6">
        {/* File Upload Card */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2 text-foreground">
              <UploadCloud className="h-5 w-5" />
              Upload Prescription
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="file-upload" className="text-foreground">Select prescription file (PDF, JPG, PNG)</Label>
              <Input
                id="file-upload"
                ref={fileInputRef}
                type="file"
                accept="application/pdf,image/jpeg,image/png"
                onChange={handleFileChange}
                className="hidden"
              />
              <Button 
                variant="outline" 
                onClick={handleUploadClick} 
                className="w-full"
                disabled={isUploading}
              >
                {selectedFile ? 'Change File' : 'Choose File'}
              </Button>
              {selectedFile && (
                <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                  <FileText className="h-4 w-4" />
                  {selectedFile.name}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Patient Schedule Card - Restored */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="text-xl text-foreground">Patient Schedule & Notification Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="patient_name" className="text-foreground">Patient Name *</Label>
                <Input
                  id="patient_name"
                  value={userSchedule.patient_name}
                  onChange={(e) => handleScheduleChange('patient_name', e.target.value)}
                  placeholder="Enter patient name"
                  required
                  disabled={isUploading}
                  className="bg-background text-foreground"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="contact_number" className="text-foreground">Contact Number *</Label>
                <Input
                  id="contact_number"
                  value={userSchedule.contact_number}
                  onChange={(e) => handleScheduleChange('contact_number', e.target.value)}
                  placeholder="+1234567890"
                  required
                  disabled={isUploading}
                  className="bg-background text-foreground"
                />
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-semibold text-foreground">Daily Schedule</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="wake_up_time" className="text-foreground">Wake Up Time</Label>
                  <Input
                    id="wake_up_time"
                    type="time"
                    value={userSchedule.wake_up_time}
                    onChange={(e) => handleScheduleChange('wake_up_time', e.target.value)}
                    disabled={isUploading}
                    className="bg-background text-foreground"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="breakfast_time" className="text-foreground">Breakfast Time</Label>
                  <Input
                    id="breakfast_time"
                    type="time"
                    value={userSchedule.breakfast_time}
                    onChange={(e) => handleScheduleChange('breakfast_time', e.target.value)}
                    disabled={isUploading}
                    className="bg-background text-foreground"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lunch_time" className="text-foreground">Lunch Time</Label>
                  <Input
                    id="lunch_time"
                    type="time"
                    value={userSchedule.lunch_time}
                    onChange={(e) => handleScheduleChange('lunch_time', e.target.value)}
                    disabled={isUploading}
                    className="bg-background text-foreground"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dinner_time" className="text-foreground">Dinner Time</Label>
                  <Input
                    id="dinner_time"
                    type="time"
                    value={userSchedule.dinner_time}
                    onChange={(e) => handleScheduleChange('dinner_time', e.target.value)}
                    disabled={isUploading}
                    className="bg-background text-foreground"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sleep_time" className="text-foreground">Sleep Time</Label>
                  <Input
                    id="sleep_time"
                    type="time"
                    value={userSchedule.sleep_time}
                    onChange={(e) => handleScheduleChange('sleep_time', e.target.value)}
                    disabled={isUploading}
                    className="bg-background text-foreground"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-semibold text-foreground">Medication Timing Offsets (minutes)</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="before_breakfast_offset" className="text-foreground">Before Breakfast</Label>
                  <Input
                    id="before_breakfast_offset"
                    type="number"
                    value={userSchedule.before_breakfast_offset_minutes}
                    onChange={(e) => handleScheduleChange('before_breakfast_offset_minutes', parseInt(e.target.value))}
                    disabled={isUploading}
                    className="bg-background text-foreground"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="after_lunch_offset" className="text-foreground">After Lunch</Label>
                  <Input
                    id="after_lunch_offset"
                    type="number"
                    value={userSchedule.after_lunch_offset_minutes}
                    onChange={(e) => handleScheduleChange('after_lunch_offset_minutes', parseInt(e.target.value))}
                    disabled={isUploading}
                    className="bg-background text-foreground"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="before_lunch_offset" className="text-foreground">Before Lunch</Label>
                  <Input
                    id="before_lunch_offset"
                    type="number"
                    value={userSchedule.before_lunch_offset_minutes}
                    onChange={(e) => handleScheduleChange('before_lunch_offset_minutes', parseInt(e.target.value))}
                    disabled={isUploading}
                    className="bg-background text-foreground"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="after_dinner_offset" className="text-foreground">After Dinner</Label>
                  <Input
                    id="after_dinner_offset"
                    type="number"
                    value={userSchedule.after_dinner_offset_minutes}
                    onChange={(e) => handleScheduleChange('after_dinner_offset_minutes', parseInt(e.target.value))}
                    disabled={isUploading}
                    className="bg-background text-foreground"
                  />
                </div>
              </div>
            </div>

            <Button 
              onClick={handleSubmit} 
              className="w-full" 
              disabled={isUploading || !selectedFile}
            >
              {isUploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                'Upload & Process Prescription'
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Results Card */}
        {uploadResult && (
          <Card className={`shadow-lg ${uploadResult.success ? 'border-green-200' : 'border-red-200'}`}>
            <CardHeader>
              <CardTitle className={`text-xl flex items-center gap-2 ${uploadResult.success ? 'text-green-700' : 'text-red-700'}`}>
                {uploadResult.success ? (
                  <>
                    <CheckCircle className="h-5 w-5" />
                    Upload Successful
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-5 w-5" />
                    Upload Failed
                  </>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {uploadResult.success ? (
                <div className="space-y-4">
                  {uploadResult.data.summary && (
                    <div>
                      <h4 className="font-semibold mb-2 text-foreground">Prescription Summary:</h4>
                      <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                        <pre className="whitespace-pre-wrap text-sm text-green-800 dark:text-green-200">{uploadResult.data.summary}</pre>
                      </div>
                    </div>
                  )}
                  {uploadResult.data.extracted_json && (
                    <div>
                      <h4 className="font-semibold mb-2 text-foreground">Extracted Information:</h4>
                      <div className="bg-muted p-4 rounded-lg">
                        <pre className="text-xs overflow-auto max-h-64 text-foreground">{JSON.stringify(uploadResult.data.extracted_json, null, 2)}</pre>
                      </div>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <Button onClick={() => navigate('/chat')} size="sm">
                      Chat About This Prescription
                    </Button>
                    <Button onClick={() => navigate('/dashboard')} variant="outline" size="sm">
                      Back to Dashboard
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
                  <p className="text-red-700 dark:text-red-200">{uploadResult.error}</p>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Upload;