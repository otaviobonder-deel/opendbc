from opendbc.can.can_define import CANDefine
from opendbc.can.parser import CANParser
from opendbc.car import Bus, create_button_events, structs
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.gwm.values import DBC
from opendbc.car.interfaces import CarStateBase

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

    # Basic functionality to get tests passing
    # TODO: Map actual signals from DBC file

    # Speed - using a placeholder for now
    ret.vEgoRaw = 0.0  # TODO: Map from SPEED message
    ret.vEgo, ret.aEgo = self.update_speed_kf(ret.vEgoRaw)
    ret.standstill = ret.vEgoRaw < 0.01

    # Gear - using the DRIVE_MODE signal we know exists
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

    # Basic defaults for required fields
    ret.gas = 0.0
    ret.gasPressed = False
    ret.brakePressed = False
    ret.brake = 0.0
    ret.parkingBrake = False
    ret.steeringAngleDeg = 0.0
    ret.steeringTorque = 0.0
    ret.steeringPressed = False
    ret.steerFaultTemporary = False
    ret.steerFaultPermanent = False
    ret.leftBlinker = False
    ret.rightBlinker = False
    ret.doorOpen = False
    ret.seatbeltUnlatched = False

    # Cruise state
    ret.cruiseState.enabled = False
    ret.cruiseState.available = False
    ret.cruiseState.speed = 0.0
    ret.cruiseState.nonAdaptive = False

    # No button events for now
    ret.buttonEvents = []

    return ret

  @staticmethod
  def get_can_parsers(CP):
    messages = [
      # Only using messages that we know exist and are being used
      ("CAR_OVERALL_SIGNALS", 50),  # For DRIVE_MODE signal
    ]

    return {
      Bus.pt: CANParser(DBC[CP.carFingerprint][Bus.pt], messages, 0),
    }