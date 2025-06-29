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
import { useAuth } from '../src/context/AuthContext';
import { AlertCircle, CheckCircle } from 'lucide-react';

const Login = () => {
  const [signupData, setSignupData] = useState({ username: '', email: '', password: '' });
  const [loginData, setLoginData] = useState({ username_or_email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const navigate = useNavigate();
  const { login, signup } = useAuth();

  const handleSignupChange = (e) => {
    const { name, value } = e.target;
    setSignupData({ ...signupData, [name]: value });
    setMessage({ type: '', text: '' });
  };

  const handleLoginChange = (e) => {
    const { name, value } = e.target;
    setLoginData({ ...loginData, [name]: value });
    setMessage({ type: '', text: '' });
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      await signup(signupData);
      setMessage({ type: 'success', text: 'Account created successfully!' });
      setTimeout(() => navigate('/dashboard'), 1500);
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'Signup failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      await login(loginData);
      setMessage({ type: 'success', text: 'Login successful!' });
      setTimeout(() => navigate('/dashboard'), 1500);
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'Login failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='flex items-center w-full justify-center py-32'>
      <Tabs defaultValue='login' className='w-[400px]'>
        <TabsList className='grid w-full grid-cols-2'>
          <TabsTrigger value='login'>Sign In</TabsTrigger>
          <TabsTrigger value='signup'>Sign Up</TabsTrigger>
        </TabsList>

        {/* Message Display */}
        {message.text && (
          <div className={`mt-4 p-3 rounded-lg flex items-center gap-2 ${
            message.type === 'success' 
              ? 'bg-green-50 text-green-700 border border-green-200' 
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}>
            {message.type === 'success' ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <AlertCircle className="h-4 w-4" />
            )}
            {message.text}
          </div>
        )}

        {/* Login Tab */}
        <TabsContent value='login'>
          <Card>
            <CardHeader>
              <CardTitle>Sign In</CardTitle>
              <CardDescription>Access your medical dashboard</CardDescription>
            </CardHeader>
            <form onSubmit={handleLogin}>
              <CardContent className='space-y-2'>
                <div className='space-y-1'>
                  <Label htmlFor='username_or_email'>Username or Email</Label>
                  <Input
                    type='text'
                    name='username_or_email'
                    placeholder='john@doe.com'
                    value={loginData.username_or_email}
                    onChange={handleLoginChange}
                    required
                    disabled={loading}
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
                    disabled={loading}
                  />
                </div>
              </CardContent>
              <CardFooter>
                <Button type="submit" disabled={loading} className="w-full">
                  {loading ? 'Signing In...' : 'Sign In'}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </TabsContent>

        {/* Signup Tab */}
        <TabsContent value='signup'>
          <Card>
            <CardHeader>
              <CardTitle>Sign Up</CardTitle>
              <CardDescription>Create your medical account</CardDescription>
            </CardHeader>
            <form onSubmit={handleSignup}>
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
                    disabled={loading}
                  />
                </div>
                <div className='space-y-1'>
                  <Label htmlFor='email'>Email</Label>
                  <Input
                    type='email'
                    name='email'
                    placeholder='john@doe.com'
                    value={signupData.email}
                    onChange={handleSignupChange}
                    required
                    disabled={loading}
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
                    disabled={loading}
                  />
                </div>
              </CardContent>
              <CardFooter>
                <Button type="submit" disabled={loading} className="w-full">
                  {loading ? 'Creating Account...' : 'Sign Up'}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Login;