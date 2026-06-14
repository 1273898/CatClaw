# SKILLS_SNAPSHOT.md - 技能快照

## 技能总览

### 已实现技能

| 技能名称 | 类别 | 状态 | 说明 |
|----------|------|------|------|
| terminal | 系统 | ✅ 完成 | 沙箱化终端执行 |
| fetch_url | 网络 | ✅ 完成 | 网页内容获取 |
| read_file | 文件 | ✅ 完成 | 文件读取 |
| file_write | 文件 | ✅ 完成 | 文件写入 |
| web_search | 搜索 | ✅ 完成 | 网络搜索 |
| calculator | 计算 | ✅ 完成 | 数学计算 |

### 计划中技能

| 技能名称 | 类别 | 优先级 | 说明 |
|----------|------|--------|------|
| ssh_connect | 远程 | ⭐⭐⭐ | SSH连接 |
| docker_ops | 容器 | ⭐⭐ | Docker操作 |
| git_ops | 版本控制 | ⭐⭐ | Git操作 |
| api_call | API | ⭐⭐ | HTTP API调用 |
| database | 数据库 | ⭐ | 数据库操作 |

## 技能详情

### 1. terminal - 终端执行

**功能**: 在沙箱中执行系统命令

**配置**:
```yaml
terminal:
  root_dir: "."
  timeout: 30
  blacklist:
    - "rm -rf"
    - "shutdown"
    - "chmod 777"
```

**使用示例**:
```python
result = await terminal.execute("ls -la")
```

**安全特性**:
- root_dir限制
- 危险命令黑名单
- 超时控制
- 输出限制

---

### 2. fetch_url - 网页获取

**功能**: 获取网页内容并清洗HTML

**配置**:
```yaml
fetch_url:
  timeout: 30
  max_size: 10MB
  clean_html: true
```

**使用示例**:
```python
content = await fetch_url.execute("https://example.com")
```

**特性**:
- HTML转Markdown
- 自动清洗噪音
- 编码检测
- 错误重试

---

### 3. read_file - 文件读取

**功能**: 安全读取本地文件

**配置**:
```yaml
read_file:
  root_dir: "."
  max_size: 10MB
  allowed_extensions:
    - ".txt"
    - ".md"
    - ".py"
    - ".json"
```

**使用示例**:
```python
content = await read_file.execute("path/to/file.txt")
```

**安全特性**:
- 路径遍历防护
- 文件大小限制
- 扩展名白名单
- 编码处理

---

### 4. web_search - 网络搜索

**功能**: 搜索互联网获取信息

**配置**:
```yaml
web_search:
  provider: "duckduckgo"
  max_results: 5
  safe_search: true
```

**使用示例**:
```python
results = await web_search.execute("Python教程")
```

**返回格式**:
```json
{
    "results": [
        {
            "title": "标题",
            "url": "链接",
            "snippet": "摘要"
        }
    ]
}
```

---

### 5. calculator - 计算器

**功能**: 安全执行数学计算

**支持函数**:
- 基础运算: +, -, *, /
- 三角函数: sin, cos, tan
- 对数函数: log, log10, log2
- 其他: sqrt, abs, round, pow

**使用示例**:
```python
result = await calculator.execute("sqrt(144) + 10")
```

**安全特性**:
- 沙箱执行
- 函数白名单
- 结果验证

---

### 6. file_write - 文件写入

**功能**: 安全写入本地文件

**配置**:
```yaml
file_write:
  root_dir: "."
  max_size: 10MB
  backup: true
```

**使用示例**:
```python
await file_write.execute(
    path="output.txt",
    content="Hello World"
)
```

**特性**:
- 自动备份
- 原子写入
- 权限检查
- 编码支持

## 技能注册

### 注册新技能

```python
from privateclaw.core.tools.registry import ToolRegistry

class MyTool(PrivateClawTool):
    name = "my_tool"
    description = "我的自定义工具"
    category = "custom"
    
    def _run(self, input: str) -> str:
        return f"结果: {input}"

# 注册工具
ToolRegistry.register(MyTool())
```

### 技能配置文件

```yaml
# skills/my_skill.yaml
name: my_skill
description: 我的技能
category: custom
parameters:
  input:
    type: string
    required: true
    description: 输入参数
```

## 技能管理

### 查看技能列表
```python
skills = ToolRegistry.get_all()
for skill in skills:
    print(f"{skill.name}: {skill.description}")
```

### 按类别获取技能
```python
system_skills = ToolRegistry.get_by_category("system")
```

### 技能元数据
```python
info = skill.get_metadata()
# {
#     "name": "terminal",
#     "description": "...",
#     "category": "system",
#     "requires_auth": true
# }
```

## 最佳实践

### 技能开发原则
1. **单一职责**: 每个技能只做一件事
2. **安全优先**: 默认拒绝危险操作
3. **错误处理**: 优雅处理异常情况
4. **文档完善**: 提供清晰的使用说明

### 技能测试
```python
# 单元测试
def test_terminal():
    result = terminal.execute("echo hello")
    assert result == "hello\n"

# 集成测试
async def test_workflow():
    # 测试技能组合
    pass
```

---

*这份文档记录了 CatClaw 当前可用的技能*
*最后更新: 2026-06-12*
