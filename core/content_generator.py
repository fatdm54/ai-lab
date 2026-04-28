"""
Content Generator - Topic → Multi-platform Content

Takes a topic and generates optimized content for:
- X/Twitter (short, punchy, with hashtags)
- Telegram (medium, detailed, with links)
- YouTube (long-form script, SEO optimized)

Usage:
    generator = ContentGenerator()
    content = generator.generate("free AI APIs for developers")
    print(content.x_thread)
    print(content.telegram_post)
    print(content.youtube_script)
"""

import json
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum

from .api_gateway import get_gateway, APIResponse


class ContentPillar(Enum):
    """Content categories"""
    AI_TOOLS = "ai_tools"
    INCOME_EXPERIMENT = "income_experiment"
    TUTORIAL = "tutorial"
    INDUSTRY_INSIGHT = "industry_insight"
    AUTOMATION = "automation"


@dataclass
class PlatformContent:
    """Content optimized for a specific platform"""
    platform: str
    content: str
    hashtags: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    media_hint: Optional[str] = None  # Suggestion for image/video


@dataclass
class MultiPlatformContent:
    """Complete content package for all platforms"""
    topic: str
    pillar: ContentPillar
    generated_at: str
    
    # Platform-specific content
    x_thread: Optional[PlatformContent] = None
    telegram_post: Optional[PlatformContent] = None
    youtube_script: Optional[PlatformContent] = None
    
    # Metadata
    estimated_tokens: int = 0
    generation_time_ms: float = 0


class ContentGenerator:
    """
    Generate multi-platform content from a topic
    
    Usage:
        generator = ContentGenerator()
        content = generator.generate("free AI APIs")
        
        # Post to X
        post_to_x(content.x_thread.content)
        
        # Post to Telegram
        post_to_telegram(content.telegram_post.content)
        
        # Save for YouTube
        save_script(content.youtube_script.content)
    """
    
    def __init__(self):
        self.gateway = get_gateway()
    
    def _generate_x_thread(self, topic: str, pillar: ContentPillar, context: str = "") -> PlatformContent:
        """Generate X/Twitter thread content"""
        
        pillar_descriptions = {
            ContentPillar.AI_TOOLS: "推荐一个AI工具，突出免费和实用性",
            ContentPillar.INCOME_EXPERIMENT: "分享AI赚钱实验的进展和数据",
            ContentPillar.TUTORIAL: "教用户如何用AI工具完成某个任务",
            ContentPillar.INDUSTRY_INSIGHT: "分享AI行业趋势和洞察",
            ContentPillar.AUTOMATION: "展示如何用AI自动化某个流程",
        }
        
        prompt = f"""你是一个专业的科技自媒体运营者。请为以下话题生成一条 X/Twitter 推文。

话题：{topic}
内容方向：{pillar_descriptions.get(pillar, "通用AI内容")}
{f"额外背景：{context}" if context else ""}

要求：
1. 中文为主，专业术语用英文
2. 280字符以内
3. 突出价值点（免费/赚钱/效率提升）
4. 加 3-5 个相关 hashtag
5. 如果有数据，用具体数字
6. 结尾加行动号召（关注/转发/试用）

输出格式：
[推文内容]

#hashtag1 #hashtag2 #hashtag3"""

        start_time = datetime.now()
        response = self.gateway.generate(prompt, max_tokens=500)
        generation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if not response.success:
            raise Exception(f"Failed to generate X content: {response.error}")
        
        # Parse hashtags from response
        lines = response.content.strip().split("\n")
        content_lines = []
        hashtags = []
        
        for line in lines:
            if line.startswith("#"):
                hashtags.extend(line.split())
            elif line.strip():
                content_lines.append(line)
        
        return PlatformContent(
            platform="x",
            content="\n".join(content_lines).strip(),
            hashtags=hashtags,
            media_hint="截图或数据图表"
        )
    
    def _generate_telegram_post(self, topic: str, pillar: ContentPillar, context: str = "") -> PlatformContent:
        """Generate Telegram channel post content"""
        
        prompt = f"""你是一个专业的科技内容创作者。请为以下话题生成一条 Telegram 频道帖子。

话题：{topic}
内容类型：{pillar.value}

要求：
1. 中文，专业但易懂
2. 300-500字
3. 结构清晰（标题 + 要点 + 总结）
4. 包含实用信息（链接、命令、步骤）
5. 适当的 emoji 点缀
6. 结尾引导加入频道/群组

输出格式：
📌 [标题]

[正文内容]

💡 总结：[一句话总结]

👉 [行动号召]"""

        start_time = datetime.now()
        response = self.gateway.generate(prompt, max_tokens=1500)
        generation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if not response.success:
            raise Exception(f"Failed to generate Telegram content: {response.error}")
        
        return PlatformContent(
            platform="telegram",
            content=response.content.strip(),
            hashtags=[],
            media_hint="截图或 GIF 演示"
        )
    
    def _generate_youtube_script(self, topic: str, pillar: ContentPillar, context: str = "") -> PlatformContent:
        """Generate YouTube video script"""
        
        prompt = f"""你是一个专业的 YouTube 科技频道创作者。请为以下话题生成一个视频脚本。

话题：{topic}
内容类型：{pillar.value}

要求：
1. 开头 hook（前10秒抓住注意力）
2. 问题引入（为什么观众需要看这个）
3. 解决方案（详细步骤）
4. 演示（如何操作）
5. 总结（关键要点）
6. 行动号召（订阅、点赞、评论）
7. 时长控制在 8-12 分钟（约 1200-1800 字）
8. 包含画面提示 [画面：xxx]
9. 包含字幕提示 [字幕：xxx]

输出格式：
[视频脚本，包含画面和字幕提示]"""

        start_time = datetime.now()
        response = self.gateway.generate(prompt, max_tokens=3000)
        generation_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if not response.success:
            raise Exception(f"Failed to generate YouTube content: {response.error}")
        
        return PlatformContent(
            platform="youtube",
            content=response.content.strip(),
            hashtags=[topic.lower().replace(" ", "_")],
            media_hint="屏幕录制 + 画中画"
        )
    
    def generate(
        self,
        topic: str,
        pillar: ContentPillar = ContentPillar.AI_TOOLS,
        platforms: Optional[List[str]] = None,
        context: str = ""
    ) -> MultiPlatformContent:
        """
        Generate content for multiple platforms
        
        Args:
            topic: The content topic
            pillar: Content category
            platforms: List of platforms to generate for (default: all)
            context: Additional context for content generation
        
        Returns:
            MultiPlatformContent with platform-specific content
        """
        if platforms is None:
            platforms = ["x", "telegram", "youtube"]
        
        start_time = datetime.now()
        
        content = MultiPlatformContent(
            topic=topic,
            pillar=pillar,
            generated_at=start_time.isoformat()
        )
        
        total_tokens = 0
        
        # Generate for each platform
        if "x" in platforms:
            content.x_thread = self._generate_x_thread(topic, pillar, context)
        
        if "telegram" in platforms:
            content.telegram_post = self._generate_telegram_post(topic, pillar, context)
        
        if "youtube" in platforms:
            content.youtube_script = self._generate_youtube_script(topic, pillar, context)
        
        # Calculate stats
        generation_time = (datetime.now() - start_time).total_seconds() * 1000
        content.generation_time_ms = generation_time
        content.estimated_tokens = total_tokens
        
        return content
    
    def generate_batch(
        self,
        topics: List[str],
        pillar: ContentPillar = ContentPillar.AI_TOOLS,
        platforms: Optional[List[str]] = None
    ) -> List[MultiPlatformContent]:
        """Generate content for multiple topics"""
        results = []
        for topic in topics:
            try:
                content = self.generate(topic, pillar, platforms)
                results.append(content)
                print(f"✅ Generated: {topic}")
            except Exception as e:
                print(f"❌ Failed: {topic} - {e}")
        return results


# Quick usage function
def quick_generate(topic: str, platform: str = "x") -> str:
    """Quick content generation - returns string"""
    generator = ContentGenerator()
    content = generator.generate(topic, platforms=[platform])
    
    if platform == "x" and content.x_thread:
        return content.x_thread.content
    elif platform == "telegram" and content.telegram_post:
        return content.telegram_post.content
    elif platform == "youtube" and content.youtube_script:
        return content.youtube_script.content
    
    return ""
