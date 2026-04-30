"""
Simple test script to call Whisper MCP tools directly.
Shows how the backend works without needing API keys.
"""

import asyncio
import httpx
from whisper.tools import web, system, utils


async def main():
    print("=" * 60)
    print("WHISPER MCP SERVER - TOOL TESTING")
    print("=" * 60)
    
    # Create mock MCP object for testing (tools don't actually need it)
    class MockMCP:
        pass
    
    mcp = MockMCP()
    
    # Register tools
    web.register(mcp)
    system.register(mcp)
    utils.register(mcp)
    
    print("\n📡 Testing MCP Server Tools...\n")
    
    # Test 1: Get World News
    print("1️⃣  Testing: get_world_news()")
    print("-" * 60)
    try:
        news = await web.get_world_news()
        if isinstance(news, str):
            print(news[:500] + "...")
        else:
            print(news)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get System Info
    print("\n2️⃣  Testing: get_system_info()")
    print("-" * 60)
    try:
        sysinfo = system.get_system_info()
        print(sysinfo[:500])
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get Current Time
    print("\n3️⃣  Testing: get_current_time()")
    print("-" * 60)
    try:
        current_time = system.get_current_time()
        print(current_time)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Search Web
    print("\n4️⃣  Testing: search_web('latest AI news')")
    print("-" * 60)
    try:
        search_results = await web.search_web("latest AI news")
        print(search_results[:500] + "...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All tools tested!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
