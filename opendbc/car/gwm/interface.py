from cereal import car
from openpilot.selfdrive.car import get_safety_config
from openpilot.selfdrive.car.interfaces import CarInterfaceBase
from openpilot.selfdrive.car.gwm.values import CAR, DBC, CAR_INFO
from openpilot.selfdrive.car.gwm.carstate import CarState
from openpilot.selfdrive.car.gwm.carcontroller import CarController

CarParams = car.CarParams

class CarInterface(CarInterfaceBase):
  CarState = CarState
  CarController = CarController

  @staticmethod
  def get_params(candidate, fingerprint=None, car_fw=None, experimental_long=False):
    ret = CarInterfaceBase.get_std_params(candidate, fingerprint)
    ret.carName = "gwm"
    ret.safetyConfigs = [get_safety_config(CarParams.SafetyModel.gwm)]
    # The GWM port is a community feature, since we don't own one to test
    ret.communityFeature = True

    # Set vehicle parameters from CAR_INFO
    if candidate in CAR_INFO:
        info = CAR_INFO[candidate]
        ret.mass = info.specs.mass
        ret.wheelbase = info.specs.wheelbase
        ret.steerRatio = info.specs.steerRatio
        ret.centerToFront = info.specs.wheelbase * 0.44
        ret.steerControlType = info.specs.steerControlType
        ret.minEnableSpeed = info.specs.minEnableSpeed
        ret.minSteerSpeed = info.specs.minSteerSpeed

    ret.steerActuatorDelay = 0.1
    ret.steerLimitTimer = 0.4

    # Longitudinal control parameters
    ret.experimentalLongitudinalAvailable = True
    ret.openpilotLongitudinalControl = experimental_long
    ret.longitudinalTuning.kpBP = [0., 5., 35.]
    ret.longitudinalTuning.kpV = [1.2, 0.8, 0.5]
    ret.longitudinalTuning.kiBP = [0., 35.]
    ret.longitudinalTuning.kiV = [0.18, 0.12]

    return ret

  def update(self, c, can_strings):
    self.cp.update_strings(can_strings)
    self.cp_cam.update_strings(can_strings)

    ret = self.CS.update(self.cp, self.cp_cam)
    ret.canValid = self.cp.can_valid and self.cp_cam.can_valid

    # Handle events
    events = self.create_common_events(ret)
    ret.events = events.to_msg()

    self.CS.out = ret.as_reader()
    return self.CS.out

  def apply(self, c):
    can_sends = self.CC.update(c, self.CS)
    return can_sends
