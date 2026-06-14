import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Box } from '@mui/material'

// 动作配置
const ACTIONS = {
  walkleft: { weight: 1, frames: 12, speed: -0.5 },
  walkright: { weight: 1, frames: 12, speed: 0.5 },
  fish: { weight: 1, frames: 12, speed: 0 },
  sleep: { weight: 1, frames: 12, speed: 0 },
  kiss: { weight: 1, frames: 12, speed: 0 },
  stand: { weight: 1, frames: 12, speed: 0 },
}

function DesktopPet() {
  const [position, setPosition] = useState({ x: 50, y: typeof window !== 'undefined' ? window.innerHeight - 150 : 50 })
  const [action, setAction] = useState('stand')
  const [frameIndex, setFrameIndex] = useState(0)
  const [isDragging, setIsDragging] = useState(false)

  const petRef = useRef(null)
  const dragOffset = useRef({ x: 0, y: 0 })
  const actionTimer = useRef(null)
  const animationRef = useRef(null)

  // 根据权重随机选择动作
  const randomAction = useCallback(() => {
    const actions = Object.entries(ACTIONS)
    const totalWeight = actions.reduce((sum, [, config]) => sum + config.weight, 0)
    let random = Math.random() * totalWeight

    for (const [name, config] of actions) {
      if (random <= config.weight) {
        return name
      }
      random -= config.weight
    }
    return 'stand'
  }, [])

  // 获取当前帧的图片路径
  const getFrameSrc = useCallback((actionName, index) => {
    const frameNum = (index % 12) + 1
    if (actionName === 'walkleft') return `/pet/walkleft${frameNum}.png`
    if (actionName === 'walkright') return `/pet/walkright${frameNum}.png`
    if (actionName === 'fish') return `/pet/fish${frameNum}.png`
    if (actionName === 'sleep') return `/pet/sleep${frameNum}.png`
    if (actionName === 'kiss') return `/pet/kiss${frameNum}.png`
    if (actionName === 'stand') return `/pet/stand${frameNum}.png`
    return `/pet/stand1.png`
  }, [])

  // 更新宠物位置
  const updatePosition = useCallback((currentAction) => {
    const config = ACTIONS[currentAction]
    if (!config || config.speed === 0) return

    setPosition(prev => {
      let newX = prev.x + config.speed

      // 边界检测
      if (newX < 0) {
        setAction('walkright')
        newX = 0
      } else if (newX > window.innerWidth - 100) {
        setAction('walkleft')
        newX = window.innerWidth - 100
      }

      return { ...prev, x: newX }
    })
  }, [])

  // 动画循环
  useEffect(() => {
    let lastTime = 0
    const FPS = 10
    const frameInterval = 1000 / FPS

    const animate = (timestamp) => {
      if (timestamp - lastTime >= frameInterval) {
        lastTime = timestamp
        setFrameIndex(prev => prev + 1)
        updatePosition(action)
      }
      animationRef.current = requestAnimationFrame(animate)
    }

    animationRef.current = requestAnimationFrame(animate)

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [action, updatePosition])

  // 随机切换动作
  useEffect(() => {
    if (isDragging) return

    actionTimer.current = setInterval(() => {
      setAction(randomAction())
      setFrameIndex(0)
    }, 3000)

    return () => {
      if (actionTimer.current) {
        clearInterval(actionTimer.current)
      }
    }
  }, [isDragging, randomAction])

  // 鼠标按下
  const handleMouseDown = useCallback((e) => {
    e.preventDefault()
    setIsDragging(true)
    setAction('drag')
    setFrameIndex(0)

    if (petRef.current) {
      const rect = petRef.current.getBoundingClientRect()
      dragOffset.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      }
    }

    if (actionTimer.current) {
      clearInterval(actionTimer.current)
    }
  }, [])

  // 鼠标移动
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging) return

      const newX = e.clientX - dragOffset.current.x
      const newY = e.clientY - dragOffset.current.y

      setPosition({ x: newX, y: newY })
    }

    const handleMouseUp = () => {
      if (!isDragging) return

      setIsDragging(false)
      setAction('stand')
      setFrameIndex(0)

      // 边界检测
      setPosition(prev => {
        let { x, y } = prev
        if (x < 0) x = 50
        if (x > window.innerWidth - 100) x = window.innerWidth - 150
        if (y < 0) y = 50
        if (y > window.innerHeight - 100) y = window.innerHeight - 150
        return { x, y }
      })
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging])

  const currentSrc = isDragging ? `/pet/drag${(frameIndex % 12) + 1}.png` : getFrameSrc(action, frameIndex)

  return (
    <Box
      ref={petRef}
      sx={{
        position: 'fixed',
        left: position.x,
        top: position.y,
        width: 100,
        height: 100,
        zIndex: 9999,
        cursor: isDragging ? 'grabbing' : 'grab',
        userSelect: 'none',
      }}
      onMouseDown={handleMouseDown}
    >
      <Box
        component="img"
        src={currentSrc}
        alt="Desktop Pet"
        sx={{
          width: 90,
          height: 90,
          pointerEvents: 'none',
          userSelect: 'none',
        }}
      />
    </Box>
  )
}

export default DesktopPet
