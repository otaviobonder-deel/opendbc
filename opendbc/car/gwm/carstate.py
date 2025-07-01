from cereal import car
from opendbc.can.parser import CANParser
from opendbc.can.can_define import CANDefine
from openpilot.selfdrive.car.interfaces import CarStateBase
from openpilot.selfdrive.car.gwm.values import DBC, CAR, MSG_ID, Signals, Buttons, CarGear
from openpilot.selfdrive.car.common.conversions import Conversions as CV

class CarState(CarStateBase):
  def __init__(self, CP):
    super().__init__(CP)
    can_define = CANDefine(DBC[CP.carFingerprint]['pt'])
    self.shifter_values = can_define.dv[f'{MSG_ID.CAR_OVERALL_SIGNALS}.{Signals.DRIVE_MODE}']

  def update(self, cp, cp_cam):
    ret = car.CarState.new_message()

    # Update vehicle speed
    ret.vEgo = cp.vl[MSG_ID.SPEED][Signals.VEHICLE_SPEED] * CV.KPH_TO_MS
    ret.vEgoRaw = ret.vEgo

    # Update steering angle
    ret.steeringAngleDeg = cp.vl[MSG_ID.STEER_AND_AP_STALK][Signals.STEERING_ANGLE]
    ret.steeringTorque = cp.vl[MSG_ID.STEER_AND_AP_STALK][Signals.STEERING_TORQUE]
    ret.steeringPressed = abs(ret.steeringTorque) > 1.0

    # Update brake state
    ret.brakePressed = cp.vl[MSG_ID.CAR_OVERALL_SIGNALS2][Signals.BRAKE_SIGNAL] == 1
    ret.brake = cp.vl[MSG_ID.BRAKE][Signals.BRAKE_PRESSURE]

    # Update gas state
    ret.gas = cp.vl[MSG_ID.CAR_OVERALL_SIGNALS2][Signals.GAS_POSITION] / 100.0
    ret.gasPressed = ret.gas > 1e-3

    # Update gear shifter
    gear = cp.vl[MSG_ID.CAR_OVERALL_SIGNALS][Signals.DRIVE_MODE]
    ret.gearShifter = self.parse_gear_shifter(self.shifter_values.get(gear, CarGear.UNKNOWN))

    # Update button states
    ret.leftBlinker = False  # Placeholder
    ret.rightBlinker = False  # Placeholder

    # Update cruise control state
    # Note: Cruise control button events are on STEER_AND_AP_STALK
    ret.cruiseState.available = True  # For now, let's assume it's always available
    ret.cruiseState.enabled = cp.vl[MSG_ID.AUTOPILOT]['AP_STATE'] == 1
    # Set speed is not directly available in these messages, would need to be tracked
    ret.cruiseState.speed = 0 # Placeholder
    ret.cruiseState.standstill = ret.vEgo < 0.1

    # Placeholder for other states
    ret.doorOpen = False
    ret.seatbeltUnlatched = cp.vl.get(Signals.SEAT_BELT_DRIVER_STATE, 0) != 0 if Signals.SEAT_BELT_DRIVER_STATE in cp.vl else False

    # Update brake and gas pedal status
    ret.brakePressed = cp.vl.get(Signals.BRAKE_SIGNAL, 0) > 0 if Signals.BRAKE_SIGNAL in cp.vl else False
    ret.gasPressed = cp.vl.get(Signals.ACCELERATOR_PEDAL, 0) > 0 if Signals.ACCELERATOR_PEDAL in cp.vl else False

    # Placeholder for events
    events = self.create_common_events(ret)
    ret.events = events.to_msg()

    if all(signal in cp.vl for signal in [
      Signals.FRONT_LEFT_WHEEL_SPEED,
      Signals.FRONT_RIGHT_WHEEL_SPEED,
      Signals.REAR_LEFT_WHEEL_SPEED,
      Signals.REAR_RIGHT_WHEEL_SPEED
    ]):
      ret.wheelSpeeds = self.get_wheel_speeds(
        cp.vl[Signals.FRONT_LEFT_WHEEL_SPEED],
        cp.vl[Signals.FRONT_RIGHT_WHEEL_SPEED],
        cp.vl[Signals.REAR_LEFT_WHEEL_SPEED],
        cp.vl[Signals.REAR_RIGHT_WHEEL_SPEED]
      )
      ret.vEgoRaw = float(np.mean([
        ret.wheelSpeeds.fl,
        ret.wheelSpeeds.fr,
        ret.wheelSpeeds.rl,
        ret.wheelSpeeds.rr
      ]))
      ret.vEgo, ret.aEgo = self.update_speed_kf(ret.vEgoRaw)
      ret.vEgoCluster = ret.vEgo * 1.015  # Adjust for cluster speed difference
    
    ret.standstill = ret.vEgoRaw < 0.01
    
    # Update steering angle and torque
    if Signals.STEERING_ANGLE in cp.vl and Signals.STEERING_TORQUE in cp.vl:
      ret.steeringAngleDeg = cp.vl[Signals.STEERING_ANGLE]
      ret.steeringTorque = cp.vl[Signals.STEERING_TORQUE]
      ret.steeringPressed = abs(ret.steeringTorque) > STEER_THRESHOLD
      
      # Update steering angle offset
      if not self.accurate_steer_angle_seen and abs(ret.steeringAngleDeg) > 1e-3:
        self.accurate_steer_angle_seen = True
      
      if self.accurate_steer_angle_seen:
        # Apply angle offset if needed
        pass  # TODO: Implement angle offset calculation if needed
    
    # Update gear shifter
    if Signals.GEAR_SHIFTER in cp.vl:
      gear = cp.vl[Signals.GEAR_SHIFTER]
      ret.gearShifter = self.parse_gear_shifter(self.shifter_values.get(gear, None))
    
    # Update turn signals
    if all(signal in cp.vl for signal in [Signals.LEFT_TURN_SIGNAL, Signals.RIGHT_TURN_SIGNAL]):
      ret.leftBlinker = cp.vl[Signals.LEFT_TURN_SIGNAL] == 1
      ret.rightBlinker = cp.vl[Signals.RIGHT_TURN_SIGNAL] == 1
    
    # Update cruise control state
    if Signals.CRUISE_STATE in cp.vl:
      cruise_state = cp.vl[Signals.CRUISE_STATE]
      ret.cruiseState.enabled = bool(cruise_state & 0x1)
      ret.cruiseState.speed = cp.vl.get(Signals.CRUISE_SPEED, 0) * CV.KPH_TO_MS
      ret.cruiseState.available = True  # TODO: Check actual availability signal
    
    # Update button events
    if Signals.DISTANCE_BUTTON in cp.vl:
      self.distance_button = cp.vl[Signals.DISTANCE_BUTTON]
      ret.buttonEvents = create_button_events(
        self.distance_button, self.prev_distance_button, {1: ButtonType.gapAdjustCruise}
      )
      self.prev_distance_button = self.distance_button
    
    return ret
