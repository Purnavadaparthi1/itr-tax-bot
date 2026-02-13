"""
Simple ngrok tunnel for sharing your ITR Tax Bot
"""
from pyngrok import ngrok
import time

print("\n" + "="*80)
print("🚀 Creating public link for your ITR Tax Bot...")
print("="*80 + "\n")

try:
    # Connect frontend (port 3001)
    print("📡 Creating tunnel for Frontend (port 3001)...")
    frontend_url = ngrok.connect(3001)
    print(f"✅ Frontend: {frontend_url}\n")
    
    print("📡 Creating tunnel for Backend (port 8001)...")
    backend_url = ngrok.connect(8001)
    print(f"✅ Backend: {backend_url}\n")
    
    print("="*80)
    print("✅ YOUR APP IS NOW LIVE!")
    print("="*80)
    print(f"\n🔗 SHARE THIS LINK:")
    print(f"   {frontend_url}\n")
    print("📝 How to use:")
    print("   1. Send the link above to anyone")
    print("   2. They can open it in browser")
    print("   3. They can test your Tax Bot!\n")
    print("⏰ Valid while this script is running")
    print("   Press CTRL+C to stop\n")
    print("="*80 + "\n")
    
    # Keep running
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\n\n🛑 Stopping tunnels...")
    ngrok.kill()
    print("✅ Closed!\n")
except Exception as e:
    print(f"❌ Error: {e}")
    ngrok.kill()
