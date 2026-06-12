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
  Divider,
  Chip,
  CircularProgress,
} from '@mui/material'
import {
  IconEdit,
  IconEye,
  IconDeviceFloppy,
  IconRefresh,
} from '@tabler/icons-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function PromptsPage() {
  const [documents, setDocuments] = useState([])
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [content, setContent] = useState('')
  const [editMode, setEditMode] = useState(false)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  // 加载文档列表
  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      const response = await fetch('/api/prompts/')
      const data = await response.json()
      setDocuments(data.documents)
    } catch (error) {
      console.error('加载文档列表失败:', error)
    }
  }

  // 加载文档内容
  const loadDocument = async (name) => {
    setLoading(true)
    try {
      const response = await fetch(`/api/prompts/${name}`)
      const data = await response.json()
      setSelectedDoc(data)
      setContent(data.content)
      setEditMode(false)
    } catch (error) {
      console.error('加载文档失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 保存文档
  const saveDocument = async () => {
    if (!selectedDoc) return

    setSaving(true)
    try {
      const response = await fetch(`/api/prompts/${selectedDoc.name}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      })

      if (response.ok) {
        setEditMode(false)
        loadDocuments()
      }
    } catch (error) {
      console.error('保存文档失败:', error)
    } finally {
      setSaving(false)
    }
  }

  // 恢复备份
  const restoreDocument = async () => {
    if (!selectedDoc) return

    try {
      const response = await fetch(`/api/prompts/${selectedDoc.name}/restore`, {
        method: 'POST',
      })

      if (response.ok) {
        loadDocument(selectedDoc.name)
      }
    } catch (error) {
      console.error('恢复文档失败:', error)
    }
  }

  return (
    <Box sx={{ display: 'flex', height: '100%' }}>
      {/* 左侧文档列表 */}
      <Box
        sx={{
          width: 280,
          borderRight: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">系统提示词</Typography>
          <Typography variant="caption" color="text.secondary">
            {documents.length} 个文档
          </Typography>
        </Box>

        <List sx={{ flex: 1, overflow: 'auto' }}>
          {documents.map((doc) => (
            <ListItem key={doc.name} disablePadding>
              <ListItemButton
                selected={selectedDoc?.name === doc.name}
                onClick={() => loadDocument(doc.name)}
              >
                <ListItemText
                  primary={doc.name}
                  secondary={doc.filename}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>

      {/* 右侧内容区 */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {selectedDoc ? (
          <>
            {/* 工具栏 */}
            <Box
              sx={{
                p: 2,
                borderBottom: 1,
                borderColor: 'divider',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                bgcolor: 'background.paper',
              }}
            >
              <Box>
                <Typography variant="h6">{selectedDoc.name}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {selectedDoc.filename}
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  startIcon={editMode ? <IconEye /> : <IconEdit />}
                  onClick={() => setEditMode(!editMode)}
                  variant="outlined"
                  size="small"
                >
                  {editMode ? '预览' : '编辑'}
                </Button>

                {editMode && (
                  <Button
                    startIcon={<IconDeviceFloppy />}
                    onClick={saveDocument}
                    variant="contained"
                    size="small"
                    disabled={saving}
                  >
                    {saving ? '保存中...' : '保存'}
                  </Button>
                )}

                <Button
                  startIcon={<IconRefresh />}
                  onClick={restoreDocument}
                  variant="outlined"
                  size="small"
                  color="secondary"
                >
                  恢复备份
                </Button>
              </Box>
            </Box>

            {/* 内容区 */}
            <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                  <CircularProgress />
                </Box>
              ) : editMode ? (
                <TextField
                  fullWidth
                  multiline
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  sx={{
                    '& .MuiInputBase-root': {
                      fontFamily: '"JetBrains Mono", monospace',
                      fontSize: '14px',
                      lineHeight: 1.6,
                    },
                  }}
                />
              ) : (
                <Paper sx={{ p: 3, bgcolor: 'background.default' }}>
                  <Box className="markdown-body">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {content}
                    </ReactMarkdown>
                  </Box>
                </Paper>
              )}
            </Box>
          </>
        ) : (
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Typography variant="body1" color="text.secondary">
              选择一个文档查看
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  )
}

export default PromptsPage
