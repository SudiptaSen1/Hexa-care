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
import { Bot, User, MessageSquare, Plus } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const Chat = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const userId = 'user123'; // Replace with actual user ID from auth

  // Load user sessions on component mount
  useEffect(() => {
    loadUserSessions();
  }, []);

  const loadUserSessions = async () => {
    try {
      const response = await fetch(`${API_BASE}/sessions/${userId}`);
      const data = await response.json();
      if (response.ok) {
        setSessions(data.sessions || []);
      }
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const startNewSession = async () => {
    try {
      const response = await fetch(`${API_BASE}/sessions/start/${userId}`, {
        method: 'POST'
      });
      const data = await response.json();
      if (response.ok) {
        setCurrentSessionId(data.session_id);
        setMessages([]);
        await loadUserSessions(); // Refresh sessions list
      }
    } catch (error) {
      console.error('Error starting new session:', error);
    }
  };

  const loadChatHistory = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE}/history/${userId}/${sessionId}`);
      const data = await response.json();
      if (response.ok) {
        const formattedMessages = data.chat_history.map(msg => ({
          sender: msg.type === 'human' ? 'user' : 'bot',
          text: msg.content,
          timestamp: new Date().toLocaleTimeString()
        }));
        setMessages(formattedMessages);
        setCurrentSessionId(sessionId);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !currentSessionId) {
      if (!currentSessionId) {
        alert('Please start a new session first');
      }
      return;
    }

    const userMessage = {
      sender: 'user',
      text: input,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/sessions/${userId}/${currentSessionId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: input })
      });

      const data = await response.json();
      
      if (response.ok) {
        const botMessage = {
          sender: 'bot',
          text: data.answer,
          timestamp: new Date().toLocaleTimeString(),
        };
        setMessages(prev => [...prev, botMessage]);
      } else {
        const errorMessage = {
          sender: 'bot',
          text: 'Sorry, I encountered an error processing your message.',
          timestamp: new Date().toLocaleTimeString(),
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        sender: 'bot',
        text: 'Sorry, I\'m having trouble connecting right now.',
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className='flex h-[600px] max-w-6xl mx-auto p-4 gap-4'>
      {/* Sessions Sidebar */}
      <Card className='w-80 flex flex-col'>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Chat Sessions</span>
            <Button size="sm" onClick={startNewSession}>
              <Plus className="h-4 w-4" />
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent className='flex-1 overflow-hidden'>
          <ScrollArea className='h-full'>
            <div className='space-y-2'>
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    currentSessionId === session.session_id
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted hover:bg-muted/80'
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
              ))}
              {sessions.length === 0 && (
                <div className="text-center text-muted-foreground text-sm py-4">
                  No chat sessions yet. Start a new one!
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Chat Area */}
      <Card className='flex-1 flex flex-col overflow-hidden'>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Medical Assistant Chat
            {currentSessionId && (
              <span className="text-sm font-normal text-muted-foreground">
                (Session Active)
              </span>
            )}
          </CardTitle>
        </CardHeader>

        <CardContent className='p-4 flex-1 overflow-hidden'>
          <ScrollArea className='h-full pr-2'>
            <div className='space-y-4'>
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex gap-2 items-start max-w-xs ${
                    msg.sender === 'user' ? 'ml-auto flex-row-reverse' : ''
                  }`}
                >
                  <div className='mt-1'>
                    {msg.sender === 'user' ? (
                      <User className='w-5 h-5 text-primary' />
                    ) : (
                      <Bot className='w-5 h-5 text-muted-foreground' />
                    )}
                  </div>
                  <div className='flex flex-col items-start'>
                    <div
                      className={`rounded-xl px-4 py-2 text-sm whitespace-pre-line ${
                        msg.sender === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted text-muted-foreground'
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
                <div className='text-center text-muted-foreground text-sm'>
                  Start a new session to begin chatting about your medical records.
                </div>
              )}
              {messages.length === 0 && currentSessionId && (
                <div className='text-center text-muted-foreground text-sm'>
                  Ask me anything about your uploaded prescriptions and medical history.
                </div>
              )}
              {isLoading && (
                <div className="flex gap-2 items-start max-w-xs">
                  <Bot className='w-5 h-5 text-muted-foreground mt-1' />
                  <div className="bg-muted text-muted-foreground rounded-xl px-4 py-2 text-sm">
                    Thinking...
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>

        <div className='p-4 border-t'>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className='flex space-x-2'
          >
            <Input
              placeholder='Ask about your prescriptions, medications, or health records...'
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading || !currentSessionId}
            />
            <Button 
              type='submit' 
              disabled={isLoading || !currentSessionId || !input.trim()}
            >
              Send
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
};

export default Chat;