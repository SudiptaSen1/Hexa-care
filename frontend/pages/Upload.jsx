import React, { useRef, useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { UploadCloud, FileText } from 'lucide-react';

const Upload = () => {
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png'];

    if (file && allowedTypes.includes(file.type)) {
      setSelectedFile(file);
    } else {
      alert('Please upload a valid PDF, JPG, or PNG file.');
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleSubmit = () => {
    if (!selectedFile) {
      alert('Please select a file to upload.');
      return;
    }

    // Replace with actual upload logic
    console.log('Uploading file:', selectedFile);
    alert(`File "${selectedFile.name}" uploaded successfully.`);
  };

  return (
    <div className="flex justify-center items-center mt-40 px-4">
      <Card className="w-full max-w-md p-6 shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl flex items-center gap-2">
            <UploadCloud className="h-5 w-5" />
            Upload Medical Report
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="pdf-upload">Select a PDF file{" "}</Label>
            <Input
              id="file-upload"
              ref={fileInputRef}
              type="file"
              accept="application/pdf,image/jpeg,image/png"
              onChange={handleFileChange}
              className="hidden"
            />
            <Button variant="outline" onClick={handleUploadClick}>
              Choose File
            </Button>
            {selectedFile && (
              <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                <FileText className="h-4 w-4" />
                {selectedFile.name}
              </div>
            )}
          </div>
          <Button onClick={handleSubmit} className="w-full">
            Upload
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default Upload;
