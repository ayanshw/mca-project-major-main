import os, threading, time, json
from dotenv import load_dotenv
import createoffense
from DTO import OffenseCreationDTO

load_dotenv()

EVENT_EXPIRY_SECONDS = int(os.getenv("EVENT_EXPIRY_SECONDS", 60)) 
OCCURRENCE_THRESHOLD = int(os.getenv("OCCURRENCE_THRESHOLD", 30))

class EventStore:
    def __init__(self):
        self.store = []
        self.lock = threading.Lock()

    def add_event(self, event):
        if not event.get("vehicle_num"):  # Ignore if vehicle_num is empty or not provided
            return

        with self.lock:
            now = time.time()

            # Remove old camera timestamps within each item
            for item in self.store:
                item["cameras"] = [cam for cam in item["cameras"] if now - cam["time"] <= EVENT_EXPIRY_SECONDS]
                item["occurrences"] = len(item["cameras"])

            # Remove completely expired items
            self.store = [item for item in self.store if item["occurrences"] > 0]

            # Find if the vehicle already exists
            for item in self.store:
                if item["vehicle_num"] == event["vehicle_num"]:
                    item["cameras"].append({"id": event["camera_id"], "time": now})
                    item["occurrences"] = len(item["cameras"])
                    break
            else:
                # New entry
                self.store.append({
                    "vehicle_num": event["vehicle_num"],
                    "vehicle_type": event.get("vehicle_type"),
                    "occurrences": 1,
                    "cameras": [{"id": event["camera_id"], "time": now}]
                })

            # Separate removal pass
            to_remove = []
            for item in self.store:
                if item["occurrences"] >= OCCURRENCE_THRESHOLD:
                    print(f"Offense detected for vehicle {item['vehicle_num']} with {item['occurrences']} occurrences.")
                    vehicle_num = item["vehicle_num"]
                    if not vehicle_num:
                        print("Vehicle number is empty, skipping offense creation.")
                        continue
                    if not item["cameras"]:
                        print(f"No cameras found for vehicle {vehicle_num}, skipping offense creation.")
                        continue
                    createof(vehicle_num, item["cameras"][0]["id"])
                    to_remove.append(item)

            for item in to_remove:
                self.store.remove(item)
                
def createof(vehicle_num, camera_id):
    """
    Create an offense record for a vehicle.
    This function is a placeholder and should be replaced with actual DB logic.
    """
    print(f"Creating offense for vehicle {vehicle_num} at camera {camera_id}")
    # For now, we just print it
    return createoffense.createOffense(OffenseCreationDTO(
        vehicleNumber=vehicle_num,
        timestamp=time.time(),
        type="motorcycle",
        mac=camera_id,
        offenseType="road-parking"
    ))
