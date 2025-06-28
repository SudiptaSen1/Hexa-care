import React, { useState } from 'react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card';
import { ScrollArea } from '../components/ui/scroll-area';
import { Bot, User } from 'lucide-react'; // 🧠 👤 Icons

const Chat = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]); // Start empty

  const handleSend = () => {
    if (!input.trim()) return;

    const newMessage = {
      sender: 'user',
      text: input,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInput('');

    setTimeout(() => {
      const botMessage = {
        sender: 'bot',
        text: 'I’m reviewing your symptoms... hang tight!',
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, botMessage]);
    }, 1000);
  };

  return (
    <div className='flex flex-col h-[600px] max-w-2xl mx-auto p-4'>
      <Card className='flex-1 flex flex-col overflow-hidden'>
        <CardHeader>
          <CardTitle>Medical Assistant Chat</CardTitle>
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
                          ? 'bg-rose-500 text-white'
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
              {messages.length === 0 && (
                <div className='text-center text-muted-foreground text-sm'>
                  Start a conversation about your symptoms or concerns.
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className='flex mt-4 space-x-2'
      >
        <Input
          placeholder='Describe your symptoms...'
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <Button type='submit'>Send</Button>
      </form>
    </div>
  );
};

export default Chat;
