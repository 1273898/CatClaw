import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
} from '@mui/material'
import { IconDeviceFloppy } from '@tabler/icons-react'

function SettingsPage() {
  const [settings, setSettings] = useState({
    llm_provider: 'deepseek',
    llm_model: 'deepseek-v4-flash',
    llm_temperature: 0.7,
    memory_short_term_limit: 50,
    memory_long_term_enabled: true,
  })

  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const response = await fetch('/api/settings')
      const data = await response.json()
      setSettings(data)
    } catch (error) {
      console.error('加载设置失败:', error)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      })
    } catch (error) {
      console.error('保存设置失败:', error)
    } finally {
      setSaving(false)
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
        <Typography variant="h6">设置</Typography>
        <Button
          variant="contained"
          startIcon={<IconDeviceFloppy />}
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? '保存中...' : '保存'}
        </Button>
      </Box>

      <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            大模型配置
          </Typography>
          <Divider sx={{ mb: 2 }} />

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>提供商</InputLabel>
            <Select
              value={settings.llm_provider}
              label="提供商"
              onChange={(e) => setSettings({ ...settings, llm_provider: e.target.value })}
            >
              <MenuItem value="deepseek">DeepSeek</MenuItem>
              <MenuItem value="openai">OpenAI</MenuItem>
              <MenuItem value="anthropic">Anthropic</MenuItem>
              <MenuItem value="ollama">Ollama (本地)</MenuItem>
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="模型"
            value={settings.llm_model}
            onChange={(e) => setSettings({ ...settings, llm_model: e.target.value })}
            sx={{ mb: 2 }}
          />

          <TextField
            fullWidth
            label="温度"
            type="number"
            value={settings.llm_temperature}
            onChange={(e) => setSettings({ ...settings, llm_temperature: parseFloat(e.target.value) })}
            inputProps={{ min: 0, max: 2, step: 0.1 }}
          />
        </Paper>

        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            记忆设置
          </Typography>
          <Divider sx={{ mb: 2 }} />

          <TextField
            fullWidth
            label="短期记忆限制"
            type="number"
            value={settings.memory_short_term_limit}
            onChange={(e) => setSettings({ ...settings, memory_short_term_limit: parseInt(e.target.value) })}
            sx={{ mb: 2 }}
          />

          <FormControlLabel
            control={
              <Switch
                checked={settings.memory_long_term_enabled}
                onChange={(e) => setSettings({ ...settings, memory_long_term_enabled: e.target.checked })}
              />
            }
            label="启用长期记忆"
          />
        </Paper>
      </Box>
    </Box>
  )
}

export default SettingsPage
