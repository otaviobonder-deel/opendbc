from opendbc.car.structs import CarParams
from opendbc.car.gwm.values import CAR

Ecu = CarParams.Ecu

FW_VERSIONS = {
  CAR.GWM_HAVAL_H6_PHEV_2024: {
    (Ecu.engine, 0x7e0, None): [
      b'\x01GWM_ENGINE_2024\x00\x00\x00\x00',
    ],
    (Ecu.eps, 0x7a1, None): [
      b'\x01GWM_EPS_2024\x00\x00\x00\x00\x00',
    ],
    (Ecu.fwdRadar, 0x750, 0xf): [
      b'\x01GWM_RADAR_2024\x00\x00\x00\x00',
    ],
    (Ecu.fwdCamera, 0x750, 0x6d): [
      b'\x01GWM_CAMERA_2024\x00\x00\x00\x00',
    ],
  },
}
