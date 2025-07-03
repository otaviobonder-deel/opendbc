from opendbc.can.packer import CANPacker
from opendbc.car.interfaces import CarControllerBase
from opendbc.car.gwm.values import CarControllerParams, GwmChecksum, Bus
from opendbc.car.gwm import gwmcan

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
      apply_steer = int(round(actuators.torque * CarControllerParams.STEER_MAX))
      apply_steer = max(-CarControllerParams.STEER_MAX, min(CarControllerParams.STEER_MAX, apply_steer))
    else:
      steer_req = 0
      apply_steer = 0

    # Create the steering command message with proper counter
    # Counter increments every 20ms (50Hz)
    counter = self.frame % 16
    can_sends.append(gwmcan.create_steer_command(self.packer, apply_steer, steer_req, counter))

    self.frame += 1
    return can_sends
