# GWM (Great Wall Motors) Port for openpilot

This directory contains the openpilot port for GWM (Great Wall Motors) vehicles, specifically the Haval H6 PHEV 2024 model.

## Supported Vehicles

- **GWM Haval H6 PHEV 2024** - Initial support with basic longitudinal and lateral control

## Implementation Status

- [x] Basic CAN message parsing
- [x] CarState implementation
- [x] CarController implementation
- [x] CarInterface implementation
- [x] Safety model integration
- [ ] Full steering torque control validation
- [ ] Full longitudinal control validation
- [ ] Real-world testing and tuning

## Dependencies

- openpilot v0.9.0 or later
- Python 3.8+
- Required Python packages:
  - numpy
  - pycapnp
  - panda

## Testing

### Unit Tests

Run the unit tests to verify basic functionality:

```bash
cd /path/to/openpilot/opendbc/car/gwm
python -m unittest discover -s tests
```

### Bench Testing

To perform a bench test of the interface using simulated CAN messages:

```bash
cd /path/to/openpilot/opendbc/car/gwm/tools
python bench_test.py
```

### CAN Message Logging

To log and analyze CAN messages from a GWM vehicle:

1. Connect a compatible CAN interface (e.g., panda, Kvaser)
2. Use the following command to log CAN messages:

```bash
cd /path/to/openpilot
PYTHONPATH=$PWD ./tools/plotjuggler/juggle.py --demo gwm_haval_h6_phev_2024
```

## CAN Message Reference

### Important Message IDs

| Message Name       | ID (hex) | Description                          |
|--------------------|----------|--------------------------------------|
| STEER_ANGLE_SENSOR | 0x2E6    | Steering angle sensor data           |
| VEHICLE_SPEED      | 0x3F1    | Vehicle speed                        |
| BRAKE_STATUS       | 0x2E8    | Brake pedal status and pressure      |
| GAS_STATUS         | 0x2EA    | Gas pedal position                   |
| GEAR_STATUS        | 0x2EC    | Gear shifter position                |
| STEER_REQUEST      | 0x2E5    | Steering torque request              |
| ACCEL_CMD          | 0x2E9    | Acceleration command                 |
| BRAKE_CMD          | 0x2E7    | Brake command                        |

### Signal Reference

#### Steering Angle Sensor (0x2E6)

| Signal Name   | Start Bit | Length | Factor | Offset | Unit |
|---------------|-----------|--------|--------|--------|------|
| STEER_ANGLE   | 0         | 16     | 0.1    | -3276.8| deg  |
| STEER_RATE    | 16        | 16     | 1      | -32768 | deg/s|

#### Vehicle Speed (0x3F1)

| Signal Name   | Start Bit | Length | Factor | Offset | Unit  |
|---------------|-----------|--------|--------|--------|-------|
| VEHICLE_SPEED | 0         | 16     | 0.01   | 0      | km/h  |

#### Brake Status (0x2E8)

| Signal Name   | Start Bit | Length | Factor | Offset | Unit  |
|---------------|-----------|--------|--------|--------|-------|
| BRAKE_PRESSED | 0         | 1      | 1      | 0      | bool  |
| BRAKE_PRESSURE| 8         | 8      | 0.1    | 0      | bar   |

## Development Notes

### Adding Support for New GWM Models

1. Add the new model to the `CAR` enum in `values.py`
2. Update the platform configuration in `values.py`
3. Add any model-specific parameters and signals
4. Update the CAN message definitions if needed
5. Add test cases for the new model

### Tuning Parameters

Key parameters that may need adjustment for different GWM models:

- `STEER_RATIO`: Steering ratio (turns lock-to-lock)
- `STEER_MAX`: Maximum steering torque
- `STEER_DELTA_UP`: Rate limit for increasing torque
- `STEER_DELTA_DOWN`: Rate limit for decreasing torque
- `ACCEL_MAX`: Maximum acceleration
- `ACCEL_MIN`: Maximum deceleration

### Safety Considerations

- The safety model enforces maximum torque limits and rate limits
- Steering torque is limited to prevent mechanical stress
- Automatic disengagement occurs on driver override or system fault

## Contributing

Contributions to improve the GWM port are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add or update tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
