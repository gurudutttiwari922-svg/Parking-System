# parking_system/core.py
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, List
import math


@dataclass
class Vehicle:
    number: str
    vtype: str  # '2W', '4W', 'TR'
    entry_time: str  # ISO format


class ParkingLot:
    def __init__(self, capacities: Dict[str, int] = None, rates: Dict[str, float] = None):
        self.capacities = capacities or {'2W': 10, '4W': 20, 'TR': 5}
        self.rates = rates or {'2W': 5.0, '4W': 10.0, 'TR': 20.0}  # per hour
        self.slots: Dict[str, Dict[int, Optional[Vehicle]]] = {
            t: {i + 1: None for i in range(cap)} for t, cap in self.capacities.items()
        }

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def find_vehicle(self, number: str) -> Optional[Tuple[str, int]]:
        number = number.strip().upper()
        for t, sdict in self.slots.items():
            for slot_no, vehicle in sdict.items():
                if vehicle and vehicle.number == number:
                    return t, slot_no
        return None

    def park_vehicle(self, number: str, vtype: str) -> Tuple[bool, str]:
        number = number.strip().upper()
        vtype = vtype.strip().upper()
        if vtype not in self.slots:
            return False, f"Invalid vehicle type '{vtype}'. Use 2W, 4W, or TR."
        if self.find_vehicle(number):
            return False, f"Vehicle {number} already parked."
        for slot_no, vehicle in self.slots[vtype].items():
            if vehicle is None:
                v = Vehicle(number=number, vtype=vtype, entry_time=self._now_iso())
                self.slots[vtype][slot_no] = v
                return True, f"Parked {number} at {vtype} slot {slot_no}."
        return False, f"No available slots for type {vtype}."

    def remove_vehicle(self, identifier: str) -> Tuple[bool, str, Optional[float]]:
        import re
        id_clean = identifier.strip().upper()
        m = re.match(r'^(2W|4W|TR)[-:]?(\d+)$', id_clean)
        if m:
            t, s = m.group(1), int(m.group(2))
            if t in self.slots and s in self.slots[t]:
                vehicle = self.slots[t][s]
                if vehicle is None:
                    return False, f"Slot {t}:{s} is already empty.", None
                fee = self._calculate_fee(vehicle)
                self.slots[t][s] = None
                return True, f"Removed vehicle {vehicle.number} from {t}:{s}. Fee: ₹{fee:.2f}", fee
            return False, f"Invalid slot {t}:{s}.", None
        found = self.find_vehicle(id_clean)
        if not found:
            return False, f"Vehicle {id_clean} not found.", None
        t, s = found
        vehicle = self.slots[t][s]
        fee = self._calculate_fee(vehicle)
        self.slots[t][s] = None
        return True, f"Removed vehicle {vehicle.number} from {t}:{s}. Fee: ₹{fee:.2f}", fee

    def _calculate_fee(self, vehicle: Vehicle) -> float:
        entry = datetime.fromisoformat(vehicle.entry_time)
        now = datetime.now(timezone.utc)
        diff = now - entry
        hours = diff.total_seconds() / 3600.0
        hours_rounded = math.ceil(hours if hours > 0 else 0)
        rate = self.rates.get(vehicle.vtype, 0.0)
        return hours_rounded * rate

    def status_summary(self) -> Dict[str, Dict[str, int]]:
        summary = {}
        for t, sdict in self.slots.items():
            total = len(sdict)
            occupied = sum(1 for v in sdict.values() if v is not None)
            summary[t] = {'total': total, 'occupied': occupied, 'available': total - occupied}
        return summary

    def list_parked(self) -> List[Dict]:
        out = []
        for t, sdict in self.slots.items():
            for slot_no, vehicle in sdict.items():
                if vehicle:
                    out.append({'type': t, 'slot': slot_no, **asdict(vehicle)})
        return out

    def to_dict(self) -> Dict:
        d = {'capacities': self.capacities, 'rates': self.rates, 'slots': {}}
        for t, sdict in self.slots.items():
            d['slots'][t] = {str(k): asdict(v) if v else None for k, v in sdict.items()}
        return d

    @classmethod
    def from_dict(cls, data: Dict):
        pl = cls(capacities=data.get('capacities'), rates=data.get('rates'))
        slots = data.get('slots', {})
        for t, sdict in slots.items():
            if t not in pl.slots:
                continue
            for k, v in sdict.items():
                kint = int(k)
                pl.slots[t][kint] = None if v is None else Vehicle(**v)
        return pl
