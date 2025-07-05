from opendbc.car import get_safety_config, structs
from opendbc.car.gwm.carcontroller import CarController
from opendbc.car.gwm.carstate import CarState
from opendbc.car.interfaces import CarInterfaceBase

TransmissionType = structs.CarParams.TransmissionType


class CarInterface(CarInterfaceBase):
  CarState = CarState
  CarController = CarController

  @staticmethod
  def _get_params(ret: structs.CarParams, candidate, fingerprint, car_fw, alpha_long, is_release, docs) -> structs.CarParams:
    ret.brand = "gwm"
    ret.autoResumeSng = False

    # Car specs
    ret.steerControlType = structs.CarParams.SteerControlType.angle
    ret.steerActuatorDelay = 0.2  # TODO: Measure this
    ret.steerLimitTimer = 1.0

    # No radar interface for now
    ret.radarUnavailable = True

    # No lateral control for initial implementation
    ret.dashcamOnly = True

    # Longitudinal control not implemented yet
    ret.openpilotLongitudinalControl = False

    # Safety model - using noOutput for now since we're not controlling
    ret.safetyConfigs = [get_safety_config(structs.CarParams.SafetyModel.noOutput)]

    # Set transmission type based on PHEV nature
    ret.transmissionType = TransmissionType.automatic

    # Speed limits
    ret.minEnableSpeed = -1.  # Can engage at any speed
    ret.minSteerSpeed = 0.    # Can steer at any speed

    # TODO: Verify these values
    ret.centerToFront = ret.wheelbase * 0.44

    return ret

  @staticmethod
  def _get_ecu_apks(CP):
    # Disable stock systems if needed
    # For now, we're not disabling anything since we're not controlling
    return {}