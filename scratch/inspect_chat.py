import livekit.agents.llm as lk_llm
import inspect

print(f"LLM.chat signature: {inspect.signature(lk_llm.LLM.chat)}")
