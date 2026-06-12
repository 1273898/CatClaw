import React, { useState } from 'react'
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
} from '@mui/material'
import { IconSearch, IconDatabase } from '@tabler/icons-react'

function MemoryPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) return

    setLoading(true)
    try {
      const response = await fetch('/api/memory/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, k: 10 }),
      })
      const data = await response.json()
      setResults(data.results)
    } catch (error) {
      console.error('搜索失败:', error)
    } finally {
      setLoading(false)
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
        }}
      >
        <Typography variant="h6">记忆库</Typography>
        <Typography variant="caption" color="text.secondary">
          搜索长期记忆
        </Typography>
      </Box>

      <Box sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <TextField
            fullWidth
            placeholder="搜索记忆..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button
            variant="contained"
            startIcon={<IconSearch />}
            onClick={handleSearch}
            disabled={loading}
          >
            搜索
          </Button>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <IconDatabase size={20} />
          <Typography variant="body2" color="text.secondary">
            {results.length} 条结果
          </Typography>
        </Box>

        <List>
          {results.map((result, index) => (
            <Paper key={index} sx={{ mb: 2 }}>
              <ListItem>
                <ListItemText
                  primary={result.content.substring(0, 100) + '...'}
                  secondary={
                    <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                      <Chip
                        label={`分数: ${result.score?.toFixed(2) || 'N/A'}`}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                      {result.metadata?.source && (
                        <Chip
                          label={result.metadata.source}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  }
                />
              </ListItem>
            </Paper>
          ))}
        </List>
      </Box>
    </Box>
  )
}

export default MemoryPage
