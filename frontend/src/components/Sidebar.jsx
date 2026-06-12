import React from 'react'
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
} from '@tabler/icons-react'

const menuItems = [
  { id: 'chat', label: '聊天', icon: IconMessage },
  { id: 'sessions', label: '会话', icon: IconList },
  { id: 'tools', label: '工具', icon: IconTool },
  { id: 'memory', label: '记忆', icon: IconBrain },
  { id: 'prompts', label: '提示词', icon: IconFileText },
  { id: 'settings', label: '设置', icon: IconSettings },
]

function Sidebar({ currentPage, onNavigate }) {
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
          sx={{
            width: 32,
            height: 32,
            borderRadius: 2,
            bgcolor: 'primary.main',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography variant="h6" sx={{ color: 'white', fontWeight: 700 }}>
            P
          </Typography>
        </Box>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          PrivateClaw
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
          onClick={() => onNavigate('chat')}
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
