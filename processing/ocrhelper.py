import os
import re
import cv2
import torch
from PIL import Image
from datetime import datetime
import numpy as np


SAVE_IMAGE= True  # Set to False to disable saving images

def preprocess_plate_np(
    plate_img_np,
    denoise=True,
    sharpen=True,
    resize=True,
    threshold=True,
    invert=True
):
    """
    Flexible preprocessing for number plate image.
    Allows enabling/disabling steps like denoise, sharpen, etc.
    """
    if plate_img_np is None or not isinstance(plate_img_np, np.ndarray):
        raise ValueError("Input must be a valid NumPy array.")

    # Convert to grayscale
    img = cv2.cvtColor(plate_img_np, cv2.COLOR_BGR2GRAY)

    # Optional: Denoising
    if denoise:
        img = cv2.bilateralFilter(img, 11, 17, 17)

    # Optional: Sharpening
    if sharpen:
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        img = cv2.filter2D(img, -1, kernel)

    # Optional: Resize
    if resize:
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Optional: Thresholding
    if threshold:
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Optional: Invert (black text on white background)
    if invert:
        img = 255 - img

    return img



def detect_plate(vehicle_img_np, yolo_model):
    """
    Detects plate using YOLOv8 model. Returns cropped plate image (NumPy array) or None.
    """
    results = yolo_model(vehicle_img_np)[0]

    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        plate_crop = vehicle_img_np[y1:y2, x1:x2]

        if plate_crop.size > 0:
            return plate_crop

    return None


def save_plate_image(plate_img_np, save_dir, idx=0):
    """
    Save cropped plate image with timestamp for debugging.
    """
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    debug_path = os.path.join(save_dir, f"plate_{timestamp}_{idx}.jpg")
    cv2.imwrite(debug_path, plate_img_np)
    print(f"[DEBUG] Saved cropped plate to {debug_path}")
    return debug_path


def trocr_ocr(plate_img_np, processor, trocr_model):
    """
    Run TrOCR model on a NumPy image of the plate. Returns the cleaned OCR string.
    """
    try:
        plate_pil = Image.fromarray(cv2.cvtColor(plate_img_np, cv2.COLOR_BGR2RGB)).convert("RGB")
    except Exception as e:
        print("[ERROR] Failed to convert image to PIL:", e)
        return ""

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    trocr_model = trocr_model.to(device)

    pixel_values = processor(images=plate_pil, return_tensors="pt").pixel_values.to(device)

    with torch.no_grad():
        generated_ids = trocr_model.generate(pixel_values)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())
    print("Predicted Plate:", clean_text)
    return clean_text


def updated_ocr(processor, trocr_model, yolo_model, vehicle_crop, save_dir="./plate_debug", preprocess=False):
    """
    Full pipeline: YOLO plate detection → preprocessing → TrOCR → OCR result.
    """
    plate_crop = detect_plate(vehicle_crop, yolo_model)

    if plate_crop is None:
        print("[OCR] No plate detected in vehicle crop.")
        return ""

    if SAVE_IMAGE:
        save_plate_image(plate_crop, save_dir)

    if preprocess:
        processed_img = preprocess_plate_np(plate_crop, denoise=False, sharpen=True, resize=True, threshold=False, invert=False)


    return trocr_ocr(plate_crop, processor, trocr_model)
