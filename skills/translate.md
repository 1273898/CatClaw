---
name: translate
type: custom
description: 文本翻译（中英互译）
triggers:
  - 翻译
  - 英文怎么说
  - 中文意思
  - translate
tags:
  - 翻译
  - 语言
confidence: 0.8
parameters:
  text: 需要翻译的文本
  target_lang: 目标语言（zh/en）
---

# Translate

中英文互译工具。

## 功能

- 将中文翻译成英文
- 将英文翻译成中文
- 自动检测源语言

## 使用示例

- "翻译 'hello world' 成中文"
- "'人工智能' 用英文怎么说"
- "翻译 今天天气真好 为英文"

## 代码

```python
from typing import Type, Optional
from pydantic import BaseModel, Field
from privateclaw.core.tools.base import PrivateClawTool
import json, urllib.request, urllib.parse


class TranslateInput(BaseModel):
    text: str = Field(description="Text to translate")
    target_lang: Optional[str] = Field(default="", description="Target language code")


class TranslateTool(PrivateClawTool):
    name: str = "translate"
    description: str = "Translate text between Chinese and English"
    category: str = "information"
    args_schema: Type[BaseModel] = TranslateInput

    def _run(self, text: str, target_lang: str = "") -> str:
        # 使用免费翻译 API（mymemory）
        try:
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair=auto|{target_lang or 'zh-CN'}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
                translated = data.get('responseData', {}).get('translatedText', '')
                return f"翻译结果: {translated}"
        except Exception as e:
            return f"翻译失败: {str(e)}"
```
