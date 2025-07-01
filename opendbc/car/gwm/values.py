from dataclasses import dataclass
from enum import IntFlag
from opendbc.car import PlatformConfig, CarSpecs, DbcDict, Bus
from opendbc.car.docs_definitions import CarDocs
from enum import StrEnum

class CAR(StrEnum):
  GWM_HAVAL_H6_PHEV_2024 = "GWM Haval H6 PHEV 2024"

@dataclass
class GwmCarControllerParams:
  STEER_MAX = 2048
  STEER_STEP = 2
  STEER_DELTA_UP = 15
  STEER_DELTA_DOWN = 25
  STEER_ERROR_MAX = 350
  ANGLE_RATE_LIMIT_UP = 10
  ANGLE_RATE_LIMIT_DOWN = 25
  ACCEL_MIN = -3.5
  ACCEL_MAX = 2.0

def dbc_dict(pt_dbc, cam_dbc) -> DbcDict:
  return {
    Bus.pt: pt_dbc,
    Bus.cam: cam_dbc,
  }

class GwmFlags(IntFlag):
  PHEV = 1

@dataclass
class GwmPlatformConfig(PlatformConfig):
  def init(self):
    pass

PLATFORMS = {
  CAR.GWM_HAVAL_H6_PHEV_2024: GwmPlatformConfig(
    [CarDocs("GWM Haval H6 PHEV 2024", "All")],
    CarSpecs(
        mass=2040,
        wheelbase=2.73,
        steerRatio=16.0,
        centerToFrontRatio=0.44,
        minSteerSpeed=0.0,
    ),
    dbc_dict('gwm_haval_h6_phev_2024', 'gwm_haval_h6_phev_2024'),
    flags=GwmFlags.PHEV,
  )
}

FINGERPRINTS = {
  CAR.GWM_HAVAL_H6_PHEV_2024: [{}],
}

DBC = {
  CAR.GWM_HAVAL_H6_PHEV_2024: dbc_dict('gwm_haval_h6_phev_2024', 'gwm_haval_h6_phev_2024'),
}

class MSG_ID:
  CAR_OVERALL_SIGNALS2 = 0x60
  IMPRECISE_SPEED_INFORMATION = 0x93
  STEER_AND_AP_STALK = 0xA1
  SPEED = 0x103
  AUTOPILOT = 0x12B
  CAR_OVERALL_SIGNALS = 0x12F
  BRAKE = 0x137

class Signals:
  STEERING_ANGLE = "STEERING_ANGLE"
  STEERING_TORQUE = "STEERING_TORQUE"
  AP_CANCEL_COMMAND = "AP_CANCEL_COMMAND"
  AP_ENABLE_COMMAND = "AP_ENABLE_COMMAND"
  AP_INCREASE_SPEED_COMMAND = "AP_INCREASE_SPEED_COMMAND"
  AP_DECREASE_SPEED_COMMAND = "AP_DECREASE_SPEED_COMMAND"
  AP_REDUCE_DISTANCE_COMMAND = "AP_REDUCE_DISTANCE_COMMAND"
  AP_INCREASE_DISTANCE_COMMAND = "AP_INCREASE_DISTANCE_COMMAND"
  VEHICLE_SPEED = "SPEED"
  BRAKE_PRESSURE = "BRAKE_PRESSURE"
  BRAKE_SIGNAL1 = "BRAKE_SIGNAL1"
  GAS_POSITION = "GAS_POSITION"
  ACC_GAS_POSITION = "ACC_GAS_POSITION"
  BRAKE_SIGNAL = "BRAKE_SIGNAL"
  DRIVE_MODE = "DRIVE_MODE"
  AP_STEERING_COMMAND = "AP_STEERING_UNDEFINED_SIGNAL1"
  AP_STATE = "AP_STATE"

class Buttons:
  NONE = 0
  RES_ACCEL = 1
  DECEL_SET = 2
  CANCEL = 3
  MAIN = 4

class CarGear:
  PARK = 'P'
  REVERSE = 'R'
  NEUTRAL = 'N'
  DRIVE = 'D'

class GwmChecksum:
  def __init__(self):
    self.gwm_crc_lookup = [
        0x00, 0x1D, 0x3A, 0x27, 0x74, 0x69, 0x4E, 0x53, 0xE8, 0xF5, 0xD2, 0xCF, 0x9C, 0x81, 0xA6, 0xBB,
        0xCD, 0xD0, 0xF7, 0xEA, 0xB9, 0xA4, 0x83, 0x9E, 0x25, 0x38, 0x1F, 0x02, 0x51, 0x4C, 0x6B, 0x76
    ]

  def gwm_checksum(self, msg, len_msg):
    checksum = 0xFF
    for i in range(len_msg):
        checksum = self.gwm_crc_lookup[(checksum ^ msg[i]) & 0x1F]
    return checksum