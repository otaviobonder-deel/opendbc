import unittest
import numpy as np
from opendbc.can.parser import CANParser
from opendbc.can.packer import CANPacker
from openpilot.selfdrive.pandad import can_list_to_can_capnp
from opendbc.can import can_define
from opendbc.car.gwm.interface import CarInterface
from opendbc.car.gwm.values import CAR, DBC, MSG_ID, Signals
from opendbc.car.gwm.carstate import CarState
from opendbc.car.gwm.carcontroller import CarController


def create_can_parser(cp, dbc_name):
  """Helper function to create a CAN parser for testing"""
  dbc_fp = DBC[dbc_name]['pt']
  return CANParser(dbc_fp, cp, 0)


def create_can_packer(dbc_name):
  """Helper function to create a CAN packer for testing"""
  dbc_fp = DBC[dbc_name]['pt']
  return CANPacker(dbc_fp)


class TestGWMInterface(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    # Initialize test parameters
    cls.car_model = CAR.HAVAL_H6_PHEV_2024
    cls.CP = CarInterface.get_std_params(cls.car_model)
    cls.CI = CarInterface(cls.CP, None, None)
    
    # Create CAN parser and packer
    cls.can_parser = create_can_parser(cls.CI.get_common_global_msgs(), 'gwm_haval_h6_phev_2024')
    cls.can_packer = create_can_packer('gwm_haval_h6_phev_2024')
    
    # Initialize car state
    cls.CS = CarState(cls.CP)
    
    # Initialize car controller
    cls.CC = CarController(cls.CP, cls.CI.car_fingerprint)

  def test_steering_angle_parsing(self):
    """Test that steering angle is parsed correctly from CAN messages"""
    # Create a test steering angle message
    test_angle = 5.0  # degrees
    msg = self.can_packer.make_can_msg(
      "STEER_ANGLE_SENSOR",
      0,
      {"STEER_ANGLE": test_angle}
    )
    
    # Update the parser with the test message
    msgs = [msg]
    self.can_parser.update_strings([msg[2] for msg in msgs])
    
    # Update car state with the parsed message
    self.CS.update(self.can_parser)
    
    # Check that the steering angle was parsed correctly
    self.assertAlmostEqual(self.CS.angle_steers, test_angle, places=1)

  def test_vehicle_speed_parsing(self):
    """Test that vehicle speed is parsed correctly from CAN messages"""
    # Create a test vehicle speed message (50 km/h)
    test_speed = 50.0  # km/h
    msg = self.can_packer.make_can_msg(
      "VEHICLE_SPEED",
      0,
      {"VEHICLE_SPEED": test_speed}
    )
    
    # Update the parser with the test message
    msgs = [msg]
    self.can_parser.update_strings([msg[2] for msg in msgs])
    
    # Update car state with the parsed message
    self.CS.update(self.can_parser)
    
    # Check that the vehicle speed was parsed correctly
    # Convert km/h to m/s for comparison
    expected_speed = test_speed / 3.6
    self.assertAlmostEqual(self.CS.v_ego, expected_speed, places=1)

  def test_brake_pedal_parsing(self):
    """Test that brake pedal state is parsed correctly from CAN messages"""
    # Create a test brake pedal message (pressed)
    msg = self.can_packer.make_can_msg(
      "BRAKE_STATUS",
      0,
      {"BRAKE_PRESSED": 1, "BRAKE_PRESSURE": 10.5}
    )
    
    # Update the parser with the test message
    msgs = [msg]
    self.can_parser.update_strings([msg[2] for msg in msgs])
    
    # Update car state with the parsed message
    self.CS.update(self.can_parser)
    
    # Check that the brake pedal state was parsed correctly
    self.assertTrue(self.CS.brake_pressed)
    self.assertAlmostEqual(self.CS.brake_pressure, 10.5, places=1)

  def test_gas_pedal_parsing(self):
    """Test that gas pedal state is parsed correctly from CAN messages"""
    # Create a test gas pedal message (50% pressed)
    test_pedal = 50.0  # %
    msg = self.can_packer.make_can_msg(
      "GAS_STATUS",
      0,
      {"GAS_PEDAL": test_pedal}
    )
    
    # Update the parser with the test message
    msgs = [msg]
    self.can_parser.update_strings([msg[2] for msg in msgs])
    
    # Update car state with the parsed message
    self.CS.update(self.can_parser)
    
    # Check that the gas pedal state was parsed correctly
    self.assertAlmostEqual(self.CS.gas_pedal, test_pedal / 100.0, places=2)

  def test_gear_shifter_parsing(self):
    """Test that gear shifter position is parsed correctly from CAN messages"""
    # Create a test gear shifter message (Drive)
    test_gear = 4  # Drive
    msg = self.can_packer.make_can_msg(
      "GEAR_STATUS",
      0,
      {"GEAR_SHIFTER": test_gear}
    )
    
    # Update the parser with the test message
    msgs = [msg]
    self.can_parser.update_strings([msg[2] for msg in msgs])
    
    # Update car state with the parsed message
    self.CS.update(self.can_parser)
    
    # Check that the gear shifter position was parsed correctly
    self.assertEqual(self.CS.gear_shifter, test_gear)

  def test_steering_control(self):
    """Test that steering control commands are generated correctly"""
    # Create a test steering command (10% of max torque)
    test_steer = 0.1  # 10% of max torque
    
    # Create a test car control message
    class TestCarControl:
      def __init__(self):
        self.actuators = type('Actuators', (), {
          'steer': test_steer,
          'steerAngle': 0.0,
          'accel': 0.0,
          'brake': 0.0,
        })
        self.enabled = True
        self.active = True
        self.cruiseControl = type('CruiseControl', (), {'cancel': False})
        self.hudControl = type('HUDControl', (), {'setSpeed': 0, 'visualAlert': 'none'})
    
    # Generate CAN messages
    can_sends = self.CC.update(TestCarControl(), self.CS, 0)
    
    # Check that the correct number of messages were generated
    self.assertGreater(len(can_sends), 0)
    
    # Check that the steering command was generated correctly
    steer_found = False
    for addr, _, dat, _ in can_sends:
      if addr == MSG_ID.STEER_REQUEST:
        steer_found = True
        # Check that the steering torque is within expected range
        # (test_steer * STEER_MAX should be approximately the value in the message)
        expected_torque = int(test_steer * self.CC.params.STEER_MAX)
        # The actual value will depend on the CAN message format
        # This is a simplified check - adjust as needed for your implementation
        self.assertGreater(dat[0], 0)  # Just check that some data is present
    
    self.assertTrue(steer_found, "Steering command not found in CAN messages")

  def test_longitudinal_control(self):
    """Test that longitudinal control commands are generated correctly"""
    # Create a test acceleration command (0.5 m/s^2)
    test_accel = 0.5  # m/s^2
    
    # Create a test car control message
    class TestCarControl:
      def __init__(self):
        self.actuators = type('Actuators', (), {
          'steer': 0.0,
          'steerAngle': 0.0,
          'accel': test_accel,
          'brake': 0.0,
        })
        self.enabled = True
        self.active = True
        self.cruiseControl = type('CruiseControl', (), {'cancel': False})
        self.hudControl = type('HUDControl', (), {'setSpeed': 0, 'visualAlert': 'none'})
    
    # Generate CAN messages
    can_sends = self.CC.update(TestCarControl(), self.CS, 0)
    
    # Check that the correct number of messages were generated
    self.assertGreater(len(can_sends), 0)
    
    # Check that the acceleration command was generated correctly
    accel_found = False
    for addr, _, dat, _ in can_sends:
      if addr == MSG_ID.ACCEL_CMD:
        accel_found = True
        # Check that the acceleration command is within expected range
        # This is a simplified check - adjust as needed for your implementation
        self.assertGreater(dat[0], 0)  # Just check that some data is present
    
    self.assertTrue(accel_found, "Acceleration command not found in CAN messages")


if __name__ == "__main__":
  unittest.main()
