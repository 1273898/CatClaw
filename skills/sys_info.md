---
name: sys_info
type: system
description: 获取系统资源使用情况（CPU、内存、磁盘）
triggers:
  - 系统信息
  - 资源使用
  - 电脑状态
  - 系统监控
tags:
  - 系统
  - 监控
  - 性能
confidence: 0.9
parameters: {}
---

# System Info

获取当前系统的 CPU、内存、磁盘使用情况。

## 功能

- CPU 使用率
- 内存使用情况
- 磁盘空间
- 运行时间

## 使用示例

- "看看系统资源"
- "电脑现在卡吗？"
- "磁盘空间还剩多少"

## 代码

```python
from typing import Type
from pydantic import BaseModel, Field
from privateclaw.core.tools.base import PrivateClawTool
import psutil


class SysInfoInput(BaseModel):
    pass


class SysInfoTool(PrivateClawTool):
    name: str = "sys_info"
    description: str = "Get system resource usage"
    category: str = "system"
    args_schema: Type[BaseModel] = SysInfoInput

    def _run(self, input: str = "") -> str:
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            boot = psutil.boot_time()
            import datetime
            uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(boot)
            return (
                f"🖥️ 系统状态:\n"
                f"CPU: {cpu}%\n"
                f"内存: {mem.used//1024**3}GB / {mem.total//1024**3}GB ({mem.percent}%)\n"
                f"磁盘: {disk.used//1024**3}GB / {disk.total//1024**3}GB ({disk.percent}%)\n"
                f"运行时间: {str(uptime).split('.')[0]}"
            )
        except Exception as e:
            return f"获取系统信息失败: {str(e)}"
```
