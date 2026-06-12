# PrivateClaw 安装故障排除

## 问题：代理错误 (ProxyError)

如果看到类似以下错误：
```
ProxyError('Cannot connect to proxy.', FileNotFoundError(2, 'No such file or directory'))
```

### 解决方案 1：运行修复脚本

```powershell
# 1. 先修复代理配置
.\fix_proxy.bat

# 2. 然后安装
.\install_no_proxy.bat
```

### 解决方案 2：手动禁用代理

在 PowerShell 中运行：

```powershell
# 清除代理环境变量
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:http_proxy = ""
$env:https_proxy = ""

# 然后安装
pip install langchain langchain-core langchain-openai langchain-anthropic langchain-community langgraph openai anthropic chromadb fastapi uvicorn websockets click rich pydantic pydantic-settings python-dotenv httpx PyYAML
```

### 解决方案 3：修改 pip 配置文件

创建或编辑 `%APPDATA%\pip\pip.ini`：

```ini
[global]
timeout = 60
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
```

### 解决方案 4：使用国内镜像源

如果在中国大陆，可以使用清华镜像：

```powershell
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple langchain langchain-core langchain-openai
```

或者创建 `%APPDATA%\pip\pip.ini`：

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

## 问题：Python 版本过低

PrivateClaw 需要 Python 3.11+，但你当前是 Python 3.8.6。

### 解决方案

1. 下载并安装 Python 3.11+：
   - 官网：https://www.python.org/downloads/
   - 推荐：Python 3.12 或 3.13

2. 安装时勾选 "Add Python to PATH"

3. 验证安装：
```powershell
python --version
# 应该显示 Python 3.11.x 或更高
```

## 问题：pip 不是内部或外部命令

### 解决方案

```powershell
# 使用 python -m pip 代替
python -m pip install langchain
```

## 快速测试安装

创建 `test_install.py`：

```python
import sys
print(f"Python version: {sys.version}")

try:
    import langchain
    print(f"LangChain version: {langchain.__version__}")
    print("✓ LangChain installed successfully!")
except ImportError as e:
    print(f"✗ LangChain not installed: {e}")

try:
    import fastapi
    print(f"FastAPI version: {fastapi.__version__}")
    print("✓ FastAPI installed successfully!")
except ImportError as e:
    print(f"✗ FastAPI not installed: {e}")
```

运行：
```powershell
python test_install.py
```

## 联系帮助

如果以上方法都无法解决问题，请提供以下信息：

1. Python 版本：`python --version`
2. pip 版本：`pip --version`
3. 操作系统版本
4. 完整的错误信息
