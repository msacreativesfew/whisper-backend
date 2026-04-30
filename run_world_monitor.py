import os
import sys
import webview

def main():
    # Get the absolute path to the Vite dist directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "monitor-ui", "dist")
    html_file = os.path.join(dist_dir, "index.html")

    if not os.path.exists(html_file):
        print(f"Error: {html_file} does not exist. Please run 'npm run build' in monitor-ui.")
        sys.exit(1)

    # Convert to proper file URI
    html_uri = f"file://{html_file}"

    print(f"Starting World Monitor UI from: {html_uri}")

    # Create the window
    window = webview.create_window(
        'Whisper World Monitor',
        url=html_uri,
        width=1200,
        height=800,
        frameless=False,
        background_color='#020917'
    )

    # Start the app
    webview.start()

if __name__ == '__main__':
    main()
