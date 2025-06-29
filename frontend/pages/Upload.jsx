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

  React.useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

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

  const handleSubmit = async () => {
    if (!selectedFile) {
      alert('Please select a file to upload.');
      return;
    }

    setIsUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

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
            <CardTitle className="text-xl flex items-center gap-2">
              <UploadCloud className="h-5 w-5" />
              Upload Prescription
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="file-upload">Select prescription file (PDF, JPG, PNG)</Label>
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
                      <h4 className="font-semibold mb-2">Prescription Summary:</h4>
                      <div className="bg-green-50 p-4 rounded-lg">
                        <pre className="whitespace-pre-wrap text-sm">{uploadResult.data.summary}</pre>
                      </div>
                    </div>
                  )}
                  {uploadResult.data.extracted_json && (
                    <div>
                      <h4 className="font-semibold mb-2">Extracted Information:</h4>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <pre className="text-xs overflow-auto max-h-64">{JSON.stringify(uploadResult.data.extracted_json, null, 2)}</pre>
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
                <div className="bg-red-50 p-4 rounded-lg">
                  <p className="text-red-700">{uploadResult.error}</p>
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