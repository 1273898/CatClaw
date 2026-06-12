import React, { useState, useRef, useEffect } from 'react'
import {
  Box,
  Typography,
  TextField,
  IconButton,
  Paper,
  Avatar,
  Chip,
} from '@mui/material'
import { IconSend, IconRobot, IconUser } from '@tabler/icons-react'

function ChatPage({ sessionId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          session_id: sessionId,
        }),
      })

      const data = await response.json()
      const aiMessage = { role: 'assistant', content: data.response }
      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      const errorMessage = { role: 'assistant', content: '错误: ' + error.message }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Typography variant="h6">聊天</Typography>
        <Typography variant="caption" color="text.secondary">
          会话: {sessionId}
        </Typography>
      </Box>

      {/* Messages */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        {messages.length === 0 ? (
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 2,
            }}
          >
            <Avatar sx={{ width: 64, height: 64, bgcolor: 'primary.main' }}>
              <IconRobot size={32} />
            </Avatar>
            <Typography variant="h6" color="text.secondary">
              PrivateClaw
            </Typography>
            <Typography variant="body2" color="text.secondary">
              开始对话吧！
            </Typography>
          </Box>
        ) : (
          messages.map((msg, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                gap: 1,
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              }}
            >
              <Avatar
                sx={{
                  bgcolor: msg.role === 'user' ? 'secondary.main' : 'primary.main',
                }}
              >
                {msg.role === 'user' ? <IconUser size={20} /> : <IconRobot size={20} />}
              </Avatar>
              <Paper
                sx={{
                  p: 2,
                  maxWidth: '70%',
                  bgcolor: msg.role === 'user' ? 'secondary.main' : 'background.paper',
                  borderRadius: 2,
                }}
              >
                <Typography variant="body1">{msg.content}</Typography>
              </Paper>
            </Box>
          ))
        )}
        {loading && (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              <IconRobot size={20} />
            </Avatar>
            <Paper sx={{ p: 2, bgcolor: 'background.paper' }}>
              <Typography variant="body2" color="text.secondary">
                思考中...
              </Typography>
            </Paper>
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input */}
      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="输入消息... (Enter 发送，Shift+Enter 换行)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <IconButton
            color="primary"
            onClick={handleSend}
            disabled={!input.trim() || loading}
          >
            <IconSend />
          </IconButton>
        </Box>
      </Box>
    </Box>
  )
}

export default ChatPage
