import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  IconButton,
  Button,
  Paper,
  Chip,
} from '@mui/material'
import { IconTrash, IconPlus } from '@tabler/icons-react'

function SessionsPage({ onSessionSelect }) {
  const [sessions, setSessions] = useState([])

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      const response = await fetch('/api/sessions')
      const data = await response.json()
      setSessions(data.sessions)
    } catch (error) {
      console.error('加载会话失败:', error)
    }
  }

  const deleteSession = async (sessionId) => {
    try {
      await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' })
      loadSessions()
    } catch (error) {
      console.error('删除会话失败:', error)
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box>
          <Typography variant="h6">会话管理</Typography>
          <Typography variant="caption" color="text.secondary">
            {sessions.length} 个会话
          </Typography>
        </Box>
        <Button
          startIcon={<IconPlus />}
          variant="contained"
          size="small"
        >
          新建会话
        </Button>
      </Box>

      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <List>
          {sessions.map((sessionId) => (
            <Paper key={sessionId} sx={{ mb: 1 }}>
              <ListItem
                secondaryAction={
                  <IconButton
                    edge="end"
                    onClick={() => deleteSession(sessionId)}
                  >
                    <IconTrash size={18} />
                  </IconButton>
                }
              >
                <ListItemButton onClick={() => onSessionSelect(sessionId)}>
                  <ListItemText
                    primary={sessionId}
                    secondary="点击进入会话"
                  />
                </ListItemButton>
              </ListItem>
            </Paper>
          ))}
        </List>
      </Box>
    </Box>
  )
}

export default SessionsPage
