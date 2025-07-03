const TorqueSteeringLimits GWM_STEERING_LIMITS = {
  .max_torque = 1023,
  .dynamic_max_torque = false,
  .max_torque_lookup = {0},
  .max_rate_up = 15,
  .max_rate_down = 25,
  .max_rt_delta = 112,
  .type = TorqueDriverLimited,
  .driver_torque_allowance = 50,
  .driver_torque_multiplier = 1,
  .max_torque_error = 350,
  .min_valid_request_frames = 1,
  .max_invalid_request_frames = 1,
  .min_valid_request_rt_interval = 170000,  // 170ms
  .has_steer_req_tolerance = false,
};

const LongitudinalLimits GWM_LONG_LIMITS = {
  .max_accel = 2000,         // 2.0 m/s^2
  .min_accel = -3500,        // -3.5 m/s^2
  .inactive_accel = 0,
};

#define GWM_MSG_STEER_AND_AP_STALK 0xA1
#define GWM_MSG_AUTOPILOT 0x12B
#define GWM_MSG_CAR_OVERALL_SIGNALS2 0x60
#define GWM_MSG_BRAKE 0x137

// TX messages
static const CanMsg GWM_TX_MSGS[] = {
  {GWM_MSG_AUTOPILOT, 0, 8, .check_relay = true},
  {GWM_MSG_AUTOPILOT, 2, 8, .check_relay = false},
};

// GWM uses a custom checksum
static uint8_t gwm_crc_lookup[] = {
  0x00, 0x1D, 0x3A, 0x27, 0x74, 0x69, 0x4E, 0x53, 0xE8, 0xF5, 0xD2, 0xCF, 0x9C, 0x81, 0xA6, 0xBB,
  0xCD, 0xD0, 0xF7, 0xEA, 0xB9, 0xA4, 0x83, 0x9E, 0x25, 0x38, 0x1F, 0x02, 0x51, 0x4C, 0x6B, 0x76
};

static uint32_t gwm_get_checksum(const CANPacket_t *to_push) {
  return GET_BYTE(to_push, 4);
}

static uint32_t gwm_compute_checksum(const CANPacket_t *to_push) {
  uint8_t checksum = 0xFF;
  int len = GET_LEN(to_push);
  for (int i = 0; i < len; i++) {
    if (i == 4) continue;  // Skip checksum byte
    checksum = gwm_crc_lookup[(checksum ^ GET_BYTE(to_push, i)) & 0x1F];
  }
  return checksum;
}

static uint8_t gwm_get_counter(const CANPacket_t *to_push) {
  return (GET_BYTE(to_push, 3) >> 4) & 0xF;
}

static void gwm_rx_hook(const CANPacket_t *to_push) {
  int addr = GET_ADDR(to_push);
  int bus = GET_BUS(to_push);

  // Sample steering torque
  if ((addr == GWM_MSG_STEER_AND_AP_STALK) && (bus == 0)) {
    int torque_driver_new = ((GET_BYTE(to_push, 3) & 0xFF) << 8) | (GET_BYTE(to_push, 4) & 0xFF);
    update_sample(&torque_driver, torque_driver_new);
  }

  // Sample vehicle speed
  if ((addr == 0x103) && (bus == 0)) {
    vehicle_moving = GET_BYTE(to_push, 7) > 0;
  }

  // Check gas/brake pressed
  if ((addr == GWM_MSG_CAR_OVERALL_SIGNALS2) && (bus == 0)) {
    gas_pressed = GET_BYTE(to_push, 9) > 0;
    brake_pressed = GET_BIT(to_push, 86U);
  }

  // Check cruise engaged
  if ((addr == GWM_MSG_AUTOPILOT) && (bus == 0)) {
    bool cruise_engaged = (GET_BYTE(to_push, 2) >> 2) & 0x3;
    pcm_cruise_check(cruise_engaged);
  }

  generic_rx_checks((addr == GWM_MSG_AUTOPILOT) && (bus == 0));
}

static bool gwm_tx_hook(const CANPacket_t *to_send) {
  int tx = 1;
  int addr = GET_ADDR(to_send);
  int bus = GET_BUS(to_send);

  // Check relay malfunction
  if ((addr == GWM_MSG_AUTOPILOT) && (bus == 0)) {
    tx = 0;
  }

  if (tx && (addr == GWM_MSG_AUTOPILOT)) {
    // AP_STATE is at bits 18-19 (byte 2, bits 2-3)
    int steer_req = (GET_BYTE(to_send, 2) >> 2) & 0x3;
    // AP_STEERING_UNDEFINED_SIGNAL1: 11 bits from bit 15 to bit 5
    // Bits 15-8 are in byte 1, bits 7-5 are in byte 0
    int desired_torque = ((GET_BYTE(to_send, 1) & 0xFF) << 3) | ((GET_BYTE(to_send, 0) >> 5) & 0x7);
    desired_torque = to_signed(desired_torque, 11);

        if (steer_torque_cmd_checks(desired_torque, steer_req, GWM_STEERING_LIMITS)) {
      tx = 0;
    }
  }

  return tx;
}

static int gwm_fwd_hook(int bus_num, int addr) {
  int bus_fwd = -1;

  if (bus_num == 0) {
    bus_fwd = 2;  // Forward to camera CAN
  }
  if (bus_num == 2) {
    // Block openpilot actuation messages from camera
    bool is_openpilot_msg = (addr == GWM_MSG_AUTOPILOT);
    if (!is_openpilot_msg) {
      bus_fwd = 0;  // Forward to PT CAN
    }
  }

  return bus_fwd;
}

// RX message checks
static RxCheck gwm_rx_checks[] = {
  {.msg = {{GWM_MSG_STEER_AND_AP_STALK, 0, 8, .frequency = 50U}, { 0 }, { 0 }}},
  {.msg = {{0x103, 0, 8, .frequency = 50U}, { 0 }, { 0 }}},
  {.msg = {{GWM_MSG_CAR_OVERALL_SIGNALS2, 0, 8, .frequency = 50U}, { 0 }, { 0 }}},
  {.msg = {{GWM_MSG_AUTOPILOT, 0, 8, .frequency = 50U}, { 0 }, { 0 }}},
};

const safety_hooks gwm_hooks = {
  .init = gwm_init,
  .rx = gwm_rx_hook,
  .tx = gwm_tx_hook,
  .fwd = gwm_fwd_hook,
  .get_counter = gwm_get_counter,
  .get_checksum = gwm_get_checksum,
  .compute_checksum = gwm_compute_checksum,
};

static safety_config gwm_init(uint16_t param) {
  UNUSED(param);
  return (safety_config){
    .rx_checks = gwm_rx_checks,
    .rx_checks_len = sizeof(gwm_rx_checks) / sizeof(gwm_rx_checks[0]),
    .tx_msgs = GWM_TX_MSGS,
    .tx_msgs_len = sizeof(GWM_TX_MSGS) / sizeof(GWM_TX_MSGS[0]),
    .disable_forwarding = false,
  };
}