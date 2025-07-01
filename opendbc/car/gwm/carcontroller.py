from cereal import car
from opendbc.can.packer import CANPacker
from openpilot.selfdrive.car.gwm.values import DBC, CAR, MSG_ID, Signals, CarControllerParams, GwmChecksum

class CarController:
  def __init__(self, dbc_name, CP, VM):
    self.CP = CP
    self.packer = CANPacker(DBC[CP.carFingerprint]['pt'])
    self.gwm_checksum = GwmChecksum()
    self.frame = 0

  def update(self, c, CS):
    can_sends = []
    actuators = c.actuators

    # Steering command
    if c.enabled:
      steer_req = 1
      # Apply steering torque
      apply_steer = int(round(actuators.steer * CarControllerParams.STEER_MAX))
      apply_steer = max(-CarControllerParams.STEER_MAX, min(CarControllerParams.STEER_MAX, apply_steer))
    else:
      steer_req = 0
      apply_steer = 0

    # Create the steering command message
    # NOTE: This message requires a checksum and counter.
    # The GWM checksum is custom. A manual packing implementation might be needed
    # if the CANPacker does not handle it correctly based on the DBC.
    # For now, we assume the packer can handle it.
    values = {
      Signals.AP_STEERING_COMMAND: apply_steer,
      Signals.AP_STATE: steer_req,
    }
    
    can_sends.append(self.packer.make_can_msg(MSG_ID.AUTOPILOT, 0, values))
    
    self.frame += 1
    return can_sends
