from opendbc.car.structs import CarParams
from opendbc.car.gwm.values import CAR

Ecu = CarParams.Ecu

# Deprecated fingerprint format (message ID: length)
FINGERPRINTS = {
  CAR.GWM_HAVAL_H6_PHEV_2024: [{
    367: 64, 311: 64, 315: 64, 415: 64, 546: 64, 551: 64, 573: 64, 576: 64, 147: 8, 412: 16, 288: 64, 96: 64, 161: 8, 273: 8, 259: 64, 581: 8, 849: 16, 327: 64, 295: 8, 299: 64, 323: 64, 395: 64, 347: 64, 628: 64, 664: 64, 649: 64, 303: 64, 357: 8, 411: 8, 623: 8, 639: 16, 648: 64, 707: 64, 745: 64, 880: 8, 1045: 8, 589: 64, 793: 16, 661: 8, 837: 16, 901: 8, 778: 64, 680: 8, 683: 64, 692: 64, 696: 64, 719: 64, 717: 8, 671: 8, 714: 8, 1281: 8, 1001: 16
  }],
}

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
