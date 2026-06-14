import React, { useState, useEffect } from 'react'
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  IconButton,
} from '@mui/material'
import {
  IconMessage,
  IconList,
  IconTool,
  IconBrain,
  IconFileText,
  IconSettings,
  IconPlus,
  IconStar,
  IconPlug,
} from '@tabler/icons-react'

const menuItems = [
  { id: 'chat', label: '聊天', icon: IconMessage },
  { id: 'sessions', label: '会话', icon: IconList },
  { id: 'skills', label: 'SKILLS', icon: IconStar },
  { id: 'channels', label: '渠道', icon: IconPlug },
  { id: 'tools', label: '工具', icon: IconTool },
  { id: 'memory', label: '记忆', icon: IconBrain },
  { id: 'prompts', label: '提示词', icon: IconFileText },
  { id: 'settings', label: '设置', icon: IconSettings },
]

// 猫咪图标列表
const catIcons = [
  '/cats/波斯猫.svg',
  '/cats/黑猫.svg',
  '/cats/狸花猫.svg',
  '/cats/缅因猫.svg',
  '/cats/田园猫.svg',
  '/cats/暹罗猫.svg',
]

function Sidebar({ currentPage, onNavigate, onNewChat }) {
  const [currentCat, setCurrentCat] = useState(() => {
    // 随机选择一个猫咪图标
    const randomIndex = Math.floor(Math.random() * catIcons.length)
    return catIcons[randomIndex]
  })

  // 当页面导航时更换猫咪图标
  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * catIcons.length)
    setCurrentCat(catIcons[randomIndex])
  }, [currentPage])

  return (
    <Box
      sx={{
        width: 240,
        bgcolor: 'background.paper',
        borderRight: 1,
        borderColor: 'divider',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Logo */}
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box
          component="img"
          src={currentCat}
          alt="CatClaw"
          sx={{
            width: 32,
            height: 32,
            borderRadius: 1,
            objectFit: 'contain',
          }}
        />
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          CatClaw
        </Typography>
      </Box>

      <Divider />

      {/* New Chat Button */}
      <Box sx={{ p: 1 }}>
        <IconButton
          fullWidth
          sx={{
            border: 1,
            borderColor: 'divider',
            borderRadius: 2,
            mb: 1,
          }}
          onClick={() => {
            if (onNewChat) {
              onNewChat()
            } else {
              onNavigate('chat')
            }
          }}
        >
          <IconPlus size={18} />
          <Typography variant="body2" sx={{ ml: 1 }}>
            新对话
          </Typography>
        </IconButton>
      </Box>

      {/* Menu Items */}
      <List sx={{ flex: 1, px: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.id} disablePadding>
            <ListItemButton
              selected={currentPage === item.id}
              onClick={() => onNavigate(item.id)}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                '&.Mui-selected': {
                  bgcolor: 'primary.main',
                  color: 'white',
                  '&:hover': {
                    bgcolor: 'primary.dark',
                  },
                },
              }}
            >
              <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                <item.icon size={20} />
              </ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* Footer */}
      <Divider />
      <Box sx={{ p: 2 }}>
        <Typography variant="caption" color="text.secondary">
          v0.1.0 · 本地模式
        </Typography>
      </Box>
    </Box>
  )
}

export default Sidebar
