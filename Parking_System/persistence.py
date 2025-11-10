# parking_system/persistence.py
import json
from typing import Optional
from .core import ParkingLot

def save_parking(file_path: str, parking_lot: ParkingLot) -> None:
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(parking_lot.to_dict(), f, indent=2)

def load_parking(file_path: str) -> Optional[ParkingLot]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return ParkingLot.from_dict(data)
    except FileNotFoundError:
        return None
