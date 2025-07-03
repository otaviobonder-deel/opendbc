import unittest

from cereal import car
from opendbc.can.parser import CANParser
from opendbc.can.packer import CANPacker
from opendbc.car.structs import CarParams
from opendbc.car.gwm.interface import CarInterface
from opendbc.car.gwm.values import CAR, DBC, MSG_ID, Signals, CarGear, CarControllerParams
from opendbc.car.gwm.fingerprints import FW_VERSIONS


Ecu = CarParams.Ecu

class TestGWMInterface(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.CP = CarInterface.get_params(CAR.GWM_HAVAL_H6_PHEV_2024.value, {}, [], alpha_long=False, is_release=False, docs=False)
    cls.CI = CarInterface(cls.CP)

  def setUp(self):
    self.CI.CS.out = car.CarState.new_message()

  def test_car_params(self):
    self.assertEqual(self.CP.brand, "gwm")
    self.assertEqual(self.CP.mass, 2176)

  def test_can_parsing(self):
    packer = CANPacker(DBC[self.CP.carFingerprint]['pt'])
    msgs = []
    msgs.append(packer.make_can_msg(MSG_ID.STEER_AND_AP_STALK, 0, {Signals.STEERING_ANGLE: 10.0, Signals.STEERING_TORQUE: 5.0}))
    msgs.append(packer.make_can_msg(MSG_ID.SPEED, 0, {Signals.VEHICLE_SPEED: 50.0}))
    msgs.append(packer.make_can_msg(MSG_ID.CAR_OVERALL_SIGNALS2, 0, {Signals.BRAKE_SIGNAL: 1, Signals.GAS_POSITION: 50.0}))
    msgs.append(packer.make_can_msg(MSG_ID.BRAKE, 0, {Signals.BRAKE_PRESSURE: 100.0}))
    msgs.append(packer.make_can_msg(MSG_ID.CAR_OVERALL_SIGNALS, 0, {Signals.DRIVE_MODE: 4}))
    msgs.append(packer.make_can_msg(MSG_ID.AUTOPILOT, 0, {Signals.AP_STATE: 1}))

    # All messages are at timestamp 0, create the can_packets structure
    can_packets = [(0, msgs)]

    self.CI.update(can_packets)

    cs = self.CI.CS.out
    self.assertAlmostEqual(cs.steeringAngleDeg, 10.0)
    self.assertAlmostEqual(cs.steeringTorque, 5.0)
    self.assertTrue(cs.steeringPressed)
    self.assertAlmostEqual(cs.vEgo, 50.0 / 3.6, places=2)
    self.assertTrue(cs.brakePressed)
    self.assertAlmostEqual(cs.brake, 100.0)
    self.assertAlmostEqual(cs.gas, 0.5)
    self.assertTrue(cs.gasPressed)
    self.assertEqual(cs.gearShifter, CarGear.DRIVE)
    self.assertTrue(cs.cruiseState.enabled)

  def test_steering_control(self):
    self.CI.CS.out.vEgo = 10.0
    self.CI.CS.out.steeringAngleDeg = 5.0

    cc = car.CarControl.new_message()
    cc.enabled = True
    cc.latActive = True
    cc.actuators.torque = 0.5

    can_sends = self.CI.apply(cc)
    self.assertGreater(len(can_sends), 0)

    steer_msg_tuple = [msg for msg in can_sends if msg[0] == MSG_ID.AUTOPILOT][0]
    steer_msg_addr, steer_msg_data, steer_msg_bus = steer_msg_tuple

    parser = CANParser(DBC[self.CP.carFingerprint]['pt'], [('AUTOPILOT', 50)], 0)
    # The CANParser expects the bus number (an int), not the bus name (a string).
    parser.update_strings([(0, [(steer_msg_addr, steer_msg_data, 0)])])
    unpacked = parser.vl['AUTOPILOT']

    expected_steer = int(round(0.5 * CarControllerParams.STEER_MAX))
    self.assertEqual(unpacked[Signals.AP_STEERING_COMMAND], expected_steer)
    self.assertEqual(unpacked[Signals.AP_STATE], 1)

class TestGWMFingerprint(unittest.TestCase):
  def test_essential_ecus(self):
    # Asserts standard ECUs exist for each platform
    common_ecus = {Ecu.fwdRadar, Ecu.fwdCamera, Ecu.eps, Ecu.engine}
    for car_model, ecus in FW_VERSIONS.items():
      with self.subTest(car_model=car_model.value):
        present_ecus = {ecu[0] for ecu in ecus}
        missing_ecus = common_ecus - present_ecus
        self.assertEqual(len(missing_ecus), 0)
