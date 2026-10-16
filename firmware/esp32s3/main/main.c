/*
 * LEGACY ParrotCore PWM body controller v0.2 for ESP32-S3.
 *
 * v0.5.1 NOTE: Parrot V1 now selects Feetech half-duplex TTL smart servos.
 * This MCPWM implementation is retained only as a generic/PWM bench reference.
 * See firmware/README_V051.md and src/parrotcore/feetech_protocol.py.
 *
 * SAFETY MODEL
 * - Servo rail defaults OFF.
 * - Physical E-stop input is active-low and latches shutdown.
 * - Brain traffic must refresh a watchdog; timeout disables servo rail.
 * - Joint commands are range-checked on the MCU even if Linux already checked them.
 * - Servo PWM uses two 50 Hz MCPWM timers and four operators for eight channels.
 *
 * Calibrate pulse endpoints on a disconnected/lightweight mechanism before enabling
 * a complete body. Reference pin numbers are prototypes, not a production PCB layout.
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/uart.h"
#include "driver/mcpwm_prelude.h"
#include "esp_err.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "cJSON.h"

#define UART_PORT UART_NUM_1
#define UART_TX_GPIO 17
#define UART_RX_GPIO 18
#define UART_BAUD 115200
#define ESTOP_GPIO 12
#define SERVO_ENABLE_GPIO 13

#define SERVO_COUNT 8
#define SERVO_TIMEBASE_HZ 1000000
#define SERVO_PERIOD_US 20000
#define WATCHDOG_US 750000
#define RX_LINE_MAX 512

static const char *TAG = "parrotcore_body";

typedef struct {
    int gpio;
    float logical_min;
    float logical_max;
    uint32_t pulse_min_us;
    uint32_t pulse_max_us;
    uint32_t home_us;
    mcpwm_cmpr_handle_t comparator;
    mcpwm_gen_handle_t generator;
} servo_t;

static servo_t servos[SERVO_COUNT] = {
    {4,  -60, 60, 700, 2300, 1500, NULL, NULL},
    {5,  -35, 40, 850, 2150, 1500, NULL, NULL},
    {6,    0, 35, 950, 1850,  950, NULL, NULL},
    {7,    0, 75, 700, 2300,  700, NULL, NULL},
    {8,    0, 75, 700, 2300,  700, NULL, NULL},
    {9,  -20, 35, 900, 2100, 1350, NULL, NULL},
    {10,   0,100, 800, 2200,  800, NULL, NULL},
    {11, -15, 20,1000, 2000, 1450, NULL, NULL},
};

static mcpwm_timer_handle_t timers[2] = {NULL, NULL};
static bool estop_latched = true;
static int64_t last_brain_rx_us = 0;
static uint32_t tx_seq = 0;

static void servo_power(bool enabled)
{
    gpio_set_level(SERVO_ENABLE_GPIO, enabled ? 1 : 0);
}

static bool physical_estop_active(void)
{
    return gpio_get_level(ESTOP_GPIO) == 0;
}

static void send_json(const char *type, const char *extra_json)
{
    char buf[384];
    tx_seq++;
    if (extra_json && extra_json[0]) {
        snprintf(buf, sizeof(buf), "{\"v\":0,\"seq\":%lu,\"type\":\"%s\",%s}\n",
                 (unsigned long)tx_seq, type, extra_json);
    } else {
        snprintf(buf, sizeof(buf), "{\"v\":0,\"seq\":%lu,\"type\":\"%s\"}\n",
                 (unsigned long)tx_seq, type);
    }
    uart_write_bytes(UART_PORT, buf, strlen(buf));
}

static uint32_t logical_to_pulse(int id, float value)
{
    servo_t *s = &servos[id];
    float ratio = (value - s->logical_min) / (s->logical_max - s->logical_min);
    float pulse = s->pulse_min_us + ratio * (float)(s->pulse_max_us - s->pulse_min_us);
    if (pulse < s->pulse_min_us) pulse = s->pulse_min_us;
    if (pulse > s->pulse_max_us) pulse = s->pulse_max_us;
    return (uint32_t)lroundf(pulse);
}

static esp_err_t set_joint(int id, float value)
{
    if (id < 0 || id >= SERVO_COUNT) return ESP_ERR_INVALID_ARG;
    servo_t *s = &servos[id];
    if (value < s->logical_min || value > s->logical_max) return ESP_ERR_INVALID_ARG;
    return mcpwm_comparator_set_compare_value(s->comparator, logical_to_pulse(id, value));
}

static void init_gpio(void)
{
    gpio_config_t out = {
        .pin_bit_mask = 1ULL << SERVO_ENABLE_GPIO,
        .mode = GPIO_MODE_OUTPUT,
    };
    ESP_ERROR_CHECK(gpio_config(&out));
    servo_power(false);

    gpio_config_t in = {
        .pin_bit_mask = 1ULL << ESTOP_GPIO,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&in));
}

static void init_uart(void)
{
    uart_config_t cfg = {
        .baud_rate = UART_BAUD,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    ESP_ERROR_CHECK(uart_driver_install(UART_PORT, 2048, 0, 0, NULL, 0));
    ESP_ERROR_CHECK(uart_param_config(UART_PORT, &cfg));
    ESP_ERROR_CHECK(uart_set_pin(UART_PORT, UART_TX_GPIO, UART_RX_GPIO, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));
}

static void init_mcpwm(void)
{
    for (int group = 0; group < 2; ++group) {
        mcpwm_timer_config_t timer_cfg = {
            .group_id = group,
            .clk_src = MCPWM_TIMER_CLK_SRC_DEFAULT,
            .resolution_hz = SERVO_TIMEBASE_HZ,
            .period_ticks = SERVO_PERIOD_US,
            .count_mode = MCPWM_TIMER_COUNT_MODE_UP,
        };
        ESP_ERROR_CHECK(mcpwm_new_timer(&timer_cfg, &timers[group]));
    }

    for (int op_index = 0; op_index < 4; ++op_index) {
        int group = (op_index < 3) ? 0 : 1;
        mcpwm_oper_handle_t oper = NULL;
        mcpwm_operator_config_t oper_cfg = {.group_id = group};
        ESP_ERROR_CHECK(mcpwm_new_operator(&oper_cfg, &oper));
        ESP_ERROR_CHECK(mcpwm_operator_connect_timer(oper, timers[group]));

        for (int gen_index = 0; gen_index < 2; ++gen_index) {
            int id = op_index * 2 + gen_index;
            mcpwm_comparator_config_t cmp_cfg = {.flags.update_cmp_on_tez = true};
            ESP_ERROR_CHECK(mcpwm_new_comparator(oper, &cmp_cfg, &servos[id].comparator));

            mcpwm_generator_config_t gen_cfg = {.gen_gpio_num = servos[id].gpio};
            ESP_ERROR_CHECK(mcpwm_new_generator(oper, &gen_cfg, &servos[id].generator));

            ESP_ERROR_CHECK(mcpwm_comparator_set_compare_value(servos[id].comparator, servos[id].home_us));
            ESP_ERROR_CHECK(mcpwm_generator_set_action_on_timer_event(
                servos[id].generator,
                MCPWM_GEN_TIMER_EVENT_ACTION(MCPWM_TIMER_DIRECTION_UP, MCPWM_TIMER_EVENT_EMPTY, MCPWM_GEN_ACTION_HIGH)));
            ESP_ERROR_CHECK(mcpwm_generator_set_action_on_compare_event(
                servos[id].generator,
                MCPWM_GEN_COMPARE_EVENT_ACTION(MCPWM_TIMER_DIRECTION_UP, servos[id].comparator, MCPWM_GEN_ACTION_LOW)));
        }
    }

    for (int group = 0; group < 2; ++group) {
        ESP_ERROR_CHECK(mcpwm_timer_enable(timers[group]));
        ESP_ERROR_CHECK(mcpwm_timer_start_stop(timers[group], MCPWM_TIMER_START_NO_STOP));
    }
}

static void fault(const char *code, const char *detail)
{
    char extra[256];
    snprintf(extra, sizeof(extra), "\"code\":\"%s\",\"detail\":\"%s\"", code, detail);
    send_json("fault", extra);
}

static void handle_message(const char *line)
{
    cJSON *root = cJSON_Parse(line);
    if (!root) {
        fault("BAD_JSON", "parse failed");
        return;
    }

    cJSON *v = cJSON_GetObjectItem(root, "v");
    cJSON *type = cJSON_GetObjectItem(root, "type");
    if (!cJSON_IsNumber(v) || v->valueint != 0 || !cJSON_IsString(type)) {
        cJSON_Delete(root);
        fault("BAD_MESSAGE", "version/type invalid");
        return;
    }

    last_brain_rx_us = esp_timer_get_time();

    if (strcmp(type->valuestring, "ping") == 0) {
        send_json("pong", estop_latched ? "\"estop\":true" : "\"estop\":false");
    } else if (strcmp(type->valuestring, "estop") == 0) {
        cJSON *active = cJSON_GetObjectItem(root, "active");
        if (!cJSON_IsBool(active)) {
            fault("BAD_ESTOP", "active must be boolean");
        } else if (cJSON_IsTrue(active)) {
            estop_latched = true;
            servo_power(false);
            send_json("ack", "\"command\":\"estop\"");
        } else if (!physical_estop_active()) {
            estop_latched = false;
            servo_power(true);
            send_json("ack", "\"command\":\"reset_estop\"");
        } else {
            fault("ESTOP_ACTIVE", "physical estop still active");
        }
    } else if (strcmp(type->valuestring, "joint") == 0) {
        cJSON *id = cJSON_GetObjectItem(root, "id");
        cJSON *value = cJSON_GetObjectItem(root, "value");
        if (estop_latched || physical_estop_active()) {
            fault("ESTOP", "motion rejected");
        } else if (!cJSON_IsNumber(id) || !cJSON_IsNumber(value) ||
                   set_joint(id->valueint, (float)value->valuedouble) != ESP_OK) {
            fault("BAD_JOINT", "invalid id or value");
        } else {
            servo_power(true);
            send_json("ack", "\"command\":\"joint\"");
        }
    } else if (strcmp(type->valuestring, "pose") == 0) {
        cJSON *values = cJSON_GetObjectItem(root, "values");
        bool ok = cJSON_IsObject(values) && !estop_latched && !physical_estop_active();
        if (ok) {
            cJSON *item = NULL;
            cJSON_ArrayForEach(item, values) {
                int id = atoi(item->string);
                if (!cJSON_IsNumber(item) || set_joint(id, (float)item->valuedouble) != ESP_OK) {
                    ok = false;
                    break;
                }
            }
        }
        if (ok) {
            servo_power(true);
            send_json("ack", "\"command\":\"pose\"");
        } else {
            fault("BAD_POSE", "invalid pose or safety state");
        }
    } else {
        fault("UNKNOWN_COMMAND", type->valuestring);
    }

    cJSON_Delete(root);
}

static void safety_tick(void)
{
    if (physical_estop_active()) {
        if (!estop_latched) fault("ESTOP", "physical estop activated");
        estop_latched = true;
        servo_power(false);
        return;
    }
    if (!estop_latched && (esp_timer_get_time() - last_brain_rx_us) > WATCHDOG_US) {
        estop_latched = true;
        servo_power(false);
        fault("WATCHDOG", "brain heartbeat expired");
    }
}

void app_main(void)
{
    init_gpio();
    init_uart();
    init_mcpwm();

    last_brain_rx_us = esp_timer_get_time();
    ESP_LOGI(TAG, "ParrotCore body controller v0.2 ready; servo rail OFF until estop reset");
    send_json("boot", "\"servo_power\":false,\"estop\":true");

    char line[RX_LINE_MAX];
    size_t used = 0;
    uint8_t ch;

    while (1) {
        int n = uart_read_bytes(UART_PORT, &ch, 1, pdMS_TO_TICKS(10));
        if (n == 1) {
            if (ch == '\n') {
                line[used] = '\0';
                if (used) handle_message(line);
                used = 0;
            } else if (ch != '\r') {
                if (used < sizeof(line) - 1) line[used++] = (char)ch;
                else {
                    used = 0;
                    fault("LINE_TOO_LONG", "input discarded");
                }
            }
        }
        safety_tick();
    }
}
