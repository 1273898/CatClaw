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
  TextField,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
} from '@mui/material'
import {
  IconTrash,
  IconPlus,
  IconSearch,
  IconClock,
  IconMessage,
  IconBrandTelegram,
  IconWorld,
  IconDeviceDesktop,
} from '@tabler/icons-react'

function SessionsPage({ onSessionSelect }) {
  const [sessions, setSessions] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [newSessionId, setNewSessionId] = useState('')

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      const response = await fetch('/api/sessions')
      const data = await response.json()
      setSessions(data.sessions || [])
    } catch (error) {
      console.error('加载会话失败:', error)
    }
  }

  const createSession = async () => {
    if (!newSessionId.trim()) return

    try {
      await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: newSessionId }),
      })
      setCreateDialogOpen(false)
      setNewSessionId('')
      loadSessions()
    } catch (error) {
      console.error('创建会话失败:', error)
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

  const formatTime = (isoString) => {
    if (!isoString) return ''
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins} 分钟前`
    if (diffHours < 24) return `${diffHours} 小时前`
    if (diffDays < 7) return `${diffDays} 天前`
    return date.toLocaleDateString('zh-CN')
  }

  const getChannelInfo = (channel) => {
    switch (channel) {
      case 'qq':
        return { label: 'QQ', color: '#12B7F5', icon: <IconBrandTelegram size={14} /> }
      case 'feishu':
        return { label: '飞书', color: '#3370FF', icon: <IconBrandTelegram size={14} /> }
      case 'web':
        return { label: '网页', color: '#E94560', icon: <IconWorld size={14} /> }
      case 'cli':
        return { label: 'CLI', color: '#52c41a', icon: <IconDeviceDesktop size={14} /> }
      default:
        return { label: channel || '未知', color: '#999', icon: <IconMessage size={14} /> }
    }
  }

  const filteredSessions = sessions.filter((session) =>
    session.session_id.toLowerCase().includes(searchQuery.toLowerCase())
  )

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
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
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
            onClick={() => setCreateDialogOpen(true)}
          >
            新建会话
          </Button>
        </Box>

        {/* Search */}
        <TextField
          fullWidth
          size="small"
          placeholder="搜索会话..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <IconSearch size={18} />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {/* Sessions List */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <List>
          {filteredSessions.map((session) => (
            <Paper key={session.session_id} sx={{ mb: 1, overflow: 'hidden' }}>
              <ListItem
                disablePadding
                secondaryAction={
                  <IconButton
                    edge="end"
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteSession(session.session_id)
                    }}
                    sx={{ mr: 1 }}
                  >
                    <IconTrash size={18} />
                  </IconButton>
                }
              >
                <ListItemButton onClick={() => onSessionSelect(session.session_id)}>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                          {session.session_id}
                        </Typography>
                        {session.channel && (
                          <Chip
                            icon={getChannelInfo(session.channel).icon}
                            label={getChannelInfo(session.channel).label}
                            size="small"
                            sx={{
                              bgcolor: getChannelInfo(session.channel).color + '20',
                              color: getChannelInfo(session.channel).color,
                              border: `1px solid ${getChannelInfo(session.channel).color}40`,
                              fontWeight: 500,
                            }}
                          />
                        )}
                        {session.is_active && (
                          <Chip
                            label="活跃"
                            size="small"
                            color="success"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 0.5 }}>
                        {session.last_message && (
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              mb: 0.5,
                            }}
                          >
                            {session.last_message}
                          </Typography>
                        )}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <IconMessage size={14} color="gray" />
                            <Typography variant="caption" color="text.secondary">
                              {session.message_count || 0} 条消息
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <IconClock size={14} color="gray" />
                            <Typography variant="caption" color="text.secondary">
                              {formatTime(session.last_active)}
                            </Typography>
                          </Box>
                        </Box>
                      </Box>
                    }
                  />
                </ListItemButton>
              </ListItem>
            </Paper>
          ))}

          {filteredSessions.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography color="text.secondary">
                {searchQuery ? '没有找到匹配的会话' : '暂无会话'}
              </Typography>
            </Box>
          )}
        </List>
      </Box>

      {/* Create Session Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)}>
        <DialogTitle>新建会话</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="会话 ID"
            fullWidth
            variant="outlined"
            value={newSessionId}
            onChange={(e) => setNewSessionId(e.target.value)}
            placeholder="输入会话名称..."
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>取消</Button>
          <Button onClick={createSession} variant="contained">创建</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default SessionsPage
