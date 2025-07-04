#!/usr/bin/env python3
import unittest
from opendbc.car.structs import CarParams
from opendbc.safety.tests.libsafety import libsafety_py
import opendbc.safety.tests.common as common
from opendbc.safety.tests.common import CANPackerPanda


class TestGwmSafetyBase(common.PandaCarSafetyTest, common.TorqueSteeringSafetyTestBase):
  TX_MSGS = [[0x12B, 0], [0x12B, 2]]
  STANDSTILL_THRESHOLD = 0
  RELAY_MALFUNCTION_ADDRS = {0: (0x12B,)}
  FWD_BLACKLISTED_ADDRS = {2: [0x12B]}
  FWD_BUS_LOOKUP = {0: 2, 2: 0}

  MAX_TORQUE = 1023
  MAX_RT_DELTA = 112
  RT_INTERVAL = 250000
  MAX_TORQUE_ERROR = 350

  DRIVER_TORQUE_ALLOWANCE = 50
  DRIVER_TORQUE_FACTOR = 1

  packer: CANPackerPanda
  safety: libsafety_py.Panda

  def _torque_driver_msg(self, torque):
    values = {"STEERING_TORQUE": torque}
    return self.packer.make_can_msg_panda("STEER_AND_AP_STALK", 0, values)

  def _torque_cmd_msg(self, torque, steer_req=1):
    values = {"AP_STEERING_UNDEFINED_SIGNAL1": torque, "AP_STATE": steer_req}
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


class TestGwmSafety(TestGwmSafetyBase):
  MAX_RATE_UP = 15
  MAX_RATE_DOWN = 25
  MAX_TORQUE_LOOKUP = ([0], [1023])

  def setUp(self):
    self.packer = CANPackerPanda("gwm_haval_h6_phev_2024")
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(CarParams.SafetyModel.gwm, 0)
    self.safety.init_tests()


if __name__ == "__main__":
  unittest.main()