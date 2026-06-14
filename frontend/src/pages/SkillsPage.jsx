import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Chip,
  CircularProgress,
  Card,
  CardContent,
  CardActions,
  Button,
  Grid,
  Alert,
  LinearProgress,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material'
import {
  IconStar,
  IconRefresh,
  IconDownload,
  IconPlus,
  IconTool,
  IconBrain,
  IconCode,
  IconSearch,
  IconFile,
  IconTerminal,
} from '@tabler/icons-react'

// 旋转动画样式
const spinKeyframes = `
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.spin {
  animation: spin 1s linear infinite;
}
`
if (typeof document !== 'undefined') {
  const style = document.createElement('style')
  style.textContent = spinKeyframes
  document.head.appendChild(style)
}

const skillTypeIcons = {
  file_operation: IconFile,
  command_execution: IconTerminal,
  web_search: IconSearch,
  data_transformation: IconCode,
  code_generation: IconCode,
  custom: IconTool,
}

const skillTypeColors = {
  file_operation: '#4caf50',
  command_execution: '#ff9800',
  web_search: '#2196f3',
  data_transformation: '#9c27b0',
  code_generation: '#e91e63',
  custom: '#607d8b',
}

const sourceLabels = {
  learned: '自动学习',
  downloaded: '网络下载',
  manual: '手动创建',
}

function SkillsPage() {
  const [skills, setSkills] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [newSkill, setNewSkill] = useState({ name: '', description: '', code: '', tags: '', triggers: '' })
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      loadData()
    }, 30000) // 每30秒刷新一次

    return () => clearInterval(interval)
  }, [autoRefresh])

  const loadData = async () => {
    setLoading(true)
    await Promise.all([loadSkills(), loadStats()])
    setLoading(false)
  }

  const loadSkills = async () => {
    try {
      const response = await fetch('/api/skills/tools/list')
      const data = await response.json()
      setSkills(data.skills || [])
      setLastUpdate(new Date())
    } catch (err) {
      setError('加载技能失败')
      console.error(err)
    }
  }

  const loadStats = async () => {
    try {
      const response = await fetch('/api/skills/tools/stats')
      const data = await response.json()
      setStats(data.stats)
    } catch (err) {
      console.error('加载统计失败:', err)
    }
  }

  const handleRefresh = async () => {
    setLoading(true)
    await Promise.all([loadSkills(), loadStats()])
    setLoading(false)
  }

  const handleReload = async () => {
    try {
      await fetch('/api/skills/tools/reload', { method: 'POST' })
      await loadSkills()
      await loadStats()
    } catch (err) {
      setError('重新加载失败')
    }
  }

  const handleCreate = async () => {
    try {
      // Parse tags and triggers from comma-separated strings
      const skillData = {
        name: newSkill.name,
        description: newSkill.description,
        code: newSkill.code,
        tags: newSkill.tags ? newSkill.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
        triggers: newSkill.triggers ? newSkill.triggers.split(',').map(t => t.trim()).filter(Boolean) : [],
      }

      const response = await fetch('/api/skills/tools/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(skillData),
      })
      if (response.ok) {
        setCreateDialogOpen(false)
        setNewSkill({ name: '', description: '', code: '', tags: '', triggers: '' })
        await loadData()
      } else {
        setError('创建技能失败')
      }
    } catch (err) {
      setError('创建技能失败')
    }
  }

  const renderSkillCard = (skill) => {
    const IconComponent = skillTypeIcons[skill.type] || IconTool
    const typeColor = skillTypeColors[skill.type] || '#607d8b'

    return (
      <Grid item xs={12} sm={6} md={4} key={skill.id}>
        <Card
          sx={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            border: '1px solid',
            borderColor: 'divider',
            '&:hover': {
              borderColor: 'primary.main',
              boxShadow: 2,
            },
          }}
        >
          <CardContent sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <IconComponent size={20} color={typeColor} />
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                {skill.name}
              </Typography>
            </Box>

            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                mb: 2,
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {skill.description}
            </Typography>

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
              <Chip
                label={skill.type}
                size="small"
                sx={{
                  bgcolor: typeColor + '20',
                  color: typeColor,
                  fontSize: '0.7rem',
                }}
              />
              <Chip
                label={sourceLabels[skill.source] || skill.source}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.7rem' }}
              />
            </Box>

            {/* 触发词 */}
            {skill.trigger_patterns && skill.trigger_patterns.length > 0 && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  触发词:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {skill.trigger_patterns.slice(0, 3).map((pattern, i) => (
                    <Chip
                      key={i}
                      label={pattern}
                      size="small"
                      sx={{
                        fontSize: '0.65rem',
                        height: 20,
                        bgcolor: '#f5f5f5',
                      }}
                    />
                  ))}
                </Box>
              </Box>
            )}

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption" color="text.secondary">
                置信度:
              </Typography>
              <LinearProgress
                variant="determinate"
                value={skill.confidence * 100}
                sx={{
                  flex: 1,
                  height: 6,
                  borderRadius: 3,
                  bgcolor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: skill.confidence > 0.7 ? '#4caf50' : skill.confidence > 0.4 ? '#ff9800' : '#f44336',
                  },
                }}
              />
              <Typography variant="caption" color="text.secondary">
                {Math.round(skill.confidence * 100)}%
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                使用: {skill.usage_count} 次
              </Typography>
              {skill.success_count > 0 && (
                <Typography variant="caption" color="success.main">
                  成功: {skill.success_count} 次
                </Typography>
              )}
            </Box>

            {skill.tags && skill.tags.length > 0 && (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                {skill.tags.slice(0, 4).map((tag, i) => (
                  <Chip
                    key={i}
                    label={tag}
                    size="small"
                    variant="outlined"
                    sx={{ fontSize: '0.65rem', height: 20 }}
                  />
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
    )
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
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
          <Typography variant="h6" sx={{ fontWeight: 700, letterSpacing: 1 }}>SKILLS</Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="caption" color="text.secondary">
              CatClaw 技能库 · 从 skills/*.md 文件加载
            </Typography>
            {lastUpdate && (
              <Typography variant="caption" color="text.secondary">
                · 更新于 {lastUpdate.toLocaleTimeString()}
              </Typography>
            )}
          </Box>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            label={autoRefresh ? "自动刷新" : "手动模式"}
            size="small"
            color={autoRefresh ? "success" : "default"}
            onClick={() => setAutoRefresh(!autoRefresh)}
            sx={{ cursor: 'pointer' }}
          />
          <Tooltip title="从文件重新加载">
            <IconButton onClick={handleRefresh} disabled={loading}>
              <IconRefresh size={20} className={loading ? 'spin' : ''} />
            </IconButton>
          </Tooltip>
          <Tooltip title="创建新技能">
            <IconButton onClick={() => setCreateDialogOpen(true)}>
              <IconPlus size={20} />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Stats */}
      {stats && (
        <Box sx={{ p: 2, bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 3 }}>
            <Box>
              <Typography variant="h4" color="primary.main">
                {stats.total_skills}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                总技能数
              </Typography>
            </Box>
            <Box>
              <Typography variant="h4" color="success.main">
                {stats.active_skills}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                活跃技能
              </Typography>
            </Box>
            <Box>
              <Typography variant="h4" color="info.main">
                {Math.round(stats.average_confidence * 100)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                平均置信度
              </Typography>
            </Box>
          </Box>

          {stats.by_type && Object.keys(stats.by_type).length > 0 && (
            <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
              {Object.entries(stats.by_type).map(([type, count]) => (
                <Chip
                  key={type}
                  label={`${type}: ${count}`}
                  size="small"
                  sx={{
                    bgcolor: (skillTypeColors[type] || '#607d8b') + '20',
                    color: skillTypeColors[type] || '#607d8b',
                  }}
                />
              ))}
            </Box>
          )}
        </Box>
      )}

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ m: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Skills List */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {skills.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              gap: 2,
            }}
          >
            <IconStar size={48} color="#ccc" />
            <Typography variant="h6" color="text.secondary">
              还没有技能
            </Typography>
            <Typography variant="body2" color="text.secondary">
              CatClaw 会从你的使用中自动学习技能
            </Typography>
            <Button
              variant="outlined"
              startIcon={<IconPlus />}
              onClick={() => setCreateDialogOpen(true)}
            >
              手动创建技能
            </Button>
          </Box>
        ) : (
          <Grid container spacing={2}>
            {skills.map(renderSkillCard)}
          </Grid>
        )}
      </Box>

      {/* Create Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>创建新技能</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="技能名称"
            fullWidth
            variant="outlined"
            value={newSkill.name}
            onChange={(e) => setNewSkill({ ...newSkill, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="描述"
            fullWidth
            variant="outlined"
            value={newSkill.description}
            onChange={(e) => setNewSkill({ ...newSkill, description: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="触发词（逗号分隔）"
            fullWidth
            variant="outlined"
            value={newSkill.triggers}
            onChange={(e) => setNewSkill({ ...newSkill, triggers: e.target.value })}
            placeholder="提交代码, git commit, 保存更改"
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="标签（逗号分隔）"
            fullWidth
            variant="outlined"
            value={newSkill.tags}
            onChange={(e) => setNewSkill({ ...newSkill, tags: e.target.value })}
            placeholder="git, 版本控制, 代码管理"
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Python 代码（可选）"
            fullWidth
            multiline
            rows={10}
            variant="outlined"
            value={newSkill.code}
            onChange={(e) => setNewSkill({ ...newSkill, code: e.target.value })}
            placeholder={`class MyTool(PrivateClawTool):
    name = "my_tool"
    description = "My custom tool"

    def _run(self, input: str) -> str:
        return f"Result: {input}"`}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>取消</Button>
          <Button onClick={handleCreate} variant="contained">创建</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default SkillsPage
