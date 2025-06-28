import { useState } from 'react';
import { Button } from '../components/ui/button';
import {
  Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle
} from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Tabs, TabsContent, TabsList, TabsTrigger
} from '../components/ui/tabs';
import { useNavigate } from 'react-router-dom';

const API_BASE = 'http://localhost:8000';

const Login = () => {
  const [signupData, setSignupData] = useState({ username: '', email: '', password: '' });
  const [loginData, setLoginData] = useState({ username_or_email: '', password: '' });
  const navigate = useNavigate();

  const handleSignupChange = (e) => {
    const { name, value } = e.target;
    setSignupData({ ...signupData, [name]: value });
  };

  const handleLoginChange = (e) => {
    const { name, value } = e.target;
    setLoginData({ ...loginData, [name]: value });
  };

  const handleSignup = async () => {
    try {
      const res = await fetch(`${API_BASE}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(signupData)
      });
      const data = await res.json();
      console.log('Signup Response:', data);
      if (!res.ok) throw new Error(data.detail);
      alert('Signup successful!');
      navigate('/dashboard'); 
    } catch (err) {
      console.error(err);
      alert('Signup failed: ' + err.message);
    }
  };

  const handleLogin = async () => {
    try {
      const res = await fetch(`${API_BASE}/signin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginData)
      });
      const data = await res.json();
      console.log('Login Response:', data);
      if (!res.ok) throw new Error(data.detail);
      alert('Login successful!');
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      alert('Login failed: ' + err.message);
    }
  };

  return (
    <div className='flex items-center w-full justify-center py-32'>
      <Tabs defaultValue='signup' className='w-[400px]'>
        <TabsList className='grid w-full grid-cols-2'>
          <TabsTrigger value='signup'>Sign Up</TabsTrigger>
          <TabsTrigger value='login'>Sign In</TabsTrigger>
        </TabsList>

        {/* Signup Tab */}
        <TabsContent value='signup'>
          <Card>
            <CardHeader>
              <CardTitle>Sign Up</CardTitle>
              <CardDescription>Create your new account and start learning</CardDescription>
            </CardHeader>
            <CardContent className='space-y-2'>
              <div className='space-y-1'>
                <Label htmlFor='username'>Username</Label>
                <Input
                  type='text'
                  name='username'
                  placeholder='JohnDoe'
                  value={signupData.username}
                  onChange={handleSignupChange}
                  required
                />
              </div>
              <div className='space-y-1'>
                <Label htmlFor='email'>E-Mail</Label>
                <Input
                  type='email'
                  name='email'
                  placeholder='john@doe.com'
                  value={signupData.email}
                  onChange={handleSignupChange}
                  required
                />
              </div>
              <div className='space-y-1'>
                <Label htmlFor='password'>Password</Label>
                <Input
                  type='password'
                  name='password'
                  placeholder='********'
                  value={signupData.password}
                  onChange={handleSignupChange}
                  required
                />
              </div>
            </CardContent>
            <CardFooter>
              <Button onClick={handleSignup}>Sign Up</Button>
            </CardFooter>
          </Card>
        </TabsContent>

        {/* Login Tab */}
        <TabsContent value='login'>
          <Card>
            <CardHeader>
              <CardTitle>Sign In</CardTitle>
              <CardDescription>Log in to your account and continue learning</CardDescription>
            </CardHeader>
            <CardContent className='space-y-2'>
              <div className='space-y-1'>
                <Label htmlFor='username_or_email'>Username or E-Mail</Label>
                <Input
                  type='text'
                  name='username_or_email'
                  placeholder='john@doe.com'
                  value={loginData.username_or_email}
                  onChange={handleLoginChange}
                  required
                />
              </div>
              <div className='space-y-1'>
                <Label htmlFor='password'>Password</Label>
                <Input
                  type='password'
                  name='password'
                  placeholder='********'
                  value={loginData.password}
                  onChange={handleLoginChange}
                  required
                />
              </div>
            </CardContent>
            <CardFooter>
              <Button onClick={handleLogin}>Log In</Button>
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Login;
