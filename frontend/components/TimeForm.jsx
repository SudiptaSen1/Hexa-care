import { useState } from 'react';
import {
  Card, CardHeader, CardTitle, CardContent, CardFooter,
} from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Button } from './ui/button';

const defaultData = {
  meal_times: {
    breakfast: '08:30',
    lunch: '13:00',
    dinner: '20:00',
  },
  other_key_times: {
    wake_up: '07:00',
    bedtime: '22:30',
  },
  timezone: 'Asia/Kolkata',
};

export default function TimeForm() {
  const [formData, setFormData] = useState(defaultData);

  const handleChange = (section, key, value, index = null) => {
    const updated = { ...formData };

    if (section === 'snack_time') {
      updated.other_key_times.snack_time[index] = value;
    } else if (section === 'meal_times') {
      updated.meal_times[key] = value;
    } else if (section === 'other_key_times') {
      updated.other_key_times[key] = value;
    } else if (section === 'timezone') {
      updated.timezone = value;
    }

    setFormData(updated);
  };

  const handleSubmit = () => {
    console.log('Submitted data:', formData);
    alert('Form submitted! Check console.');
  };

  return (
    <Card className="max-w-xl mx-auto mt-10">
      <CardHeader>
        <CardTitle className="text-foreground">Edit Daily Schedule</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">

        {/* Meal Times */}
        <div className="space-y-2">
          <h3 className="font-semibold text-lg text-foreground">Meal Times</h3>
          {Object.entries(formData.meal_times).map(([key, value]) => (
            <div key={key}>
              <Label htmlFor={key} className="text-foreground">{key}</Label>
              <Input
                id={key}
                type="time"
                value={value}
                onChange={(e) => handleChange('meal_times', key, e.target.value)}
                className="bg-background text-foreground"
              />
            </div>
          ))}
        </div>

        {/* Other Key Times */}
        <div className="space-y-2">
          <h3 className="font-semibold text-lg text-foreground">Other Key Times</h3>
          {Object.entries(formData.other_key_times).map(([key, value]) => {
            if (key === 'snack_time') {
              return value.map((time, index) => (
                <div key={`${key}-${index}`}>
                  <Label htmlFor={`${key}-${index}`} className="text-foreground">{`Snack Time ${index + 1}`}</Label>
                  <Input
                    id={`${key}-${index}`}
                    type="time"
                    value={time}
                    onChange={(e) => handleChange('snack_time', key, e.target.value, index)}
                    className="bg-background text-foreground"
                  />
                </div>
              ));
            } else {
              return (
                <div key={key}>
                  <Label htmlFor={key} className="text-foreground">{key.replace(/_/g, ' ')}</Label>
                  <Input
                    id={key}
                    type="time"
                    value={value}
                    onChange={(e) => handleChange('other_key_times', key, e.target.value)}
                    className="bg-background text-foreground"
                  />
                </div>
              );
            }
          })}
        </div>

        {/* Timezone */}
        <div>
          <Label htmlFor="timezone" className="text-foreground">Timezone</Label>
          <Input
            id="timezone"
            type="text"
            value={formData.timezone}
            onChange={(e) => handleChange('timezone', 'timezone', e.target.value)}
            className="bg-background text-foreground"
          />
        </div>
      </CardContent>
      <CardFooter>
        <Button onClick={handleSubmit}>Save Changes</Button>
      </CardFooter>
    </Card>
  );
}