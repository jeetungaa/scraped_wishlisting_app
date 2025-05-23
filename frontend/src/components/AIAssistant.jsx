import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  Paper, 
  Avatar, 
  List, 
  ListItem, 
  ListItemAvatar, 
  ListItemText,
  IconButton
} from '@mui/material';
import { Send, SmartToy } from '@mui/icons-material';
import axios from 'axios';

const AIAssistant = () => {
  const [messages, setMessages] = useState([
    { text: "Hi! I'm your shopping assistant. How can I help you today?", sender: 'ai' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!input.trim()) return;
  
    const userMessage = { text: input, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
  
    try {
      console.log("Sending request to backend..."); // Debug log
      const response = await axios.post('http://127.0.0.1:5000/ai-assistant', {
        message: input,
        chat_history: messages
      }, {
        timeout: 10000 // 10 second timeout
      });
      console.log("Received response:", response); // Debug log
      
      const aiMessage = { text: response.data.response, sender: 'ai' };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error("Full error details:", {
        message: error.message,
        response: error.response,
        request: error.request,
        config: error.config
      });
      
      const errorMessage = { 
        text: error.response?.data?.error || 
             "Sorry, I'm having trouble connecting. Please try again later.",
        sender: 'ai' 
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ 
      position: 'fixed', 
      bottom: 16, 
      right: 16, 
      width: 350,
      height: 500,
      display: 'flex',
      flexDirection: 'column',
      bgcolor: 'background.paper',
      boxShadow: 3,
      borderRadius: 2,
      overflow: 'hidden'
    }}>
      <Box sx={{ 
        bgcolor: 'primary.main', 
        color: 'white', 
        p: 2,
        display: 'flex',
        alignItems: 'center'
      }}>
        <SmartToy sx={{ mr: 1 }} />
        <Typography variant="h6">Shopping Assistant</Typography>
      </Box>
      
      <Box sx={{ 
        flex: 1, 
        p: 2, 
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 1
      }}>
        {messages.map((msg, index) => (
          <Box
            key={index}
            sx={{
              alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '80%'
            }}
          >
            <Paper
              elevation={1}
              sx={{
                p: 1.5,
                bgcolor: msg.sender === 'user' ? 'primary.light' : 'grey.100',
                color: msg.sender === 'user' ? 'white' : 'text.primary',
                borderRadius: msg.sender === 'user' 
                  ? '18px 18px 4px 18px' 
                  : '18px 18px 18px 4px'
              }}
            >
              <Typography>{msg.text}</Typography>
            </Paper>
          </Box>
        ))}
        {isLoading && (
          <Box sx={{ alignSelf: 'flex-start' }}>
            <Paper elevation={1} sx={{ p: 1.5, bgcolor: 'grey.100' }}>
              <Typography>Thinking...</Typography>
            </Paper>
          </Box>
        )}
      </Box>
      
      <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Ask me anything..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          />
          <IconButton 
            color="primary" 
            onClick={handleSendMessage}
            disabled={isLoading}
          >
            <Send />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
};

export default AIAssistant;