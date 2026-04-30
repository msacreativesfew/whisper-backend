import livekit.agents.tts as lk_tts
import inspect

# Get the module of the type hint
sig = inspect.signature(lk_tts.ChunkedStream.__init__)
conn_options_param = sig.parameters['conn_options']
print(f"conn_options type hint: {conn_options_param.annotation}")

# Try to find where it is imported from in lk_tts
for name, obj in inspect.getmembers(lk_tts):
    if name == 'APIConnectOptions':
        print(f"Found APIConnectOptions in lk_tts: {obj}")
        break
else:
    print("APIConnectOptions not found in lk_tts members")
