from opendbc.can.parser import CANParser
from opendbc.car import Bus, structs
from opendbc.car.gwm.values import DBC
from opendbc.car.interfaces import CarStateBase
from opendbc.car.common.conversions import Conversions as CV

ButtonType = structs.CarState.ButtonEvent.Type
GearShifter = structs.CarState.GearShifter


class CarState(CarStateBase):
  def __init__(self, CP):
    super().__init__(CP)
    # TODO: Add CAN define when needed
    # can_define = CANDefine(DBC[CP.carFingerprint][Bus.pt])

    self.distance_button_prev = 0
    self.lka_button_prev = 0

  def update(self, can_parsers) -> structs.CarState:
    cp = can_parsers[Bus.pt]

    ret = structs.CarState()

    # Speed from available signals
    ret.vEgoRaw = cp.vl["SPEED"]["SPEED"] * CV.KPH_TO_MS  # Convert KPH to m/s
    ret.vEgo, ret.aEgo = self.update_speed_kf(ret.vEgoRaw)
    ret.standstill = ret.vEgoRaw < 0.01

    # Wheel speeds (convert from KPH to m/s)
    ret.wheelSpeeds = self.get_wheel_speeds(
      cp.vl["WHEEL_SPEEDS"]["FRONT_LEFT_WHEEL_SPEED"] * CV.KPH_TO_MS,
      cp.vl["WHEEL_SPEEDS"]["FRONT_RIGHT_WHEEL_SPEED"] * CV.KPH_TO_MS,
      cp.vl["WHEEL_SPEEDS"]["REAR_LEFT_WHEEL_SPEED"] * CV.KPH_TO_MS,
      cp.vl["WHEEL_SPEEDS"]["REAR_RIGHT_WHEEL_SPEED"] * CV.KPH_TO_MS,
    )

    # Gear from DRIVE_MODE signal
    gear = cp.vl["CAR_OVERALL_SIGNALS"]["DRIVE_MODE"]
    if gear == 0:
      ret.gearShifter = GearShifter.park
    elif gear == 1:
      ret.gearShifter = GearShifter.drive
    elif gear == 2:
      ret.gearShifter = GearShifter.neutral
    elif gear == 3:
      ret.gearShifter = GearShifter.reverse
    else:
      ret.gearShifter = GearShifter.unknown

    # Gas pedal
    ret.gas = cp.vl["CAR_OVERALL_SIGNALS2"]["GAS_POSITION"] / 100.0  # Convert to 0-1
    ret.gasPressed = cp.vl["CAR_OVERALL_SIGNALS"]["GAS_SIGNAL"] == 1

    # Brake
    ret.brakePressed = cp.vl["CAR_OVERALL_SIGNALS"]["BRAKE_SIGNAL"] == 1
    ret.brake = cp.vl["BRAKE"]["BRAKE_PRESSURE"] / 4184.0  # Normalize to 0-1 based on max pressure
    ret.parkingBrake = False  # TODO: Need to find this signal

    # Steering
    ret.steeringAngleDeg = cp.vl["STEER_AND_AP_STALK"]["STEERING_ANGLE"] * 0.05  # Apply scale factor
    ret.steeringTorque = cp.vl["STEER_AND_AP_STALK"]["STEERING_TORQUE"]
    ret.steeringPressed = abs(ret.steeringTorque) > 50  # Threshold for driver input
    ret.steerFaultTemporary = False  # TODO: Need EPS status signals
    ret.steerFaultPermanent = False

    # Turn signals
    ret.leftBlinker = cp.vl["LIGHTS"]["LEFT_TURN_SIGNAL"] == 1
    ret.rightBlinker = cp.vl["LIGHTS"]["RIGHT_TURN_SIGNAL"] == 1

    # Doors and seatbelt
    ret.doorOpen = cp.vl["DOOR_DRIVER"]["DOOR_DRIVER_OPEN"] == 1  # Only driver door available
    ret.seatbeltUnlatched = cp.vl["SEATBELT"]["SEAT_BELT_DRIVER_STATE"] == 1

    # Cruise state (basic implementation)
    ret.cruiseState.enabled = False  # TODO: Need cruise status signals
    ret.cruiseState.available = False
    ret.cruiseState.speed = cp.vl["ACC"]["ACC_SPEED_SELECTION"] * CV.KPH_TO_MS  # Convert to m/s
    ret.cruiseState.nonAdaptive = False

    # No button events for now
    ret.buttonEvents = []

    return ret

  @staticmethod
  def get_can_parsers(CP):
    messages = [
      # Using available messages from DBC
      ("CAR_OVERALL_SIGNALS", 50),      # For DRIVE_MODE, BRAKE_SIGNAL, GAS_SIGNAL
      ("CAR_OVERALL_SIGNALS2", 50),     # For GAS_POSITION
      ("SPEED", 50),                    # For vehicle speed
      ("WHEEL_SPEEDS", 80),             # For individual wheel speeds
      ("STEER_AND_AP_STALK", 50),       # For steering angle and torque
      ("BRAKE", 40),                    # For brake pressure
      ("LIGHTS", 10),                   # For turn signals
      ("DOOR_DRIVER", 5),               # For door status
      ("SEATBELT", 5),                  # For seatbelt status
      ("ACC", 10),                      # For ACC speed setting
    ]

    return {
      Bus.pt: CANParser(DBC[CP.carFingerprint][Bus.pt], messages, 0),
    }