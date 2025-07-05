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
    can_define = CANDefine(DBC[CP.carFingerprint][Bus.pt])
    # Gear shifter values from DRIVE_MODE signal
    self.shifter_values = can_define.dv["CAR_OVERALL_SIGNALS"]["DRIVE_MODE"]

    self.distance_button_prev = 0
    self.lka_button_prev = 0

  def update(self, can_parsers) -> structs.CarState:
    cp = can_parsers[Bus.pt]

    ret = structs.CarState()

    # Speed
    ret.vEgoRaw = cp.vl["SPEED"]["SPEED"] * CV.KPH_TO_MS
    ret.vEgo, ret.aEgo = self.update_speed_kf(ret.vEgoRaw)
    ret.standstill = ret.vEgoRaw < 0.01

    # Wheel speeds
    ret.wheelSpeeds = structs.CarState.WheelSpeeds()
    ret.wheelSpeeds.fl = cp.vl["WHEEL_SPEEDS"]["FRONT_LEFT_WHEEL_SPEED"] * CV.KPH_TO_MS
    ret.wheelSpeeds.fr = cp.vl["WHEEL_SPEEDS"]["FRONT_RIGHT_WHEEL_SPEED"] * CV.KPH_TO_MS
    ret.wheelSpeeds.rl = cp.vl["WHEEL_SPEEDS"]["REAR_LEFT_WHEEL_SPEED"] * CV.KPH_TO_MS
    ret.wheelSpeeds.rr = cp.vl["WHEEL_SPEEDS"]["REAR_RIGHT_WHEEL_SPEED"] * CV.KPH_TO_MS

    # Gas pedal
    ret.gas = cp.vl["CAR_OVERALL_SIGNALS2"]["GAS_POSITION"] / 100.0
    ret.gasPressed = cp.vl["CAR_OVERALL_SIGNALS"]["GAS_SIGNAL"] == 1

    # Brake pedal
    ret.brakePressed = cp.vl["CAR_OVERALL_SIGNALS"]["BRAKE_SIGNAL"] == 1
    ret.brake = cp.vl["BRAKE"]["BRAKE_PRESSURE"] / 8191.0  # Normalize to 0-1
    # Use handbrake signals for parking brake
    ret.parkingBrake = cp.vl["BRAKE"]["REQ_REVIEW_HANDBRAKE_ENABLED"] == 1

    # Steering wheel
    ret.steeringAngleDeg = cp.vl["STEER_AND_AP_STALK"]["STEERING_ANGLE"]
    ret.steeringTorque = cp.vl["STEER_AND_AP_STALK"]["STEERING_TORQUE"]
    ret.steeringPressed = self.update_steering_pressed(abs(ret.steeringTorque) > 150, 5)
    ret.steerFaultTemporary = False  # TODO: Find signal
    ret.steerFaultPermanent = False  # TODO: Find signal

    # Cruise state from AUTOPILOT messages
    ret.cruiseState.enabled = cp.vl["AUTOPILOT"]["AP_STATE"] == 1
    ret.cruiseState.available = True  # TODO: Find proper signal
    ret.cruiseState.speed = cp.vl["ACC"]["ACC_SPEED_SELECTION"] * CV.KPH_TO_MS
    ret.cruiseState.nonAdaptive = False  # Assuming adaptive cruise

    # Gear
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

    # Turn signals
    ret.leftBlinker = cp.vl["LIGHTS"]["LEFT_TURN_SIGNAL"] == 1
    ret.rightBlinker = cp.vl["LIGHTS"]["RIGHT_TURN_SIGNAL"] == 1

    # Door and seatbelt
    ret.doorOpen = any([
      cp.vl["DOOR_DRIVER"]["DOOR_DRIVER_OPEN"],
      cp.vl["DOOR_DRIVER"]["DOOR_FRONT_RIGHT_OPEN"],
      cp.vl["DOOR_DRIVER"]["DOOR_REAR_LEFT_OPEN"],
      cp.vl["DOOR_DRIVER"]["DOOR_REAR_RIGHT_OPEN"],
    ])
    ret.seatbeltUnlatched = cp.vl["SEATBELT"]["SEAT_BELT_DRIVER_STATE"] == 1

    # Buttons on steering wheel / AP stalk
    distance_button = cp.vl["ACC"]["CAR_DISTANCE_SELECTION"]
    lka_button = cp.vl["STEER_AND_AP_STALK"]["AP_ENABLE_COMMAND"]

    ret.buttonEvents = [
      *create_button_events(distance_button != self.distance_button_prev, self.distance_button_prev != 0, {1: ButtonType.gapAdjustCruise}),
      *create_button_events(lka_button, self.lka_button_prev, {1: ButtonType.lkas}),
    ]

    self.distance_button_prev = distance_button
    self.lka_button_prev = lka_button

    return ret

  @staticmethod
  def get_can_parsers(CP):
    messages = [
      # sig_address, frequency
      ("CAR_OVERALL_SIGNALS2", 50),
      ("SPEED", 50),
      ("STEER_AND_AP_STALK", 50),
      ("CAR_OVERALL_SIGNALS", 50),
      ("BRAKE", 50),
      ("WHEEL_SPEEDS", 50),
      ("SPEED2", 50),
      ("LIGHTS", 10),
      ("DOOR_DRIVER", 5),
      ("SEATBELT", 5),
      ("AUTOPILOT", 50),
      ("ACC", 10),
    ]

    return {
      Bus.pt: CANParser(DBC[CP.carFingerprint][Bus.pt], messages, 0),  # Assuming bus 0 for now
    }