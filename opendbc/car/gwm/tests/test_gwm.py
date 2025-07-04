import unittest

from opendbc.can.parser import CANParser
from opendbc.can.packer import CANPacker
from opendbc.car.structs import CarParams
from opendbc.car.gwm.interface import CarInterface
from opendbc.car.gwm.values import CAR, DBC, MSG_ID, Signals, CarControllerParams
from opendbc.car.gwm.fingerprints import FW_VERSIONS, FINGERPRINTS

# Mock GearShifter and car module for opendbc context
class GearShifter:
    park = 0
    reverse = 1
    neutral = 2
    drive = 3

class MockCarState:
    def __init__(self):
        self.steeringAngleDeg = 0.0
        self.steeringTorque = 0.0
        self.steeringPressed = False
        self.vEgo = 0.0
        self.brakePressed = False
        self.brake = 0.0
        self.gas = 0.0
        self.gasPressed = False
        self.gearShifter = GearShifter.park
        self.cruiseState = type('cruise', (), {'enabled': False})()
        self.vEgoCluster = 0.0
        self.cluster_speed_hyst_gap = 0.5

    @staticmethod
    def new_message():
        return MockCarState()

class MockCarControl:
    def __init__(self):
        self.enabled = False
        self.latActive = False
        self.actuators = type('actuators', (), {'torque': 0.0})()

    @staticmethod
    def new_message():
        return MockCarControl()

car = type('car', (), {'CarState': MockCarState, 'CarControl': MockCarControl})

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
    msgs.append(packer.make_can_msg(MSG_ID.CAR_OVERALL_SIGNALS, 0, {Signals.DRIVE_MODE: 1}))
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
    # Handle enum comparison - try different approaches
    if str(cs.gearShifter) == 'drive':
      # Enum string comparison works
      pass
    elif hasattr(cs.gearShifter, 'name') and cs.gearShifter.name == 'drive':
      # Enum name comparison works
      pass
    elif hasattr(cs.gearShifter, 'value') and cs.gearShifter.value == 3:
      # Enum value comparison works
      pass
    else:
      # Fallback to direct comparison
      self.assertEqual(cs.gearShifter, 3)  # drive = 3
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
  def test_fingerprints_exist(self):
    # Asserts that deprecated fingerprints exist for each platform
    for car_model in CAR:
      with self.subTest(car_model=car_model.value):
        self.assertIn(car_model, FINGERPRINTS)
        self.assertIsInstance(FINGERPRINTS[car_model], list)
        self.assertGreater(len(FINGERPRINTS[car_model]), 0)
        # Check that each fingerprint is a dictionary with message ID: length format
        for fingerprint in FINGERPRINTS[car_model]:
          self.assertIsInstance(fingerprint, dict)
          for msg_id, length in fingerprint.items():
            self.assertIsInstance(msg_id, int)
            self.assertIsInstance(length, int)
            self.assertGreater(msg_id, 0)
            self.assertGreater(length, 0)
