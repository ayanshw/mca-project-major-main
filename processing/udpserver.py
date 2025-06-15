import socket
import threading
import time
from queue import Queue
import os
from collections import defaultdict
from dotenv import load_dotenv
import logging

import processing.image_processor as imp
from repo import cameraaccessrepo
import camsocket
from DTO import cameraSocketData
from database import engine
from sqlmodel import Session

# Setup logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

load_dotenv()

# Configuration
UDP_IP = os.getenv("UDP_IP", "127.0.0.1")
UDP_PORT = int(os.getenv("UDP_PORT", 8008))
MAX_PACKET_SIZE = int(os.getenv("MAX_PACKET_SIZE", 65507))
NUMBER_WORKERS = int(os.getenv("NUMBER_WORKERS", 4))
CHUNK_TIMEOUT = 10  # seconds

# Data Structures
image_queue = Queue()
image_chunks = defaultdict(lambda: defaultdict(dict))
CameraInitSet = set()
CameraUninitSet = set()

# ------------------------ Core Handlers ------------------------

def parse_packet(data: bytes):
    parts = data.split(b"\n", 3)
    if len(parts) < 4:
        raise ValueError("Invalid packet format")

    mac = parts[0].decode().strip().replace(":", "-").lower()
    image_id = parts[1].decode()
    chunk_info = parts[2].decode()
    chunk_data = parts[3]

    chunk_id, total_chunks = map(int, chunk_info.split("/"))
    return mac, image_id, chunk_id, total_chunks, chunk_data

def handle_full_image(full_image: bytes, mac: str):
    should_process = False

    # Skip if camera is uninitialized
    if mac in CameraUninitSet:
        logging.info(f"Camera {mac} marked as uninitialized. Skipping.")
        

    # Already initialized
    elif mac in CameraInitSet:
        logging.info(f"Camera {mac} already initialized.")
        should_process = True
    else:
        # First-time DB check
        with Session(engine) as session:
            if cameraaccessrepo.checkCameraInit(mac, session=session):
                logging.info(f"Camera {mac} found initialized in DB.")
                CameraInitSet.add(mac)
                should_process = True
            else:
                logging.info(f"Camera {mac} not initialized in DB. Skipping.")
                CameraUninitSet.add(mac)
                return

    # Add to WebSocket only if initialized
    camsocket.addCameraData(cameraSocketData(mac=mac, image=full_image))

    # Push to processing queue
    if should_process:
        image_queue.put((full_image, mac))

def udp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    logging.info(f"Listening on {UDP_IP}:{UDP_PORT}")

    while True:
        try:
            data, addr = sock.recvfrom(MAX_PACKET_SIZE)

            try:
                mac, image_id, chunk_id, total_chunks, chunk_data = parse_packet(data)

                chunks = image_chunks[mac].setdefault(image_id, {
                    "total": total_chunks,
                    "received": {},
                    "timestamp": time.time()
                })
                chunks["received"][chunk_id] = chunk_data

                # Reassemble image if all chunks received
                if len(chunks["received"]) == chunks["total"]:
                    ordered = [chunks["received"][i] for i in range(chunks["total"])]
                    full_image = b"".join(ordered)
                    logging.info(f"Complete image received from {mac} ({len(full_image)} bytes)")

                    handle_full_image(full_image, mac)
                    del image_chunks[mac][image_id]

            except Exception as e:
                logging.warning(f"Invalid packet: {e}")

        except Exception as e:
            logging.error(f"Socket error: {e}")

def worker_thread(worker_id: int):
    while True:
        item = image_queue.get()
        if item is None:
            break
        image_bytes, mac_address = item
        logging.info(f"[Worker-{worker_id}] Processing image from {mac_address}")
        imp.process_image(image_bytes, mac_address)

def cleanup_expired_chunks():
    while True:
        time.sleep(5)
        now = time.time()
        for mac in list(image_chunks.keys()):
            for image_id in list(image_chunks[mac].keys()):
                if now - image_chunks[mac][image_id]["timestamp"] > CHUNK_TIMEOUT:
                    logging.info(f"Expired incomplete image from {mac} (image_id: {image_id})")
                    del image_chunks[mac][image_id]

# ------------------------ Entry Point ------------------------

def start_server():
    for i in range(NUMBER_WORKERS):
        threading.Thread(target=worker_thread, args=(i,), daemon=True).start()

    threading.Thread(target=udp_server, daemon=True).start()
    threading.Thread(target=cleanup_expired_chunks, daemon=True).start()

    logging.info("Server started. Waiting for images...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down server...")
        for _ in range(NUMBER_WORKERS):
            image_queue.put(None)
        logging.info("Server shut down.")



def clear_camera_sets():
    CameraInitSet.clear()
    CameraUninitSet.clear()