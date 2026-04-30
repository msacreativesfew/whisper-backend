"""
Web tools — search, fetch pages, and global news briefings.
"""

import httpx
import xml.etree.ElementTree as ET
import asyncio  # Required for parallel execution
import re
from datetime import datetime

SEED_FEEDS = [
    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'https://www.cnbc.com/id/100727362/device/rss/rss.html',
    'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
    'https://www.aljazeera.com/xml/rss/all.xml'
]

FINANCE_SEED_FEEDS = [
    'https://www.cnbc.com/id/10000664/device/rss/rss.html',       # CNBC Finance
    'https://feeds.bloomberg.com/markets/news.rss',                # Bloomberg Markets
    'https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best',  # Reuters
    'https://feeds.marketwatch.com/marketwatch/topstories/',       # MarketWatch
    'https://rss.nytimes.com/services/xml/rss/nyt/Business.xml',  # NYT Business
]

async def fetch_and_parse_feed(client, url):
    """Helper function to handle a single feed request and parse its XML."""
    try:
        response = await client.get(url, headers={'User-Agent': 'Whisper-AI/1.0'}, timeout=5.0)
        if response.status_code != 200:
            return []

        root = ET.fromstring(response.content)
        # Extract source name from URL (e.g., 'BBC' or 'NYTIMES')
        source_name = url.split('.')[1].upper()
        
        feed_items = []
        # Get top 5 items per feed
        items = root.findall(".//item")[:5]
        for item in items:
            title = item.findtext("title")
            description = item.findtext("description")
            link = item.findtext("link")
            
            if description:
                description = re.sub('<[^<]+?>', '', description).strip()

            feed_items.append({
                "source": source_name,
                "title": title,
                "summary": description[:200] + "..." if description else "",
                "link": link
            })
        return feed_items
    except Exception:
        # If one feed fails, return an empty list so others can still succeed
        return []

def register(mcp):

    @mcp.tool()
    async def get_world_news() -> str:
        """
        Fetches the latest global headlines from major news outlets simultaneously.
        Use this when the user asks 'What's going on in the world?' or for recent events.
        """
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            # 1. Create a list of 'tasks' (one for each URL)
            tasks = [fetch_and_parse_feed(client, url) for url in SEED_FEEDS]
            
            # 2. Fire them all at once and wait for the results
            # results will be a list of lists: [[news from bbc], [news from nyt], ...]
            results_of_lists = await asyncio.gather(*tasks)
            
            # 3. Flatten the list of lists into a single list of articles
            all_articles = [item for sublist in results_of_lists for item in sublist]

        if not all_articles:
            return "The global news grid is unresponsive, sir. I'm unable to pull headlines."

        # 4. Format the final briefing
        report = ["### GLOBAL NEWS BRIEFING (LIVE)\n"]
        # Limit to top 12 items so the AI doesn't get overwhelmed
        for entry in all_articles[:12]:
            report.append(f"**[{entry['source']}]** {entry['title']}")
            report.append(f"{entry['summary']}")
            report.append(f"Link: {entry['link']}\n")

        return "\n".join(report)

    @mcp.tool()
    async def get_world_finance_news() -> str:
        """
        Fetches the latest finance and market headlines from major financial outlets simultaneously.
        Use this when the user asks about finance news, market updates, or economic developments.
        """

        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            tasks = [fetch_and_parse_feed(client, url) for url in FINANCE_SEED_FEEDS]
            results_of_lists = await asyncio.gather(*tasks)
            all_articles = [item for sublist in results_of_lists for item in sublist]

        if not all_articles:
            return "The financial feeds are unresponsive right now, sir. I can't pull market headlines."

        report = ["### FINANCE BRIEFING (LIVE)\n"]
        for entry in all_articles[:12]:
            report.append(f"**[{entry['source']}]** {entry['title']}")
            report.append(f"{entry['summary']}")
            report.append(f"Link: {entry['link']}\n")

        return "\n".join(report)

    @mcp.tool()
    async def search_web(query: str) -> str:
        """Search the web for a given query and return a summary of results."""
        return f"[stub] Search results for: {query}"

    @mcp.tool()
    async def search_youtube(query: str) -> str:
        """Search YouTube for a video and open it in the browser."""
        import webbrowser
        import urllib.parse
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        webbrowser.open(search_url)
        return f"Searching YouTube for '{query}' and opening results now, sir."

    @mcp.tool()
    async def get_weather_and_location() -> str:
        """
        Detects the user's location based on IP and fetches the current weather.
        Use this when the user asks about the weather, their location, or 'how's it looking outside'.
        """
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                # 1. Get Location via IP
                loc_res = await client.get("http://ip-api.com/json/")
                loc_data = loc_res.json()
                city = loc_data.get("city", "Unknown")
                lat = loc_data.get("lat")
                lon = loc_data.get("lon")
                
                # 2. Get Weather via Open-Meteo
                weather_res = await client.get(
                    f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                )
                weather_data = weather_res.json()
                temp = weather_data["current_weather"]["temperature"]
                wind = weather_data["current_weather"]["windspeed"]
                
                return f"You are currently in {city}. The temperature is {temp}°C with a wind speed of {wind} km/h. It's looking quite standard for this time of day."
            except Exception as e:
                return f"I'm having trouble accessing the local sensors, sir: {str(e)}"

    @mcp.tool()
    async def fetch_url(url: str) -> str:
        """Fetch the raw text content of a URL."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text[:4000]
    
    @mcp.tool()
    async def open_world_monitor() -> str:
        """
        Opens the World Monitor dashboard locally.
        Use this when the user wants a visual overview of global events or a real-time map.
        """
        import subprocess
        import sys
        import os
        
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            script_path = os.path.join(base_dir, "run_world_monitor.py")
            subprocess.Popen([sys.executable, script_path])
            return "Displaying the World Monitor on your primary screen now, sir."
        except Exception as e:
            return f"I'm unable to initialize the visual monitor: {str(e)}"

    @mcp.tool()
    async def open_finance_world_monitor() -> str:
        """
        Opens the Finance World Monitor dashboard (finance.worldmonitor.app) in the system's web browser.
        Use this when the user wants a visual overview of global financial markets and trends.
        """
        import webbrowser
        url = "https://finance.worldmonitor.app/"

        try:
            webbrowser.open(url)
            return "Displaying the Finance World Monitor on your primary screen now, sir."
        except Exception as e:
            return f"I'm unable to initialize the finance monitor: {str(e)}"
