---
name: find_file
type: system
description: 在当前项目目录中快速查找文件
triggers:
  - 查找文件
  - 搜索文件
  - 文件在哪
  - find file
tags:
  - 文件
  - 搜索
  - 系统
confidence: 0.9
parameters:
  pattern: 文件名模式（支持通配符）
---

# Find File

快速搜索项目目录下的文件。

## 功能

- 按名称匹配文件
- 支持通配符（如 *.py, *tool*）
- 显示文件路径和大小

## 使用示例

- "查找文件 database"
- "搜索所有 pdf 文件"
- "帮我找到 git_tool.py 在哪"

## 代码

```python
from typing import Type
import os, fnmatch
from pydantic import BaseModel, Field
from privateclaw.core.tools.base import PrivateClawTool


class FindFileInput(BaseModel):
    pattern: str = Field(description="File name pattern, e.g. *.md, *tool*")


class FindFileTool(PrivateClawTool):
    name: str = "find_file"
    description: str = "Search files in current project directory"
    category: str = "system"
    args_schema: Type[BaseModel] = FindFileInput

    def _run(self, pattern: str) -> str:
        root = os.getcwd()
        matches = []
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in fnmatch.filter(filenames, pattern):
                full = os.path.join(dirpath, filename)
                rel = os.path.relpath(full, root)
                size = os.path.getsize(full)
                matches.append(f"{rel} ({size} bytes)")
        if not matches:
            return f"没有找到匹配 `{pattern}` 的文件"
        return f"找到 {len(matches)} 个文件:\n" + "\n".join(matches[:20])
```
