from opendbc.car import structs
from opendbc.can.parser import CANParser
from opendbc.car.interfaces import CarStateBase
from opendbc.car.gwm.values import DBC, MSG_ID, Signals, CarGear, Bus
from opendbc.car.common.conversions import Conversions as CV

STEER_THRESHOLD = 1.0

class CarState(CarStateBase):
  def __init__(self, CP):
    super().__init__(CP)

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
      ret.gearShifter = CarGear.park
    elif gear == 1:
      ret.gearShifter = CarGear.drive
    elif gear == 2:
      ret.gearShifter = CarGear.neutral
    elif gear == 3:
      ret.gearShifter = CarGear.reverse
    else:
      ret.gearShifter = CarGear.unknown

    # buttons
    ret.leftBlinker = cp.vl[MSG_ID.LIGHTS][Signals.LEFT_TURN_SIGNAL] == 1
    ret.rightBlinker = cp.vl[MSG_ID.LIGHTS][Signals.RIGHT_TURN_SIGNAL] == 1

    # cruise state
    ret.cruiseState.available = cp.vl[MSG_ID.AUTOPILOT][Signals.AP_STATE] in [0, 1]
    ret.cruiseState.enabled = cp.vl[MSG_ID.AUTOPILOT][Signals.AP_STATE] == 1
    ret.cruiseState.speed = cp.vl[MSG_ID.ACC][Signals.ACC_SPEED_SELECTION] * CV.KPH_TO_MS



    return ret

  @staticmethod
  def get_can_parsers(CP):
    messages = [
      (MSG_ID.STEER_AND_AP_STALK, 50),
      (MSG_ID.SPEED, 50),
      (MSG_ID.BRAKE, 50),
      (MSG_ID.CAR_OVERALL_SIGNALS, 50),
      (MSG_ID.CAR_OVERALL_SIGNALS2, 50),
      (MSG_ID.AUTOPILOT, 50),
      (MSG_ID.LIGHTS, 10),
      (MSG_ID.ACC, 10),
    ]

    cam_messages = []

    can_parsers = {
      Bus.pt: CANParser(DBC[CP.carFingerprint][Bus.pt], messages, 0),
      Bus.cam: CANParser(DBC[CP.carFingerprint][Bus.cam], cam_messages, 2),
    }

    return can_parsers
