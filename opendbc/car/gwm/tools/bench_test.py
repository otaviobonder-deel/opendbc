#!/usr/bin/env python3
"""
Bench test script for GWM Haval H6 PHEV 2024 interface.
This script tests the car interface with recorded CAN data.
"""

import os
import sys
import time
import argparse
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

# Add the parent directory to the path so we can import the car interface
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opendbc.can.parser import CANParser
from opendbc.can.packer import CANPacker
from opendbc.can.tests.test_packer_parser import can_list_to_can_capnp
from opendbc.can import can_define
from opendbc.car.gwm.interface import CarInterface
from opendbc.car.gwm.values import CAR, DBC, MSG_ID, Signals
from opendbc.car.gwm.carstate import CarState
from opendbc.car.gwm.carcontroller import CarController


def setup_can_parser() -> CANParser:
    """Set up the CAN parser with the GWM DBC file."""
    dbc_fp = DBC['gwm_haval_h6_phev_2024']['pt']
    return CANParser(dbc_fp, signals=None, checks=[])


def setup_can_packer() -> CANPacker:
    """Set up the CAN packer with the GWM DBC file."""
    dbc_fp = DBC['gwm_haval_h6_phev_2024']['pt']
    return CANPacker(dbc_fp)


def create_test_messages(packer: CANPacker) -> List[Tuple[int, int, bytes, int]]:
    """Create test CAN messages for bench testing."""
    messages = []
    
    # Add steering angle message (0 degrees)
    messages.append(packer.make_can_msg(
        "STEER_ANGLE_SENSOR",
        0,
        {"STEER_ANGLE": 0.0}
    ))
    
    # Add vehicle speed message (0 km/h)
    messages.append(packer.make_can_msg(
        "VEHICLE_SPEED",
        0,
        {"VEHICLE_SPEED": 0.0}
    ))
    
    # Add brake status message (not pressed)
    messages.append(packer.make_can_msg(
        "BRAKE_STATUS",
        0,
        {"BRAKE_PRESSED": 0, "BRAKE_PRESSURE": 0.0}
    ))
    
    # Add gas pedal message (0%)
    messages.append(packer.make_can_msg(
        "GAS_STATUS",
        0,
        {"GAS_PEDAL": 0.0}
    ))
    
    # Add gear status message (Park)
    messages.append(packer.make_can_msg(
        "GEAR_STATUS",
        0,
        {"GEAR_SHIFTER": 1}  # 1 = Park
    ))
    
    return messages


def bench_test_interface():
    """Run a bench test of the GWM interface."""
    print("Starting GWM Haval H6 PHEV 2024 bench test...")
    
    # Initialize the car interface
    car_model = CAR.HAVAL_H6_PHEV_2024
    CP = CarInterface.get_std_params(car_model)
    CI = CarInterface(CP, None, None)
    
    # Set up CAN parser and packer
    can_parser = setup_can_parser()
    can_packer = setup_can_packer()
    
    # Initialize car state
    CS = CarState(CP)
    
    # Initialize car controller
    CC = CarController(CP, CI.car_fingerprint)
    
    # Create test messages
    test_messages = create_test_messages(can_packer)
    
    print("\n=== Initial Car State ===")
    print(f"Steering Angle: {CS.angle_steers}°")
    print(f"Vehicle Speed: {CS.v_ego * 3.6:.1f} km/h")
    print(f"Brake Pressed: {CS.brake_pressed}")
    print(f"Gas Pedal: {CS.gas_pedal * 100:.1f}%")
    print(f"Gear: {CS.gear_shifter}")
    
    # Test 1: Parse CAN messages
    print("\n=== Testing CAN Message Parsing ===")
    can_parser.update_strings([msg[2] for msg in test_messages])
    CS.update(can_parser)
    
    print("\nAfter parsing test messages:")
    print(f"Steering Angle: {CS.angle_steers}°")
    print(f"Vehicle Speed: {CS.v_ego * 3.6:.1f} km/h")
    print(f"Brake Pressed: {CS.brake_pressed}")
    print(f"Gas Pedal: {CS.gas_pedal * 100:.1f}%")
    print(f"Gear: {CS.gear_shifter}")
    
    # Test 2: Generate control commands
    print("\n=== Testing Control Command Generation ===")
    
    # Create a test car control message
    class TestCarControl:
        def __init__(self):
            self.actuators = type('Actuators', (), {
                'steer': 0.1,  # 10% steering torque
                'steerAngle': 0.0,
                'accel': 0.5,  # 0.5 m/s^2 acceleration
                'brake': 0.0,
            })
            self.enabled = True
            self.active = True
            self.cruiseControl = type('CruiseControl', (), {'cancel': False})
            self.hudControl = type('HUDControl', (), {'setSpeed': 50, 'visualAlert': 'none'})
    
    # Generate control commands
    can_sends = CC.update(TestCarControl(), CS, 0)
    
    print(f"\nGenerated {len(can_sends)} CAN messages:")
    for addr, _, dat, _ in can_sends:
        print(f"  ID: 0x{addr:03X}, Data: {dat.hex()}")
    
    print("\nBench test completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bench test the GWM Haval H6 PHEV 2024 interface')
    args = parser.parse_args()
    
    try:
        bench_test_interface()
    except KeyboardInterrupt:
        print("\nBench test interrupted by user.")
    except Exception as e:
        print(f"\nError during bench test: {e}")
        raise
