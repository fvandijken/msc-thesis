from dataclasses import dataclass
import os

@dataclass
class Config:

    shipments_file_time_windows: str
    gap_percentage: float
    time_window_interval_in_minutes: int
    max_number_shipment_multiplication: int

