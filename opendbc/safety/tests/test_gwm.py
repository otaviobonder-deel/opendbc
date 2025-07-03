#!/usr/bin/env python3
import unittest
from opendbc.safety.tests import common


class TestGwmSafety(common.PandaTorqueSafetyTest):
  TX_MSGS = [[0x12B, 0], [0x12B, 2]]
  STANDSTILL_THRESHOLD = 0
  RELAY_MALFUNCTION_ADDR = 0x12B
  RELAY_MALFUNCTION_BUS = 0
  FWD_BLACKLISTED_ADDRS = {2: [0x12B]}
  FWD_BUS_LOOKUP = {0: 2, 2: 0}

  MAX_TORQUE = 1023
  MAX_RT_DELTA = 112
  RT_INTERVAL = 250000
  MAX_TORQUE_ERROR = 350

  DRIVER_TORQUE_ALLOWANCE = 50
  DRIVER_TORQUE_FACTOR = 1

  @classmethod
  def setUp(cls):
    cls.packer = None
    cls.safety = None

  def _torque_driver_msg(self, torque):
    values = {"STEERING_TORQUE": torque}
    return self.packer.make_can_msg_panda("STEER_AND_AP_STALK", 0, values)

  def _torque_cmd_msg(self, torque, steer_req=1):
    values = {"AP_STEERING_COMMAND": torque, "AP_STATE": steer_req}
    return self.packer.make_can_msg_panda("AUTOPILOT", 0, values)

  def _speed_msg(self, speed):
    values = {"SPEED": speed}
    return self.packer.make_can_msg_panda("SPEED", 0, values)

  def _user_brake_msg(self, brake):
    values = {"BRAKE_SIGNAL": 1 if brake else 0}
    return self.packer.make_can_msg_panda("CAR_OVERALL_SIGNALS2", 0, values)

  def _user_gas_msg(self, gas):
    values = {"GAS_POSITION": gas * 100}
    return self.packer.make_can_msg_panda("CAR_OVERALL_SIGNALS2", 0, values)

  def _pcm_status_msg(self, enable):
    values = {"AP_STATE": 1 if enable else 0}
    return self.packer.make_can_msg_panda("AUTOPILOT", 0, values)


class TestGwmSafetyBase(TestGwmSafety):
  FLAGS = 0
  MAX_RATE_UP = 15
  MAX_RATE_DOWN = 25
  ANGLE_RATE_BP = [0., 5., 35.]
  ANGLE_RATE_UP = [15., 0.8, 0.15]   # unused
  ANGLE_RATE_DOWN = [25., 1.5, 0.4]  # unused

  def setUp(self):
    self.packer = common.make_msg_packer("gwm_haval_h6_phev_2024")
    self.safety = common.libpanda_py.libpanda.safety_gwm_init(self.FLAGS)
    self.safety.set_safety_hooks(common.Panda.SAFETY_GWM, self.FLAGS)
    self.safety.init_tests()


class TestGwmSafety(TestGwmSafetyBase):
  pass


if __name__ == "__main__":
  unittest.main()