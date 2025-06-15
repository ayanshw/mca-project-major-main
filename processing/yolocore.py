from ultralytics import YOLO
from dotenv import load_dotenv
import os
load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH", "D:\\DEV\\mca-project-major\\processing\\yolo_model")


def start_yolo():
    model_file = os.path.join(MODEL_PATH, "best.pt")
    # engine_file = os.path.join(MODEL_PATH, "best...engine")

    # # If the TensorRT engine file already exists, load and return it
    # if os.path.exists(engine_file):
    #     print("Loading existing TensorRT engine model...")
    #     return YOLO(engine_file)

    # # Otherwise, check if .pt model exists to export
    # if not os.path.exists(model_file):
    #     raise FileNotFoundError(f"Model file not found at {model_file}")

    # print("TensorRT engine file not found. Exporting from .pt model...")
    # model = YOLO(model_file)
    # model.export(format="engine")  # Export creates best.engine

    # # Confirm export succeeded and load the engine
    # if os.path.exists(engine_file):
    #     print("Export successful. Loading TensorRT model...")
    #     return YOLO(engine_file)
    # else:
    #     raise FileNotFoundError(f"Export failed: Engine file not found at {engine_file}")
    print("Loading YOLO model...")
    model = YOLO(model_file)
    return model

def start_anpr():
    model=YOLO(os.path.join(MODEL_PATH, "anpr.pt"))
    print("Loading ANPR model...")  
    return model