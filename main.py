#!/usr/bin/env python3
"""
AI Lab - AI赚钱实验室
用 AI 自动化赚钱的完整系统

Usage:
    python main.py --status          # Show system status
    python main.py --generate "topic"  # Generate content
    python main.py --test            # Run tests
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.api_gateway import get_gateway
from core.content_generator import ContentGenerator, ContentPillar


def show_status():
    """Show system status"""
    print("=" * 60)
    print("🤖 AI Lab Status")
    print("=" * 60)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # API Gateway status
    try:
        gateway = get_gateway()
        stats = gateway.get_usage_stats()
        
        print("📡 API Providers:")
        for provider, data in stats.items():
            status = "✅" if data["active_keys"] > 0 else "❌"
            print(f"  {status} {provider}: {data['active_keys']}/{data['total_keys']} keys active")
            print(f"     Requests: {data['total_requests']}, Tokens: {data['total_tokens']}")
        print()
        
    except Exception as e:
        print(f"❌ API Gateway error: {e}")
        print()
    
    # Project structure
    print("📁 Project Structure:")
    dirs = ["config", "core", "platforms", "scheduler", "templates", "data", "logs", "tests"]
    for d in dirs:
        path = Path(__file__).parent / d
        status = "✅" if path.exists() else "❌"
        print(f"  {status} {d}/")
    print()
    
    print("=" * 60)


def generate_content(topic: str, pillar: str = "ai_tools", platforms: str = "x"):
    """Generate content for a topic"""
    print(f"🎯 Generating content for: {topic}")
    print(f"📊 Pillar: {pillar}")
    print(f"📱 Platforms: {platforms}")
    print()
    
    try:
        generator = ContentGenerator()
        
        # Parse pillar
        pillar_enum = ContentPillar(pillar)
        
        # Parse platforms
        platform_list = [p.strip() for p in platforms.split(",")]
        
        # Generate
        content = generator.generate(
            topic=topic,
            pillar=pillar_enum,
            platforms=platform_list
        )
        
        # Display results
        if content.x_thread:
            print("🐦 X/Twitter:")
            print("-" * 40)
            print(content.x_thread.content)
            print(f"\nHashtags: {' '.join(content.x_thread.hashtags)}")
            print()
        
        if content.telegram_post:
            print("📱 Telegram:")
            print("-" * 40)
            print(content.telegram_post.content)
            print()
        
        if content.youtube_script:
            print("🎬 YouTube Script:")
            print("-" * 40)
            print(content.youtube_script.content[:500] + "...")
            print()
        
        print(f"⏱️  Generated in {content.generation_time_ms:.0f}ms")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def run_tests():
    """Run basic tests"""
    print("🧪 Running tests...")
    print()
    
    # Test API Gateway
    print("1. Testing API Gateway...")
    try:
        gateway = get_gateway()
        response = gateway.generate("Say 'test' in one word")
        if response.success:
            print(f"   ✅ Gateway OK: {response.content}")
        else:
            print(f"   ❌ Gateway failed: {response.error}")
    except Exception as e:
        print(f"   ❌ Gateway error: {e}")
    
    # Test Content Generator
    print("\n2. Testing Content Generator...")
    try:
        generator = ContentGenerator()
        content = generator.generate(
            topic="test topic",
            pillar=ContentPillar.AI_TOOLS,
            platforms=["x"]
        )
        if content.x_thread:
            print(f"   ✅ Content OK: {len(content.x_thread.content)} chars")
        else:
            print("   ❌ No content generated")
    except Exception as e:
        print(f"   ❌ Content error: {e}")
    
    print("\n✅ Tests complete")


def main():
    parser = argparse.ArgumentParser(
        description="AI Lab - AI赚钱实验室",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --status
  python main.py --generate "free AI APIs for developers"
  python main.py --generate "crypto trading bot" --pillar automation --platforms x,telegram
  python main.py --test
        """
    )
    
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--generate", "-g", type=str, help="Generate content for a topic")
    parser.add_argument("--pillar", "-p", type=str, default="ai_tools",
                       choices=["ai_tools", "income_experiment", "tutorial", "industry_insight", "automation"],
                       help="Content pillar")
    parser.add_argument("--platforms", "-P", type=str, default="x",
                       help="Comma-separated list of platforms (x,telegram,youtube)")
    parser.add_argument("--test", action="store_true", help="Run tests")
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    elif args.generate:
        generate_content(args.generate, args.pillar, args.platforms)
    elif args.test:
        run_tests()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
