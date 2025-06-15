import cv2
import numpy as np
import time
import os
from processing.ocrhelper import updated_ocr
from processing.eventstore import EventStore
import processing.yolocore
# import easyocr
import createoffense
from DTO import OffenseCreationDTO
# from paddleocr import PaddleOCR
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from dotenv import load_dotenv
load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH", "yolo_model/best.pt")
SAVE_IMAGES = os.getenv("SAVE_IMAGES", "FALSE").lower() == "true"

model = processing.yolocore.start_yolo()
anpr_model = processing.yolocore.start_anpr() # Load the YOLO model for number plate detection
# reader = easyocr.Reader(['en'])
event_store = EventStore()

processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
models = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed")



# Create the instance
# ocr = PaddleOCR(use_angle_cls=True, lang='en')

def process_image(image_bytes, camera_id):
    try:
        # Decode the raw bytes into OpenCV image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            print("Failed to decode image from camera:", camera_id)
            return

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Run YOLOv8/v11 model
        results = model(img_rgb, conf=0.5)
        pred = results[0]
        orig_img = pred.orig_img
        height, width = orig_img.shape[:2]
        class_names = model.names

        detected_objects = []
        motorcycles = []
        helmets = []

        for box in pred.boxes:
            cls_id = int(box.cls.item())
            name = class_names[cls_id]
            print(f"Detected {name} with conf {box.conf.item():.2f}")
            coords = box.xyxy[0].tolist()
            x1, y1, x2, y2 = map(int, [
                max(0, coords[0]), max(0, coords[1]),
                min(width, coords[2]), min(height, coords[3])
            ])
            cv2.rectangle(orig_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{name} {box.conf.item():.2f}"
            cv2.putText(orig_img, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # # Save image
    # filename = f"images/{int(time.time()*1000)}.jpg"
    # cv2.imwrite(filename, orig_img)
    # print(f"Saved image with boxes: {filename}")

            if name in {"motorcycle", "car", "auto", "bus", "truck", "van"}:
                detected_objects.append((name, (x1, y1, x2, y2)))
                if name == "motorcycle":
                    motorcycles.append((x1, y1, x2, y2))
            elif name == "helmet":
                helmets.append((x1, y1, x2, y2))

        # Vehicle sightings
        for name, bbox in detected_objects:
            x1, y1, x2, y2 = bbox
            vehicle_crop = orig_img[y1:y2, x1:x2]
            plate_number = updated_ocr(processor, models, anpr_model, vehicle_crop)
            event_store.add_event({
                "vehicle_type": name,
                "vehicle_num": plate_number,
                "camera_id": camera_id,
                "offense": None
            })

        # Helmet check
        for bx1, by1, bx2, by2 in motorcycles:
            helmet_found = False
            for hx1, hy1, hx2, hy2 in helmets:
                inter_area = max(0, min(hx2, bx2) - max(hx1, bx1)) * max(0, min(hy2, by2) - max(hy1, by1))
                helmet_area = (hx2 - hx1) * (hy2 - hy1)
                if helmet_area > 0 and inter_area / helmet_area > 0.8:
                    helmet_found = True
                    break
            if not helmet_found:
                bike_crop = orig_img[by1:by2, bx1:bx2]
                plate_number = updated_ocr(processor, models, anpr_model, bike_crop)
                # event_store.add_event({
                #     "vehicle_type": "motorcycle",
                #     "vehicle_num": plate_number,
                #     "camera_id": camera_id,
                #     "offense": "No helmet"
                # })
                
                # Create offense
                createoffense.createOffense(OffenseCreationDTO(
                    vehicleNumber=plate_number,
                    timestamp=time.time(),
                    type="motorcycle",
                    mac=camera_id,
                    offenseType="no-helmet"
                ))

        # Save original image if configured
        if SAVE_IMAGES:
            os.makedirs("images", exist_ok=True)
            filename = f"images/{int(time.time()*1000)}.jpg"
            cv2.imwrite(filename, orig_img)
            print(f"Saved image: {filename}")

    except Exception as e:
        print(f"[ERROR] While processing image from {camera_id}: {e}")
