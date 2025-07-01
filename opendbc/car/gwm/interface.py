from cereal import car
from opendbc.car import get_safety_config, structs
from opendbc.car.interfaces import CarInterfaceBase
from opendbc.car.gwm.values import CAR
from opendbc.car.gwm.carstate import CarState
from opendbc.car.gwm.carcontroller import CarController

CarParams = car.CarParams

class CarInterface(CarInterfaceBase):
  CarState = CarState
  CarController = CarController

  @staticmethod
  def _get_params(ret: structs.CarParams, candidate, fingerprint, car_fw, alpha_long, is_release, docs) -> structs.CarParams:
    ret.brand = "gwm"
    ret.safetyConfigs = [get_safety_config(CarParams.SafetyModel.gwm)]

    # get vehicle params from platform config
    ret.mass = CAR.GWM_HAVAL_H6_PHEV_2024.config.specs.mass
    ret.wheelbase = CAR.GWM_HAVAL_H6_PHEV_2024.config.specs.wheelbase
    ret.steerRatio = CAR.GWM_HAVAL_H6_PHEV_2024.config.specs.steerRatio
    ret.centerToFront = ret.wheelbase * CAR.GWM_HAVAL_H6_PHEV_2024.config.specs.centerToFrontRatio

    # lateral control
    ret.steerActuatorDelay = 0.4
    ret.steerLimitTimer = 0.4

    # longitudinal control
    ret.openpilotLongitudinalControl = alpha_long
    ret.longitudinalTuning.kpBP = [0., 5., 35.]
    ret.longitudinalTuning.kpV = [1.2, 0.8, 0.5]
    ret.longitudinalTuning.kiBP = [0., 35.]
    ret.longitudinalTuning.kiV = [0.18, 0.12]

    return ret
