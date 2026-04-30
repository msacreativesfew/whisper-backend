try:
    from livekit.agents.pipeline import VoicePipelineAgent
    print("VoicePipelineAgent found in livekit.agents.pipeline")
except ImportError:
    print("VoicePipelineAgent not found in livekit.agents.pipeline")
