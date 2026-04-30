from livekit.agents.voice import Agent
a = Agent(instructions="test")
print(f"Agent events: {a.list_events() if hasattr(a, 'list_events') else 'No list_events method'}")
# Or check __dict__ or dir
print(f"Agent attributes: {dir(a)}")
