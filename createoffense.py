from DTO import OffenseCreationDTO
from database import engine
from sqlmodel import Session, select
from models import OffenseHistory, CameraInfo, CameraId
import camsocket# Assuming you have an Offense model defined in models.py
from datetime import timedelta
import base64

IMAGE_NOT_MANDEATORY = False  # Set to True if image is mandatory, False otherwise

def createOffense(offense: OffenseCreationDTO) -> None:
    
    """
    Create an offense in the system.

    Args:
        offense (dict): A dictionary containing offense details.

    Returns:
        dict: A dictionary containing the created offense details.
    """
    
    

    with Session(engine) as session:
        statement = select(OffenseHistory).where(OffenseHistory.vehicleNumber == offense.vehicleNumber)
        existing_offense = session.exec(statement).first()
        
        if existing_offense:
            o_time = offense.timestamp
            e_time = existing_offense.timestamp
            # Ensure both are either naive or both are aware
            if (o_time.tzinfo is not None) and (e_time.tzinfo is None):
                e_time = e_time.replace(tzinfo=o_time.tzinfo)
            elif (e_time.tzinfo is not None) and (o_time.tzinfo is None):
                o_time = o_time.replace(tzinfo=e_time.tzinfo)
            # If still mismatched, make both naive
            if (o_time.tzinfo is not None) != (e_time.tzinfo is not None):
                o_time = o_time.replace(tzinfo=None)
                e_time = e_time.replace(tzinfo=None)
            time_diff = o_time - e_time
            # Check if the offense happened within the last 1 hour
            if abs(time_diff.total_seconds()) < 3600:  # 3600 seconds = 1 hour
                raise ValueError(f"Offense for vehicle {offense.vehicleNumber} already recorded within the last hour.")
        
        # Continue with recording the new offense if no recent offense exists
        # session.add(offense)
        # session.commit()

    
    
    with Session(engine) as session:
        statement = select(CameraId).where(CameraId.mac == offense.mac)
        camera = session.exec(statement).first()
        if not camera:
            raise ValueError(f"Camera with ID {offense.mac} does not exist.")

    # Debug: print all available MACs in camsocket
    print(f"[DEBUG] Looking for camera MAC: {camera.mac}")
    print(f"[DEBUG] Available MACs in camsocket.uninitialized_cameras: {[cam.mac for cam in getattr(camsocket, 'uninitialized_cameras', [])]}")

    image = camsocket.getCameraData(camera.mac)
    if hasattr(image, "__await__"):  # If getCameraData is a coroutine, await it
        import asyncio
        image = asyncio.run(image)

    # Debug: print type and length of image before further processing
    print(f"[DEBUG] Image from camsocket.getCameraData({camera.mac}): {type(image)} {len(image) if image else 'None'} bytes")

    if not image:
        raise ValueError(f"No image data received from camera {camera.mac}. Cannot create offense without image.")

    # Decode base64 string to bytes before saving to DB
    try:
        image_bytes = base64.b64decode(image)
    except Exception as e:
        raise ValueError(f"Failed to decode base64 image: {e}")

    # Validate the offense type
    valid_offense_types = ["no-helmet", "road-parking"]
    if offense.offenseType not in valid_offense_types:
        raise ValueError(f"Invalid offense type: {offense.offenseType}. Must be one of {valid_offense_types}.")

    data = OffenseHistory(
        uid=camera.uid,
        vehicleNumber=offense.vehicleNumber,
        image=image_bytes,  # Save as bytes
        timestamp=offense.timestamp,
        offenseType=offense.offenseType,
        paid=False,  # Default value
        exempted=False  # Default value
    )
    
    # Simulate creating an offense
   
    # Here you would typically save the offense to a database
    with Session(engine) as session:
        session.add(data)
        session.commit()
        session.refresh(data)
    return None  # Return None or the created offense object if needed