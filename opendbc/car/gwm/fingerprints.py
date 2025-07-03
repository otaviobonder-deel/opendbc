from opendbc.car.structs import CarParams
from opendbc.car.gwm.values import CAR

Ecu = CarParams.Ecu

FW_VERSIONS = {
  CAR.GWM_HAVAL_H6_PHEV_2024: {
    (Ecu.fwdCamera, 0x750, 0): [
      b'placeholder_fw_camera',
    ],
    (Ecu.fwdRadar, 0x751, 0): [
      b'placeholder_fw_radar',
    ],
    (Ecu.eps, 0x752, 0): [
      b'placeholder_fw_eps',
    ],
    (Ecu.engine, 0x753, 0): [
      b'placeholder_fw_engine',
    ],
  },
}
