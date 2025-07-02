from opendbc.can.packer import CANPacker
from opendbc.car.interfaces import CarControllerBase
from opendbc.car.gwm.values import MSG_ID, Signals, GwmCarControllerParams, GwmChecksum, Bus

class CarController(CarControllerBase):
  def __init__(self, dbc_names, CP):
    super().__init__(dbc_names, CP)
    self.packer = CANPacker(dbc_names[Bus.pt])
    self.gwm_checksum = GwmChecksum()
    self.frame = 0

  def update(self, CC, CS, now_nanos):
    can_sends = []
    actuators = CC.actuators

    # Steering command
    if CC.enabled:
      steer_req = 1
      # Apply steering torque
      apply_steer = int(round(actuators.torque * GwmCarControllerParams.STEER_MAX))
      apply_steer = max(-GwmCarControllerParams.STEER_MAX, min(GwmCarControllerParams.STEER_MAX, apply_steer))
    else:
      steer_req = 0
      apply_steer = 0

    # Create the steering command message
    # NOTE: This message requires a checksum and counter.
    # The GWM checksum is custom.
    values = {
      Signals.AP_STEERING_COMMAND: apply_steer,
      Signals.AP_STATE: steer_req,
    }

    # TODO: Implement proper checksum and counter logic using self.gwm_checksum
    # For now, assuming packer handles it based on DBC.
    can_sends.append(self.packer.make_can_msg(MSG_ID.AUTOPILOT, Bus.pt, values))

    self.frame += 1
    return can_sends
