---
name: git_commit
type: command_execution
description: 自动提交代码到Git仓库
triggers:
  - 提交代码
  - git commit
  - 保存更改
  - commit
tags:
  - git
  - 版本控制
  - 代码管理
confidence: 0.8
parameters:
  message: 提交信息
---

# Git Commit

自动提交代码到Git仓库的技能。

## 功能

- 自动添加所有更改
- 使用指定的提交信息
- 显示提交结果

## 使用示例

- "帮我提交代码，信息是'修复了登录bug'"
- "git commit: 添加新功能"

## 代码

```python
from typing import Type
from pydantic import BaseModel, Field
from privateclaw.core.tools.base import PrivateClawTool


class GitCommitInput(BaseModel):
    """Input for git commit."""
    message: str = Field(description="Commit message")


class GitCommitTool(PrivateClawTool):
    """Tool for git commit."""

    name: str = "git_commit"
    description: str = "Commit changes to git repository"
    category: str = "system"
    args_schema: Type[BaseModel] = GitCommitInput

    def _run(self, message: str) -> str:
        """Execute git commit."""
        import subprocess
        try:
            # Add all changes
            subprocess.run(["git", "add", "."], capture_output=True, text=True)

            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return f"Successfully committed: {message}"
            else:
                return f"Commit failed: {result.stderr}"
        except Exception as e:
            return f"Error: {str(e)}"

    async def _arun(self, message: str) -> str:
        """Execute git commit asynchronously."""
        return self._run(message)
```
