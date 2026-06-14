import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Switch,
  TextField,
  Button,
  Alert,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  IconButton,
  Tooltip,
  Divider,
} from '@mui/material'
import {
  IconBrandTelegram,
  IconBrandDiscord,
  IconBrandSlack,
  IconMessage,
  IconSettings,
  IconRefresh,
  IconCheck,
  IconX,
} from '@tabler/icons-react'

const channelConfigs = [
  {
    id: 'web',
    name: 'Web 界面',
    icon: IconMessage,
    color: '#1976d2',
    description: '默认的 Web 聊天界面',
    fields: [],
  },
  {
    id: 'qq',
    name: 'QQ 机器人',
    icon: IconMessage,
    color: '#12b7f5',
    description: '接入 QQ 开放平台机器人',
    fields: [
      { key: 'bot_id', label: 'AppID', placeholder: '在 q.qq.com 创建应用后获取' },
      { key: 'bot_secret', label: 'AppSecret', placeholder: '在应用的开发设置中获取', type: 'password' },
      { key: 'sandbox', label: '沙箱模式（测试用）', type: 'switch', default: true },
    ],
    docsUrl: 'https://q.qq.com',
  },
  {
    id: 'feishu',
    name: '飞书机器人',
    icon: IconMessage,
    color: '#3370ff',
    description: '接入飞书开放平台机器人',
    fields: [
      { key: 'app_id', label: 'App ID', placeholder: '你的飞书 App ID' },
      { key: 'app_secret', label: 'App Secret', placeholder: '你的飞书 App Secret', type: 'password' },
      { key: 'verification_token', label: 'Verification Token', placeholder: '事件订阅验证 Token' },
      { key: 'encrypt_key', label: 'Encrypt Key', placeholder: '加密密钥（可选）', type: 'password' },
    ],
    docsUrl: 'https://open.feishu.cn',
  },
  {
    id: 'telegram',
    name: 'Telegram',
    icon: IconBrandTelegram,
    color: '#0088cc',
    description: '接入 Telegram Bot',
    fields: [
      { key: 'token', label: 'Bot Token', placeholder: '通过 @BotFather 获取', type: 'password' },
    ],
    docsUrl: 'https://core.telegram.org/bots',
  },
  {
    id: 'discord',
    name: 'Discord',
    icon: IconBrandDiscord,
    color: '#5865f2',
    description: '接入 Discord Bot',
    fields: [
      { key: 'token', label: 'Bot Token', placeholder: 'Discord Developer Portal 获取', type: 'password' },
    ],
    docsUrl: 'https://discord.com/developers',
  },
  {
    id: 'slack',
    name: 'Slack',
    icon: IconBrandSlack,
    color: '#e01e5a',
    description: '接入 Slack Bot',
    fields: [
      { key: 'token', label: 'Bot Token', placeholder: 'xoxb-...' },
      { key: 'app_token', label: 'App Token', placeholder: 'xapp-...', type: 'password' },
    ],
    docsUrl: 'https://api.slack.com',
  },
]

function ChannelsPage() {
  const [channels, setChannels] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(null)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [webhookUrl, setWebhookUrl] = useState('')

  useEffect(() => {
    loadChannels()
    // Get webhook base URL
    setWebhookUrl(`${window.location.origin}/webhook`)
  }, [])

  const loadChannels = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/channels/config')
      const data = await response.json()
      setChannels(data.config || {})
    } catch (err) {
      console.error('Failed to load channels:', err)
      // Initialize with defaults
      const defaults = {}
      channelConfigs.forEach(ch => {
        defaults[ch.id] = { enabled: false }
        ch.fields.forEach(f => {
          defaults[ch.id][f.key] = f.default || ''
        })
      })
      setChannels(defaults)
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = async (channelId) => {
    const newEnabled = !channels[channelId]?.enabled
    setChannels(prev => ({
      ...prev,
      [channelId]: { ...prev[channelId], enabled: newEnabled },
    }))

    // Save to backend
    await saveChannel(channelId, { ...channels[channelId], enabled: newEnabled })
  }

  const handleFieldChange = (channelId, fieldKey, value) => {
    setChannels(prev => ({
      ...prev,
      [channelId]: { ...prev[channelId], [fieldKey]: value },
    }))
  }

  const saveChannel = async (channelId, config) => {
    try {
      setSaving(channelId)
      setError(null)

      const response = await fetch('/api/channels/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel: channelId, config }),
      })

      if (response.ok) {
        setSuccess(`${channelId} 配置已保存`)
        setTimeout(() => setSuccess(null), 3000)
      } else {
        setError(`保存 ${channelId} 配置失败`)
      }
    } catch (err) {
      setError(`保存失败: ${err.message}`)
    } finally {
      setSaving(null)
    }
  }

  const handleSave = async (channelId) => {
    await saveChannel(channelId, channels[channelId])
  }

  const renderChannelCard = (channelDef) => {
    const channelId = channelDef.id
    const config = channels[channelId] || {}
    const IconComponent = channelDef.icon
    const isEnabled = config.enabled || false

    return (
      <Grid item xs={12} md={6} key={channelId}>
        <Card
          sx={{
            border: '1px solid',
            borderColor: isEnabled ? channelDef.color : 'divider',
            transition: 'all 0.3s',
            '&:hover': {
              borderColor: channelDef.color,
              boxShadow: 2,
            },
          }}
        >
          <CardContent>
            {/* Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: 1,
                    bgcolor: channelDef.color + '20',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <IconComponent size={24} color={channelDef.color} />
                </Box>
                <Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    {channelDef.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {channelDef.description}
                  </Typography>
                </Box>
              </Box>
              <Switch
                checked={isEnabled}
                onChange={() => handleToggle(channelId)}
                sx={{
                  '& .MuiSwitch-switchBase.Mui-checked': {
                    color: channelDef.color,
                  },
                  '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                    bgcolor: channelDef.color,
                  },
                }}
              />
            </Box>

            {/* Status */}
            <Box sx={{ mb: 2 }}>
              <Chip
                icon={isEnabled ? <IconCheck size={14} /> : <IconX size={14} />}
                label={isEnabled ? '已启用' : '未启用'}
                size="small"
                color={isEnabled ? 'success' : 'default'}
                variant="outlined"
              />
            </Box>

            {/* Webhook URL for bot channels */}
            {channelId !== 'web' && channelId !== 'cli' && (
              <Box sx={{ mb: 2, p: 1.5, bgcolor: '#e3f2fd', borderRadius: 1, border: '1px solid #90caf9' }}>
                <Typography variant="caption" color="primary" sx={{ display: 'block', mb: 0.5, fontWeight: 600 }}>
                  Webhook 地址:
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
                    wordBreak: 'break-all',
                    color: '#1565c0',
                    fontWeight: 500,
                    bgcolor: '#fff',
                    p: 0.75,
                    borderRadius: 0.5,
                    border: '1px solid #bbdefb',
                  }}
                >
                  {webhookUrl}/{channelId}
                </Typography>
              </Box>
            )}

            {/* Configuration Fields */}
            {isEnabled && channelDef.fields.length > 0 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {channelDef.fields.map((field) => (
                  <Box key={field.key}>
                    {field.type === 'switch' ? (
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Typography variant="body2">{field.label}</Typography>
                        <Switch
                          checked={config[field.key] ?? field.default ?? false}
                          onChange={(e) => handleFieldChange(channelId, field.key, e.target.checked)}
                          size="small"
                        />
                      </Box>
                    ) : (
                      <TextField
                        fullWidth
                        size="small"
                        label={field.label}
                        placeholder={field.placeholder}
                        type={field.type || 'text'}
                        value={config[field.key] || ''}
                        onChange={(e) => handleFieldChange(channelId, field.key, e.target.value)}
                      />
                    )}
                  </Box>
                ))}
              </Box>
            )}

            {/* Docs Link */}
            {channelDef.docsUrl && (
              <Box sx={{ mt: 2 }}>
                <Typography
                  variant="caption"
                  component="a"
                  href={channelDef.docsUrl}
                  target="_blank"
                  rel="noopener"
                  sx={{ color: channelDef.color, textDecoration: 'none' }}
                >
                  📖 查看接入文档 →
                </Typography>
              </Box>
            )}
          </CardContent>

          {/* Actions */}
          {isEnabled && channelDef.fields.length > 0 && (
            <CardActions sx={{ px: 2, pb: 2 }}>
              <Button
                variant="contained"
                size="small"
                onClick={() => handleSave(channelId)}
                disabled={saving === channelId}
                sx={{ bgcolor: channelDef.color }}
              >
                {saving === channelId ? '保存中...' : '保存配置'}
              </Button>
              <Button
                size="small"
                onClick={() => loadChannels()}
              >
                重置
              </Button>
            </CardActions>
          )}
        </Card>
      </Grid>
    )
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
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
          <Typography variant="h6">渠道接入</Typography>
          <Typography variant="caption" color="text.secondary">
            配置 QQ、飞书、Telegram 等聊天渠道
          </Typography>
        </Box>
        <Tooltip title="刷新">
          <IconButton onClick={loadChannels}>
            <IconRefresh size={20} />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ m: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ m: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Info */}
      <Box sx={{ m: 2, p: 2, bgcolor: '#e3f2fd', borderRadius: 1 }}>
        <Typography variant="body2" color="primary">
          💡 提示：配置渠道后，需要在对应平台设置 Webhook 地址才能接收消息。
          本地开发可使用 ngrok 等内网穿透工具。
        </Typography>
      </Box>

      {/* Channel Cards */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <Grid container spacing={2}>
          {channelConfigs.map(renderChannelCard)}
        </Grid>
      </Box>
    </Box>
  )
}

export default ChannelsPage
