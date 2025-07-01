import panda.tests.safety.common as common
from opendbc.car.gwm.values import MSG_ID, Signals, CarControllerParams

# Safety-critical CAN messages for the GWM Haval H6 PHEV 2024
TX_MSGS = [
    [MSG_ID.AUTOPILOT, 0],
]

RX_CHECKS = [
    # (message ID, frequency in Hz)
    (MSG_ID.STEER_AND_AP_STALK, 50),
    (MSG_ID.SPEED, 50),
    (MSG_ID.CAR_OVERALL_SIGNALS, 50),
    (MSG_ID.CAR_OVERALL_SIGNALS2, 50),
]

class SafetyGwm(common.PandaSafety):
  def __init__(self, panda):
    super().__init__(panda)
    self.last_steer_req = 0
    self.last_steer_angle = 0
    self.steer_override = False

  def _rx_hook(self, pkt):
    addr = self.get_addr(pkt)
    if addr == MSG_ID.STEER_AND_AP_STALK:
      steer_angle = self.get_signal(pkt, Signals.STEERING_ANGLE)
      if abs(steer_angle - self.last_steer_angle) > 5.0:
          self.steer_override = True
      self.last_steer_angle = steer_angle
    return True

  def _tx_hook(self, pkt):
    if self.get_addr(pkt) == MSG_ID.AUTOPILOT:
      steer_torque = self.get_signal(pkt, Signals.AP_STEERING_COMMAND)
      if self.steer_override or not self.steer_torque_cmd_check(steer_torque, self.last_steer_req, CarControllerParams):
        return False
    return True

  def _tx_lin_hook(self, lin_data):
    return True

  def steer_torque_cmd_check(self, torque, steer_req, params):
    self.last_steer_req = steer_req
    if steer_req and abs(torque) > params.STEER_MAX:
      return False
    return True
