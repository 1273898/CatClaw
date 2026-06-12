import React, { useState } from 'react'
import { Box } from '@mui/material'
import Sidebar from './components/Sidebar'
import ChatPage from './pages/ChatPage'
import SessionsPage from './pages/SessionsPage'
import ToolsPage from './pages/ToolsPage'
import MemoryPage from './pages/MemoryPage'
import PromptsPage from './pages/PromptsPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  const [currentPage, setCurrentPage] = useState('chat')
  const [sessionId, setSessionId] = useState('default')

  const renderPage = () => {
    switch (currentPage) {
      case 'chat':
        return <ChatPage sessionId={sessionId} />
      case 'sessions':
        return <SessionsPage onSessionSelect={(id) => {
          setSessionId(id)
          setCurrentPage('chat')
        }} />
      case 'tools':
        return <ToolsPage />
      case 'memory':
        return <MemoryPage />
      case 'prompts':
        return <PromptsPage />
      case 'settings':
        return <SettingsPage />
      default:
        return <ChatPage sessionId={sessionId} />
    }
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <Sidebar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
      />
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        {renderPage()}
      </Box>
    </Box>
  )
}

export default App
