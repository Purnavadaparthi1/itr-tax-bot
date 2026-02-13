"""
Share your ITR Tax Bot app with ngrok in 1 click!
Run this script to get a shareable public URL
"""

import subprocess
import time
from pyngrok import ngrok
import os
from dotenv import load_dotenv
import webbrowser

# Load environment
load_dotenv()

print("\n" + "="*80)
print("🚀 ITR TAX BOT - SHARE WITH NGROK")
print("="*80)

# Start backend server in background
print("\n📡 Starting backend server...")
backend_process = subprocess.Popen(['python', 'main.py'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)

# Wait for backend to start
time.sleep(3)

try:
    # Create ngrok tunnel
    print("🌐 Creating ngrok tunnel...")
    public_url = ngrok.connect(8001)
    
    # Extract the URL
    public_url_str = str(public_url).split("'")[1] if "'" in str(public_url) else str(public_url)
    
    print("\n" + "="*80)
    print("✅ SUCCESS! Your app is now shareable!")
    print("="*80)
    print(f"\n🔗 Public URL: {public_url_str}")
    print(f"\n📝 Share this link with others to test:")
    print(f"   {public_url_str}")
    print(f"\n💻 Local Testing:")
    print(f"   Frontend: http://localhost:5173")
    print(f"   Backend API: {public_url_str}")
    print("\n⏰ This link is active while this script is running!")
    print("   (Valid for 1+ days as long as you keep this running)")
    print("\n⚠️  Press CTRL+C to stop and close the tunnel\n")
    print("="*80 + "\n")
    
    # Keep running
    ngrok_process = ngrok.get_ngrok_process()
    ngrok_process.proc.wait()
    
except KeyboardInterrupt:
    print("\n\n🛑 Stopping ngrok tunnel...")
    ngrok.kill()
    backend_process.terminate()
    print("✅ Done! Tunnel closed.\n")
except Exception as e:
    print(f"\n❌ Error: {e}")
    backend_process.terminate()
    ngrok.kill()
