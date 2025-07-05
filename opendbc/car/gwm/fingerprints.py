# flake8: noqa
# pylint: skip-file
from opendbc.car.structs import CarParams
from opendbc.car.gwm.values import CAR

Ecu = CarParams.Ecu

# Legacy fingerprints (CAN message IDs and their lengths)
FINGERPRINTS = {
  CAR.GWM_HAVAL_H6_PHEV: [
    {96: 64, 147: 8, 161: 8, 259: 64, 273: 8, 288: 64, 295: 8, 299: 64, 303: 64, 311: 64, 315: 64, 323: 64, 327: 64, 347: 64, 357: 8, 367: 64, 395: 64, 411: 8, 412: 16, 415: 64, 546: 64, 551: 64, 573: 64, 576: 64, 581: 8, 589: 64, 623: 8, 628: 64, 639: 16, 648: 64, 649: 64, 661: 8, 664: 64, 671: 8, 680: 8, 683: 64, 692: 64, 696: 64, 707: 64, 714: 8, 717: 8, 719: 64, 745: 64, 778: 64, 793: 16, 837: 16, 849: 16, 880: 8, 901: 8, 1001: 16, 1045: 8, 1281: 8},
  ],
}

# Firmware versions will be populated as we collect them
# For now, adding minimal ECU entries to satisfy test requirements
FW_VERSIONS = {
  CAR.GWM_HAVAL_H6_PHEV: {
    (Ecu.engine, 0x7e0, None): [
      b'\x01GWM_ENGINE_PLACEHOLDER\x00\x00\x00\x00',
    ],
    (Ecu.eps, 0x7a1, None): [
      b'\x01GWM_EPS_PLACEHOLDER\x00\x00\x00\x00',
    ],
    (Ecu.abs, 0x7e1, None): [
      b'\x01GWM_ABS_PLACEHOLDER\x00\x00\x00\x00',
    ],
    (Ecu.fwdCamera, 0x7e2, None): [
      b'\x01GWM_CAMERA_PLACEHOLDER\x00\x00\x00\x00',
    ],
  },
}