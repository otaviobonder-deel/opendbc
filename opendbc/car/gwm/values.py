from dataclasses import dataclass, field
from enum import IntFlag

from opendbc.car import Bus, CarSpecs, DbcDict, PlatformConfig, Platforms
from opendbc.car.structs import CarParams
from opendbc.car.docs_definitions import CarDocs, CarParts, CarHarness
from opendbc.car.fw_query_definitions import FwQueryConfig, Request, StdQueries

Ecu = CarParams.Ecu


class CarControllerParams:
  # These are placeholders for now - will need tuning when control is implemented
  STEER_STEP = 3        # 33Hz
  ACC_CONTROL_STEP = 2  # 50Hz

  # No steering control for now
  ANGLE_LIMITS = None

  def __init__(self, CP):
    pass


class GWMSafetyFlags(IntFlag):
  # No safety flags yet - will add when implementing control
  pass


class GWMFlags(IntFlag):
  # Static flags if needed
  pass


@dataclass
class GWMCarDocs(CarDocs):
  package: str = "Stock"

  def init_make(self, CP: CarParams):
    self.car_parts = CarParts.common([CarHarness.custom])


@dataclass
class GWMPlatformConfig(PlatformConfig):
  dbc_dict: DbcDict = field(default_factory=lambda: {
    Bus.pt: 'gwm_haval_h6_phev_2024',  # Using the DBC file name without .dbc extension
  })


class CAR(Platforms):
  GWM_HAVAL_H6_PHEV = GWMPlatformConfig(
    [GWMCarDocs("GWM Haval H6 Plug-in Hybrid 2024", "All")],
    CarSpecs(mass=1920, wheelbase=2.738, steerRatio=16.0),  # TODO: Verify these values
    )


# Basic FW query config - minimal setup for legacy fingerprint fallback
FW_QUERY_CONFIG = FwQueryConfig(
  requests=[
    Request(
      [StdQueries.TESTER_PRESENT_REQUEST, StdQueries.MANUFACTURER_SOFTWARE_VERSION_REQUEST],
      [StdQueries.TESTER_PRESENT_RESPONSE, StdQueries.MANUFACTURER_SOFTWARE_VERSION_RESPONSE],
      logging=True,
    ),
  ],
)

DBC = CAR.create_dbc_map()