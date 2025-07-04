from opendbc.car import structs
from opendbc.can.parser import CANParser
from opendbc.car.gwm.values import DBC, Bus, MSG_ID, Signals, CarControllerParams
from opendbc.car.interfaces import CarStateBase
from common.conversions import Conversions as CV

GearShifter = structs.CarState.GearShifter

STEER_THRESHOLD = 1.0

class CarState(CarStateBase):
  def __init__(self, CP):
    super().__init__(CP)
    self.CP = CP
    self.can_define = DBC[CP.carFingerprint]["pt"]

  def update(self, can_parsers):
    cp = can_parsers[Bus.pt]
    # cp_cam = can_parsers[Bus.cam] # No messages from camera bus yet

    ret = structs.CarState.new_message()

    # vehicle speed
    ret.vEgo = cp.vl[MSG_ID.SPEED][Signals.VEHICLE_SPEED] * CV.KPH_TO_MS
    ret.vEgoRaw = ret.vEgo
    ret.standstill = ret.vEgo < 0.1

    # steering
    ret.steeringAngleDeg = cp.vl[MSG_ID.STEER_AND_AP_STALK][Signals.STEERING_ANGLE]
    ret.steeringTorque = cp.vl[MSG_ID.STEER_AND_AP_STALK][Signals.STEERING_TORQUE]
    ret.steeringPressed = abs(ret.steeringTorque) > STEER_THRESHOLD

    # brake
    ret.brakePressed = cp.vl[MSG_ID.CAR_OVERALL_SIGNALS2][Signals.BRAKE_SIGNAL] == 1
    ret.brake = cp.vl[MSG_ID.BRAKE][Signals.BRAKE_PRESSURE]

    # gas
    ret.gas = cp.vl[MSG_ID.CAR_OVERALL_SIGNALS2][Signals.GAS_POSITION] / 100.0
    ret.gasPressed = ret.gas > 1e-3

    # gear
    gear = cp.vl[MSG_ID.CAR_OVERALL_SIGNALS][Signals.DRIVE_MODE]
    if gear == 0:
      ret.gearShifter = GearShifter.park
    elif gear == 1:
      ret.gearShifter = GearShifter.drive
    else:
      ret.gearShifter = GearShifter.unknown

    # cruise state
    ret.cruiseState.enabled = cp.vl[MSG_ID.AUTOPILOT][Signals.AP_STATE] == 1
    # Note: AP_CRUISE_SPEED doesn't exist in the DBC, using a default value
    ret.cruiseState.speed = 0.0

    # blinkers - using the correct signal names from LIGHTS message
    ret.leftBlinker = cp.vl[MSG_ID.LIGHTS][Signals.LEFT_TURN_SIGNAL] == 1
    ret.rightBlinker = cp.vl[MSG_ID.LIGHTS][Signals.RIGHT_TURN_SIGNAL] == 1

    return ret

  @staticmethod
  def get_can_parsers(CP):
    return {
      Bus.pt: CANParser(DBC[CP.carFingerprint]["pt"], [
        ("STEER_AND_AP_STALK", 50),
        ("SPEED", 50),
        ("CAR_OVERALL_SIGNALS2", 50),
        ("BRAKE", 50),
        ("CAR_OVERALL_SIGNALS", 50),
        ("AUTOPILOT", 50),
        ("LIGHTS", 10),
      ], 0),
      Bus.cam: CANParser(DBC[CP.carFingerprint]["pt"], [], 0),  # No camera messages yet
    }
