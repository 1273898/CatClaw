import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
} from '@mui/material'
import { IconTool, IconTerminal, IconWorld, IconFile } from '@tabler/icons-react'

const categoryIcons = {
  system: IconTerminal,
  web: IconWorld,
  file: IconFile,
  default: IconTool,
}

function ToolsPage() {
  const [tools, setTools] = useState([])

  useEffect(() => {
    loadTools()
  }, [])

  const loadTools = async () => {
    try {
      const response = await fetch('/api/tools')
      const data = await response.json()
      setTools(data.tools)
    } catch (error) {
      console.error('加载工具失败:', error)
    }
  }

  const getCategoryIcon = (category) => {
    return categoryIcons[category] || categoryIcons.default
  }

  const getCategoryColor = (category) => {
    const colors = {
      system: 'error',
      web: 'info',
      file: 'success',
      search: 'warning',
    }
    return colors[category] || 'default'
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Typography variant="h6">工具箱</Typography>
        <Typography variant="caption" color="text.secondary">
          {tools.length} 个可用工具
        </Typography>
      </Box>

      <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
        <Grid container spacing={2}>
          {tools.map((tool) => {
            const Icon = getCategoryIcon(tool.category)
            return (
              <Grid item xs={12} sm={6} md={4} key={tool.name}>
                <Card
                  sx={{
                    height: '100%',
                    transition: 'transform 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                    },
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <IconButton
                        sx={{
                          bgcolor: `${getCategoryColor(tool.category)}.light`,
                          color: `${getCategoryColor(tool.category)}.contrastText`,
                        }}
                      >
                        <Icon size={20} />
                      </IconButton>
                      <Typography variant="h6">{tool.name}</Typography>
                    </Box>

                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {tool.description}
                    </Typography>

                    <Chip
                      label={tool.category}
                      size="small"
                      color={getCategoryColor(tool.category)}
                      variant="outlined"
                    />
                  </CardContent>
                </Card>
              </Grid>
            )
          })}
        </Grid>
      </Box>
    </Box>
  )
}

export default ToolsPage
