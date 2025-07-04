def create_steer_command(packer, steer_torque, steer_request, raw_cnt):
  """Creates a CAN message for the GWM steer command."""
  values = {
    "AP_STEERING_UNDEFINED_SIGNAL1": steer_torque,
    "AP_STATE": steer_request,
    "AP_COUNTER": raw_cnt,
  }
  return packer.make_can_msg("AUTOPILOT", 0, values)