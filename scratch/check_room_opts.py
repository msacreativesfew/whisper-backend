from livekit.agents import room_io
import inspect

print(f"RoomOptions: {inspect.signature(room_io.RoomOptions.__init__)}")
print(f"RoomOutputOptions: {inspect.signature(room_io.RoomOutputOptions.__init__)}")
