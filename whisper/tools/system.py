"""
System tools — time, environment info, shell commands, etc.
"""

import datetime
import platform
import subprocess

def register(mcp):

    @mcp.tool()
    def get_current_time() -> str:
        """Return the current date and time in ISO 8601 format."""
        return datetime.datetime.now().isoformat()

    @mcp.tool()
    def get_system_info() -> dict:
        """Return basic information about the host system."""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        }

    @mcp.tool()
    def open_application(app_name: str) -> str:
        """
        Open a standard Windows application by name.
        Supported: notepad, calc, chrome, edge, explorer
        """
        app_map = {
            "notepad": "notepad.exe",
            "calc": "calc.exe",
            "calculator": "calc.exe",
            "chrome": "start chrome",
            "edge": "start msedge",
            "explorer": "explorer.exe",
        }
        
        cmd = app_map.get(app_name.lower())
        if not cmd:
            return f"Application '{app_name}' is not supported or recognized."
            
        try:
            subprocess.Popen(cmd, shell=True)
            return f"Successfully opened {app_name}."
        except Exception as e:
            return f"Failed to open {app_name}: {e}"

    @mcp.tool()
    def control_volume(level: int) -> str:
        """
        Control the system volume.
        Args:
            level: The target volume level (0 to 100).
        """
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))

            # Clamp level
            level = max(0, min(100, level))
            
            # The volume range in pycaw is a scalar from 0.0 to 1.0.
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return f"Volume set to {level}%."
        except Exception as e:
            return f"Failed to set volume: {e}"
