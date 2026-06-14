---
name: weather_query
type: web_search
description: 查询天气信息
triggers:
  - 天气
  - weather
  - 温度
  - 下雨
tags:
  - 天气
  - 查询
  - 生活
confidence: 0.7
parameters:
  city: 城市名称
---

# 天气查询

查询指定城市的天气信息。

## 功能

- 查询当前天气
- 显示温度、湿度、风力
- 支持国内外城市

## 使用示例

- "北京今天天气怎么样？"
- "上海会下雨吗？"

## 代码

```python
from typing import Type
from pydantic import BaseModel, Field
from privateclaw.core.tools.base import PrivateClawTool


class WeatherQueryInput(BaseModel):
    """Input for weather query."""
    city: str = Field(description="City name")


class WeatherQueryTool(PrivateClawTool):
    """Tool for weather query."""

    name: str = "weather_query"
    description: str = "Query weather information for a city"
    category: str = "search"
    args_schema: Type[BaseModel] = WeatherQueryInput

    def _run(self, city: str) -> str:
        """Query weather."""
        try:
            import httpx

            # Use wttr.in for simple weather
            url = f"https://wttr.in/{city}?format=3"
            response = httpx.get(url, timeout=5)

            if response.status_code == 200:
                return response.text.strip()
            else:
                return f"无法获取 {city} 的天气信息"
        except Exception as e:
            return f"查询天气失败: {str(e)}"

    async def _arun(self, city: str) -> str:
        """Query weather asynchronously."""
        return self._run(city)
```
