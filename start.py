import uvicorn
import threading

import sys,os
from processing import udpserver
from dotenv import load_dotenv
load_dotenv()


def run_udp_server():
    udpserver.start_server()


def start_server():
    # Start UDP server in a separate thread
    
    udp_thread = threading.Thread(target=run_udp_server, daemon=True)
    udp_thread.start()
    
    SERVER_IP = os.getenv("SERVER_IP", "127.0.0.1")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 4040))# Default port can be set here
    
    CERT_FILE=".\\cert\\cert.pem"
    KEY_FILE=".\\cert\\key.pem"
    
    # Start the FastAPI server using uvicorn
    try:
        uvicorn.run(
            "main:app",
            host=SERVER_IP,
            port=SERVER_PORT,
            log_level="debug",
            reload=False,  # Disable this if running in a thread-safe context is not guaranteed
            # ssl_certfile=CERT_FILE,
            # ssl_keyfile=KEY_FILE,
        )
    except KeyboardInterrupt:
        # Handle graceful shutdown on keyboard interrupt
        print("Server stopped by user.")
        print("Shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    start_server()