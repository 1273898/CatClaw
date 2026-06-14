import React, { useState, useRef, useEffect } from 'react'
import {
  Box,
  Typography,
  TextField,
  IconButton,
  Paper,
  Avatar,
  Chip,
  Alert,
  Snackbar,
  Collapse,
} from '@mui/material'
import { IconSend, IconRobot, IconUser, IconChevronDown, IconChevronRight, IconTool } from '@tabler/icons-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Highlight, themes } from 'prism-react-renderer'

// 角色映射
const mapRole = (role) => {
  if (role === 'human') return 'user'
  if (role === 'ai') return 'assistant'
  return role
}

// 解析消息中的工具调用
const parseToolCalls = (content) => {
  const parts = []
  let remaining = content

  // 循环查找工具调用
  while (true) {
    // 查找 🔧 Tool: 标记
    const toolMatch = remaining.match(/🔧 Tool: (\w+)/)
    if (!toolMatch) {
      // 没有更多工具调用，剩余部分作为文本
      if (remaining.trim()) {
        parts.push({ type: 'text', content: remaining })
      }
      break
    }

    const toolName = toolMatch[1]
    const toolStart = toolMatch.index

    // 添加工具调用之前的文本
    if (toolStart > 0) {
      const beforeText = remaining.slice(0, toolStart)
      if (beforeText.trim()) {
        parts.push({ type: 'text', content: beforeText })
      }
    }

    // 从工具调用开始位置继续解析
    const afterTool = remaining.slice(toolStart + toolMatch[0].length)

    // 查找 📥 Input: 标记
    const inputMatch = afterTool.match(/📥 Input:/)
    if (!inputMatch) {
      // 格式不完整，将整个工具调用作为文本
      parts.push({ type: 'text', content: remaining.slice(toolStart) })
      remaining = ''
      break
    }

    // 查找 📤 Output: 标记
    const afterInput = afterTool.slice(inputMatch.index + inputMatch[0].length)
    const outputMatch = afterInput.match(/📤 Output:/)

    let toolInput = ''
    let toolResult = ''

    if (outputMatch) {
      // 提取输入（📥 Input: 后到 📤 Output: 前）
      toolInput = afterInput.slice(0, outputMatch.index).trim()
      // 清理代码块标记
      toolInput = toolInput.replace(/^```(?:json)?\n?/, '').replace(/\n?```$/, '').trim()

      // 提取输出（📤 Output: 后到下一个 🔧 Tool 或文本结束）
      const afterOutput = afterInput.slice(outputMatch.index + outputMatch[0].length)
      const nextToolIdx = afterOutput.search(/🔧 Tool:/)

      if (nextToolIdx !== -1) {
        toolResult = afterOutput.slice(0, nextToolIdx).trim()
        remaining = afterOutput.slice(nextToolIdx)
      } else {
        toolResult = afterOutput.trim()
        remaining = ''
      }
      // 清理代码块标记
      toolResult = toolResult.replace(/^```(?:\w+)?\n?/, '').replace(/\n?```$/, '').trim()
    } else {
      // 没有输出标记，尝试提取剩余内容
      toolInput = afterInput.replace(/^```(?:json)?\n?/, '').replace(/\n?```$/, '').trim()
      toolResult = '(等待输出...)'
      remaining = ''
    }

    parts.push({
      type: 'tool',
      toolName: toolName,
      toolInput: toolInput,
      toolResult: toolResult
    })
  }

  // 如果没有找到工具调用，返回原始内容
  if (parts.length === 0) {
    parts.push({ type: 'text', content: content })
  }

  return parts
}

// 工具调用折叠组件
const ToolCallCollapse = ({ toolName, toolInput, toolResult, defaultExpanded = false }) => {
  const [expanded, setExpanded] = useState(defaultExpanded)

  return (
    <Box sx={{ my: 1, border: '1px solid #f8bbd0', borderRadius: '6px', overflow: 'hidden' }}>
      <Box
        onClick={() => setExpanded(!expanded)}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          p: 1,
          bgcolor: '#fce4ec',
          cursor: 'pointer',
          '&:hover': { bgcolor: '#f8bbd0' },
          borderBottom: expanded ? '1px solid #f8bbd0' : 'none',
        }}
      >
        {expanded ? <IconChevronDown size={16} /> : <IconChevronRight size={16} />}
        <IconTool size={16} color="#c2185b" />
        <Typography variant="caption" sx={{ fontWeight: 600, color: '#c2185b' }}>
          {toolName}
        </Typography>
        <Chip
          label={expanded ? "收起" : "展开"}
          size="small"
          variant="outlined"
          sx={{ ml: 'auto', height: 20, fontSize: '0.7rem', borderColor: '#f48fb1', color: '#c2185b' }}
        />
      </Box>
      <Collapse in={expanded}>
        <Box sx={{ p: 0 }}>
          {/* 输入部分 */}
          <Box sx={{ p: 1.5, bgcolor: '#fff0f5', borderBottom: '1px solid #f8bbd0' }}>
            <Typography variant="caption" sx={{ fontWeight: 600, color: '#c2185b', display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
              📥 输入
            </Typography>
            <pre style={{
              margin: 0,
              fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
              fontSize: '0.85em',
              color: '#880e4f',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
            }}>
              {toolInput}
            </pre>
          </Box>
          {/* 输出部分 */}
          <Box sx={{ p: 1.5, bgcolor: '#fce4ec' }}>
            <Typography variant="caption" sx={{ fontWeight: 600, color: '#c2185b', display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
              📤 输出
            </Typography>
            <pre style={{
              margin: 0,
              fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
              fontSize: '0.85em',
              color: '#880e4f',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
              maxHeight: '200px',
              overflow: 'auto',
            }}>
              {toolResult}
            </pre>
          </Box>
        </Box>
      </Collapse>
    </Box>
  )
}

// 自定义淡粉色主题
const pinkTheme = {
  plain: {
    color: '#5c2d82',  // 深紫色，更易读
    backgroundColor: '#fce4ec',
  },
  styles: [
    { types: ['comment', 'prolog', 'doctype', 'cdata'], style: { color: '#999988', fontStyle: 'italic' } },
    { types: ['namespace'], style: { opacity: 0.7 } },
    { types: ['string', 'attr-value'], style: { color: '#2e7d32' } },  // 绿色字符串
    { types: ['punctuation', 'operator'], style: { color: '#5c2d82' } },  // 紫色标点
    { types: ['entity', 'url', 'symbol', 'number', 'boolean', 'variable', 'constant', 'property', 'regex', 'inserted'], style: { color: '#1565c0' } },  // 蓝色数字/变量
    { types: ['atrule', 'keyword', 'attr-name', 'selector'], style: { color: '#c62828' } },  // 红色关键字
    { types: ['function', 'deleted', 'tag'], style: { color: '#6a1b9a' } },  // 紫色函数
    { types: ['function-variable'], style: { color: '#6a1b9a' } },
    { types: ['tag', 'selector', 'keyword'], style: { color: '#c62828' } },  // 红色tag
    { types: ['builtin', 'char', 'changed'], style: { color: '#d84315' } },  // 橙色内置
    { types: ['class-name'], style: { color: '#6a1b9a' } },  // 紫色类名
  ]
}

// 语法高亮代码块组件
const CodeBlock = ({ language, children }) => {
  return (
    <Highlight theme={pinkTheme} code={children} language={language || 'javascript'}>
      {({ tokens, getLineProps, getTokenProps }) => (
        <pre style={{
          margin: 0,
          padding: '16px',
          overflow: 'auto',
          fontSize: '0.85em',
          fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
          wordBreak: 'break-all',
          whiteSpace: 'pre-wrap',
          backgroundColor: '#fce4ec',
        }}>
          {tokens.map((line, i) => (
            <div key={i} {...getLineProps({ line })}>
              {line.map((token, key) => (
                <span key={key} {...getTokenProps({ token })} />
              ))}
            </div>
          ))}
        </pre>
      )}
    </Highlight>
  )
}

// 自定义渲染器
const renderers = {
  code({ node, inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || '')
    const codeString = String(children).replace(/\n$/, '')

    if (inline) {
      // 行内代码
      return (
        <code className={className} {...props}>
          {children}
        </code>
      )
    }

    // 判断是否是短代码（单行且少于50个字符）
    const isShortCode = !codeString.includes('\n') && codeString.length < 50

    if (isShortCode) {
      // 短代码使用行内代码样式，但保持块级显示
      return (
        <Box
          component="span"
          sx={{
            display: 'inline-block',
            bgcolor: '#fce4ec',
            px: 1,
            py: 0.25,
            borderRadius: '4px',
            fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
            fontSize: '0.9em',
            color: '#c2185b',
            border: '1px solid #f8bbd0',
            mx: 0.25,
          }}
        >
          {codeString}
        </Box>
      )
    }

    // 长代码块使用语法高亮
    return <CodeBlock language={match ? match[1] : 'text'}>{codeString}</CodeBlock>
  }
}

function ChatPage({ sessionId, onFirstMessage, onSessionChange }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const [currentSessionId, setCurrentSessionId] = useState(sessionId)
  const isNewSessionRef = useRef(false)
  const [promptUpdateNotification, setPromptUpdateNotification] = useState(null)

  // 同步外部 sessionId 变化
  useEffect(() => {
    setCurrentSessionId(sessionId)
  }, [sessionId])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // 加载会话历史消息
  useEffect(() => {
    // 如果是新创建的会话，跳过加载
    if (isNewSessionRef.current) {
      isNewSessionRef.current = false
      return
    }

    const loadHistory = async () => {
      try {
        const response = await fetch(`/api/sessions/${sessionId}/history`)
        const data = await response.json()
        if (data.history && data.history.length > 0) {
          // 映射角色名称
          const mappedHistory = data.history.map(msg => ({
            ...msg,
            role: mapRole(msg.role)
          }))
          setMessages(mappedHistory)
        } else {
          setMessages([])
        }
      } catch (error) {
        console.error('加载历史消息失败:', error)
        setMessages([])
      }
    }

    loadHistory()
  }, [sessionId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    let activeSessionId = currentSessionId

    // 如果是默认会话，调用 onFirstMessage 创建新会话
    if (activeSessionId === 'default' && onFirstMessage) {
      const newSessionId = await onFirstMessage()
      if (newSessionId) {
        activeSessionId = newSessionId
        // 标记为新会话，跳过历史加载
        isNewSessionRef.current = true
        setCurrentSessionId(newSessionId)
        if (onSessionChange) {
          onSessionChange(newSessionId)
        }
      }
    }

    const userMessage = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    const userInput = input
    setInput('')
    setLoading(true)

    // 检测是否定义了身份或人格
    const identityKeywords = ['你是', '你的名字', '你的身份', '你的角色', '你叫', 'you are', 'your name']
    const soulKeywords = ['你的性格', '你的风格', '你的语气', '你要', '你应该', '你需要', '你的个性', '你的人格', 'your personality', 'your style', 'you should']

    const inputLower = userInput.toLowerCase()
    const hasIdentityDefinition = identityKeywords.some(keyword => inputLower.includes(keyword))
    const hasSoulDefinition = soulKeywords.some(keyword => inputLower.includes(keyword))

    if (hasIdentityDefinition || hasSoulDefinition) {
      setPromptUpdateNotification('检测到身份/人格定义，正在更新提示词...')
    }

    // 添加一个空的 AI 消息用于流式更新
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }])

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userInput,
          session_id: activeSessionId,
        }),
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            if (data === '[DONE]') break

            try {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                setMessages((prev) => {
                  const newMessages = [...prev]
                  const lastIndex = newMessages.length - 1
                  if (newMessages[lastIndex].role === 'assistant') {
                    newMessages[lastIndex] = {
                      ...newMessages[lastIndex],
                      content: newMessages[lastIndex].content + parsed.content,
                    }
                  }
                  return newMessages
                })
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }
    } catch (error) {
      setMessages((prev) => {
        const newMessages = [...prev]
        const lastIndex = newMessages.length - 1
        if (newMessages[lastIndex].role === 'assistant') {
          newMessages[lastIndex] = {
            ...newMessages[lastIndex],
            content: '错误: ' + error.message,
          }
        }
        return newMessages
      })
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Typography variant="h6">聊天</Typography>
        <Typography variant="caption" color="text.secondary">
          会话: {sessionId}
        </Typography>
      </Box>

      {/* Messages */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        {messages.length === 0 ? (
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 2,
            }}
          >
            <Box
              component="img"
              src="/cats/橘猫.svg"
              alt="CatClaw"
              sx={{ width: 64, height: 64 }}
            />
            <Typography variant="h6" color="text.secondary">
              CatClaw
            </Typography>
            <Typography variant="body2" color="text.secondary">
              开始对话吧！
            </Typography>
          </Box>
        ) : (
          messages.map((msg, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                gap: 1,
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              }}
            >
              {msg.role === 'user' ? (
                <Box
                  component="img"
                  src="/cats/user-avatar.png"
                  sx={{ width: 40, height: 40 }}
                />
              ) : (
                <Box
                  component="img"
                  src="/cats/橘猫.svg"
                  sx={{ width: 40, height: 40 }}
                />
              )}
              <Paper
                sx={{
                  p: 2,
                  maxWidth: '70%',
                  bgcolor: msg.role === 'user' ? 'secondary.main' : 'background.paper',
                  borderRadius: 2,
                }}
              >
                {msg.role === 'user' ? (
                  <Typography variant="body1">{msg.content}</Typography>
                ) : (
                  <Box sx={{
                    '& p': { mb: 1, '&:last-child': { mb: 0 } },
                    '& ul, & ol': { pl: 2, mb: 1 },
                    '& li': { mb: 0.5 },
                    '& strong': { fontWeight: 600 },
                    '& em': { fontStyle: 'italic' },
                    // 行内代码 - 淡粉色风格
                    '& code': {
                      bgcolor: '#fce4ec',
                      px: 0.5,
                      py: 0.2,
                      borderRadius: '6px',
                      fontSize: '0.85em',
                      color: '#c2185b',
                      fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
                    },
                    // 代码块容器 - 淡粉色风格
                    '& pre': {
                      bgcolor: '#fce4ec',
                      p: 0,
                      borderRadius: '6px',
                      overflow: 'hidden',
                      border: '1px solid #f8bbd0',
                      mb: 1,
                      maxWidth: '100%',
                    },
                    '& h1, & h2, & h3, & h4, & h5, & h6': {
                      fontWeight: 600,
                      mb: 1,
                      mt: 1,
                      pb: 0.5,
                      borderBottom: '1px solid #f8bbd0',
                    },
                    '& h1': { fontSize: '1.5em' },
                    '& h2': { fontSize: '1.25em' },
                    '& h3': { fontSize: '1.1em' },
                    '& blockquote': {
                      borderLeft: 4,
                      borderColor: '#f48fb1',
                      pl: 1.5,
                      ml: 0,
                      mb: 1,
                      color: '#656d76',
                      bgcolor: '#fce4ec',
                      py: 0.5,
                      borderRadius: '0 6px 6px 0',
                    },
                    // 表格样式
                    '& table': {
                      borderCollapse: 'collapse',
                      width: '100%',
                      mb: 1,
                    },
                    '& th, & td': {
                      border: '1px solid #f8bbd0',
                      px: 1.5,
                      py: 0.75,
                      textAlign: 'left',
                    },
                    '& th': {
                      bgcolor: '#fce4ec',
                      fontWeight: 600,
                    },
                    '& tr:nth-of-type(even)': {
                      bgcolor: '#fff0f5',
                    },
                  }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5 }}>
                      <Box
                        component="img"
                        src="/cats/猫爪.svg"
                        sx={{
                          width: 20,
                          height: 20,
                          opacity: 0.7,
                          mt: 0.5,
                        }}
                      />
                      <Box sx={{ flex: 1, overflow: 'hidden' }}>
                        {(() => {
                          const parts = parseToolCalls(msg.content)
                          return parts.map((part, i) => {
                            if (part.type === 'tool') {
                              return (
                                <ToolCallCollapse
                                  key={i}
                                  toolName={part.toolName}
                                  toolInput={part.toolInput || ''}
                                  toolResult={part.toolResult}
                                />
                              )
                            }
                            return (
                              <ReactMarkdown
                                key={i}
                                remarkPlugins={[remarkGfm]}
                                components={renderers}
                              >
                                {part.content}
                              </ReactMarkdown>
                            )
                          })
                        })()}
                      </Box>
                      <Box
                        component="img"
                        src="/cats/猫爪.svg"
                        sx={{
                          width: 20,
                          height: 20,
                          opacity: 0.7,
                          mt: 0.5,
                        }}
                      />
                    </Box>
                  </Box>
                )}
              </Paper>
            </Box>
          ))
        )}
        {loading && messages[messages.length - 1]?.role !== 'assistant' && (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Box
              component="img"
              src="/cats/橘猫.svg"
              sx={{ width: 40, height: 40 }}
            />
            <Paper sx={{ p: 2, bgcolor: 'background.paper' }}>
              <Typography variant="body2" color="text.secondary">
                思考中...
              </Typography>
            </Paper>
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input */}
      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="输入消息... (Enter 发送，Shift+Enter 换行)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <IconButton
            color="primary"
            onClick={handleSend}
            disabled={!input.trim() || loading}
          >
            <IconSend />
          </IconButton>
        </Box>
      </Box>

      {/* 提示词更新通知 */}
      <Snackbar
        open={!!promptUpdateNotification}
        autoHideDuration={3000}
        onClose={() => setPromptUpdateNotification(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setPromptUpdateNotification(null)}
          severity="success"
          sx={{ width: '100%' }}
        >
          {promptUpdateNotification}
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default ChatPage
