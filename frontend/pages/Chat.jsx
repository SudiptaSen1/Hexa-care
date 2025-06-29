import React, { useState, useEffect } from 'react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card';
import { ScrollArea } from '../components/ui/scroll-area';
import { Bot, User, MessageSquare, Plus, Loader2, RefreshCw, AlertCircle } from 'lucide-react';
import { useAuth } from '../src/context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { apiCall, API_ENDPOINTS } from '../src/config/api';

const Chat = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [error, setError] = useState(null);
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    loadUserSessions();
  }, [isAuthenticated, navigate]);

  const loadUserSessions = async () => {
    try {
      setLoadingSessions(true);
      setError(null);
      const response = await apiCall(`${API_ENDPOINTS.CHAT.GET_SESSIONS}/${user.user_id}`);
      setSessions(response.sessions || []);
    } catch (error) {
      console.error('Error loading sessions:', error);
      setError('Failed to load chat sessions');
    } finally {
      setLoadingSessions(false);
    }
  };

  const startNewSession = async () => {
    try {
      setError(null);
      const response = await apiCall(`${API_ENDPOINTS.CHAT.START_SESSION}/${user.user_id}`, {
        method: 'POST'
      });
      
      setCurrentSessionId(response.session_id);
      setMessages([]);
      await loadUserSessions();
      
      // Add welcome message
      setMessages([{
        sender: 'bot',
        text: `Hello! I'm your AI health assistant. I have access to your prescription data and can help you with questions about your medications, schedules, adherence, and general health guidance. What would you like to know?`,
        timestamp: new Date().toLocaleTimeString()
      }]);
    } catch (error) {
      console.error('Error starting new session:', error);
      setError('Failed to start new session');
    }
  };

  const loadChatHistory = async (sessionId) => {
    try {
      setError(null);
      const response = await apiCall(`${API_ENDPOINTS.CHAT.GET_HISTORY}/${user.user_id}/${sessionId}`);
      
      const formattedMessages = response.chat_history.map(msg => ({
        sender: msg.type === 'human' ? 'user' : 'bot',
        text: msg.content,
        timestamp: new Date().toLocaleTimeString()
      }));
      
      setMessages(formattedMessages);
      setCurrentSessionId(sessionId);
    } catch (error) {
      console.error('Error loading chat history:', error);
      setError('Failed to load chat history');
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !currentSessionId) {
      if (!currentSessionId) {
        setError('Please start a new session first');
      }
      return;
    }

    const userMessage = {
      sender: 'user',
      text: input,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiCall(
        `${API_ENDPOINTS.CHAT.SEND_MESSAGE}/${user.user_id}/${currentSessionId}/message`,
        {
          method: 'POST',
          body: JSON.stringify({ message: currentInput })
        }
      );

      const botMessage = {
        sender: 'bot',
        text: response.answer,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        sender: 'bot',
        text: 'Sorry, I encountered an error processing your message. Please try again or start a new session.',
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages(prev => [...prev, errorMessage]);
      setError('Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className='flex h-[600px] max-w-6xl mx-auto p-4 gap-4 bg-background'>
      {/* Sessions Sidebar */}
      <Card className='w-80 flex flex-col bg-card border-border'>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-card-foreground">
            <span>Chat Sessions</span>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={loadUserSessions} disabled={loadingSessions}>
                <RefreshCw className={`h-4 w-4 ${loadingSessions ? 'animate-spin' : ''}`} />
              </Button>
              <Button size="sm" onClick={startNewSession}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className='flex-1 overflow-hidden'>
          <ScrollArea className='h-full'>
            <div className='space-y-2'>
              {loadingSessions ? (
                <div className="text-center py-4">
                  <Loader2 className="h-4 w-4 animate-spin mx-auto" />
                  <p className="text-sm text-muted-foreground mt-2">Loading sessions...</p>
                </div>
              ) : sessions.length > 0 ? (
                sessions.map((session) => (
                  <div
                    key={session.session_id}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      currentSessionId === session.session_id
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80 text-card-foreground'
                    }`}
                    onClick={() => loadChatHistory(session.session_id)}
                  >
                    <div className="font-medium text-sm truncate">
                      {session.session_name}
                    </div>
                    <div className="text-xs opacity-70">
                      {new Date(session.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-muted-foreground text-sm py-4">
                  No chat sessions yet. Start a new one!
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Chat Area */}
      <Card className='flex-1 flex flex-col overflow-hidden bg-card border-border'>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-card-foreground">
            <MessageSquare className="h-5 w-5" />
            Medical Assistant Chat
            {currentSessionId && (
              <span className="text-sm font-normal text-muted-foreground">
                (Session Active)
              </span>
            )}
          </CardTitle>
          {error && (
            <div className="flex items-center gap-2 text-red-600 text-sm">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          )}
        </CardHeader>

        <CardContent className='p-4 flex-1 overflow-hidden'>
          <ScrollArea className='h-full pr-2'>
            <div className='space-y-4'>
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex gap-2 items-start ${
                    msg.sender === 'user' ? 'ml-auto flex-row-reverse' : ''
                  }`}
                  style={{ maxWidth: '80%' }}
                >
                  <div className='mt-1 flex-shrink-0'>
                    {msg.sender === 'user' ? (
                      <User className='w-5 h-5 text-primary' />
                    ) : (
                      <Bot className='w-5 h-5 text-muted-foreground' />
                    )}
                  </div>
                  <div className='flex flex-col items-start w-full'>
                    <div
                      className={`rounded-xl px-4 py-2 text-sm whitespace-pre-wrap break-words w-full ${
                        msg.sender === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-card-foreground'
                      }`}
                    >
                      {msg.text}
                    </div>
                    <span className='text-xs text-muted-foreground mt-1'>
                      {msg.timestamp}
                    </span>
                  </div>
                </div>
              ))}
              
              {messages.length === 0 && !currentSessionId && (
                <div className='text-center text-muted-foreground text-sm py-8'>
                  <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="mb-2">Start a new session to begin chatting about your medical records.</p>
                  <Button onClick={startNewSession} size="sm">
                    Start New Chat
                  </Button>
                </div>
              )}
              
              {messages.length === 0 && currentSessionId && (
                <div className='text-center text-muted-foreground text-sm py-8'>
                  <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Ask me anything about your uploaded prescriptions, medications, schedules, or health guidance.</p>
                  <div className="mt-4 text-xs">
                    <p>Try asking:</p>
                    <ul className="mt-2 space-y-1">
                      <li>"What medications am I currently taking?"</li>
                      <li>"How is my medication adherence?"</li>
                      <li>"What are my medication schedules?"</li>
                      <li>"Tell me about my recent prescriptions"</li>
                    </ul>
                  </div>
                </div>
              )}
              
              {isLoading && (
                <div className="flex gap-2 items-start">
                  <Bot className='w-5 h-5 text-muted-foreground mt-1' />
                  <div className="bg-muted text-card-foreground rounded-xl px-4 py-2 text-sm flex items-center gap-2">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Analyzing your medical data...
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>

        <div className='p-4 border-t border-border'>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className='flex space-x-2'
          >
            <Input
              placeholder='Ask about your prescriptions, medications, schedules, or health guidance...'
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading || !currentSessionId}
              className="bg-background text-foreground border-border"
            />
            <Button 
              type='submit' 
              disabled={isLoading || !currentSessionId || !input.trim()}
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Send'}
            </Button>
          </form>
          {!currentSessionId && (
            <p className="text-xs text-muted-foreground mt-2 text-center">
              Start a new session to begin chatting
            </p>
          )}
        </div>
      </Card>
    </div>
  );
};

export default Chat;