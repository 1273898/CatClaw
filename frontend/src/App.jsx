import React, { useState, useCallback } from 'react'
import { Box } from '@mui/material'
import Sidebar from './components/Sidebar'
import DesktopPet from './components/DesktopPet'
import ChatPage from './pages/ChatPage'
import SessionsPage from './pages/SessionsPage'
import SkillsPage from './pages/SkillsPage'
import ChannelsPage from './pages/ChannelsPage'
import ToolsPage from './pages/ToolsPage'
import MemoryPage from './pages/MemoryPage'
import PromptsPage from './pages/PromptsPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  const [currentPage, setCurrentPage] = useState('chat')
  const [sessionId, setSessionId] = useState('default')

  // 创建新会话
  const createNewSession = useCallback(async () => {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    const newSessionId = `会话_${timestamp}`

    try {
      await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: newSessionId }),
      })
      setSessionId(newSessionId)
      return newSessionId
    } catch (error) {
      console.error('创建会话失败:', error)
      return null
    }
  }, [])

  // 处理第一次发送消息时自动创建会话
  const handleFirstMessage = useCallback(async () => {
    if (sessionId === 'default') {
      const newSessionId = await createNewSession()
      return newSessionId
    }
    return sessionId
  }, [sessionId, createNewSession])

  const renderPage = () => {
    switch (currentPage) {
      case 'chat':
        return (
          <ChatPage
            sessionId={sessionId}
            onFirstMessage={handleFirstMessage}
            onSessionChange={setSessionId}
          />
        )
      case 'sessions':
        return <SessionsPage onSessionSelect={(id) => {
          setSessionId(id)
          setCurrentPage('chat')
        }} />
      case 'skills':
        return <SkillsPage />
      case 'channels':
        return <ChannelsPage />
      case 'tools':
        return <ToolsPage />
      case 'memory':
        return <MemoryPage />
      case 'prompts':
        return <PromptsPage />
      case 'settings':
        return <SettingsPage />
      default:
        return <ChatPage sessionId={sessionId} onFirstMessage={handleFirstMessage} onSessionChange={setSessionId} />
    }
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <Sidebar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        onNewChat={() => {
          setSessionId('default')
          setCurrentPage('chat')
        }}
      />
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        {renderPage()}
      </Box>
      <DesktopPet />
    </Box>
  )
}

export default App
