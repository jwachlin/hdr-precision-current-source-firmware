/*
 * dac80501.c
 *
 *  Created on: Nov 18, 2025
 *      Author: jakewachlin
 */



#include "dac80501.h"

/* Private defines */
#define DAC80501_I2C_TIMEOUT    100

/* Private function prototypes - none needed for I2C only */

/**
 * @brief Initialize DAC80501 with I2C interface
 */
HAL_StatusTypeDef DAC80501_Init(DAC80501_Handle_t *hdac, I2C_HandleTypeDef *hi2c,
                                 uint8_t i2c_addr, uint16_t vref_mv) {
    if (hdac == NULL || hi2c == NULL) {
        return HAL_ERROR;
    }

    hdac->hi2c = hi2c;
    hdac->i2c_address = i2c_addr << 1; // HAL expects 8-bit address
    hdac->vref_mv = vref_mv;
    hdac->gain_2x = false;

    HAL_Delay(1);

    // Verify device ID
    uint16_t device_id = 0;
    if (DAC80501_GetDeviceID(hdac, &device_id) != HAL_OK) {
        return HAL_ERROR;
    }

    if (device_id != DAC80501_DEVICE_ID) {
        return HAL_ERROR;
    }

    // Configure DAC: power up both reference and DAC
    if (DAC80501_WriteRegister(hdac, DAC80501_REG_CONFIG, 0x0000) != HAL_OK) {
        return HAL_ERROR;
    }

    // Set gain to 1x by default
    if (DAC80501_SetGain(hdac, false) != HAL_OK) {
        return HAL_ERROR;
    }

    // Set DAC to mid-scale
    if (DAC80501_SetValue(hdac, 0x8000) != HAL_OK) {
        return HAL_ERROR;
    }

    return HAL_OK;
}

/**
 * @brief Write to a DAC80501 register
 */
HAL_StatusTypeDef DAC80501_WriteRegister(DAC80501_Handle_t *hdac, uint8_t reg_addr, uint16_t data) {
    if (hdac == NULL) {
        return HAL_ERROR;
    }

    uint8_t tx_buffer[3];
    tx_buffer[0] = reg_addr & 0x7F; // Ensure write bit is 0
    tx_buffer[1] = (data >> 8) & 0xFF;
    tx_buffer[2] = data & 0xFF;

    return HAL_I2C_Master_Transmit(hdac->hi2c, hdac->i2c_address, tx_buffer, 3, DAC80501_I2C_TIMEOUT);
}

/**
 * @brief Read from a DAC80501 register
 */
HAL_StatusTypeDef DAC80501_ReadRegister(DAC80501_Handle_t *hdac, uint8_t reg_addr, uint16_t *data) {
    if (hdac == NULL || data == NULL) {
        return HAL_ERROR;
    }

    uint8_t tx_buffer[1];
    uint8_t rx_buffer[2];
    HAL_StatusTypeDef status;

    tx_buffer[0] = reg_addr | 0x80; // Set read bit

    // Write register address, then read data
    status = HAL_I2C_Master_Transmit(hdac->hi2c, hdac->i2c_address, tx_buffer, 1, DAC80501_I2C_TIMEOUT);
    if (status == HAL_OK) {
        status = HAL_I2C_Master_Receive(hdac->hi2c, hdac->i2c_address, rx_buffer, 2, DAC80501_I2C_TIMEOUT);
    }

    if (status == HAL_OK) {
        *data = ((uint16_t)rx_buffer[0] << 8) | rx_buffer[1];
    }

    return status;
}

/**
 * @brief Read device ID
 */
HAL_StatusTypeDef DAC80501_GetDeviceID(DAC80501_Handle_t *hdac, uint16_t *device_id) {
    return DAC80501_ReadRegister(hdac, DAC80501_REG_DEVID, device_id);
}

/**
 * @brief Set DAC output value (16-bit)
 */
HAL_StatusTypeDef DAC80501_SetValue(DAC80501_Handle_t *hdac, uint16_t value) {
    return DAC80501_WriteRegister(hdac, DAC80501_REG_DAC, value);
}

/**
 * @brief Set DAC output voltage in millivolts
 */
HAL_StatusTypeDef DAC80501_SetVoltage(DAC80501_Handle_t *hdac, uint16_t voltage_mv) {
    if (hdac == NULL) {
        return HAL_ERROR;
    }

    // Calculate maximum output voltage based on gain
    uint32_t max_voltage = hdac->vref_mv;
    if (hdac->gain_2x) {
        max_voltage *= 2;
    }

    // Clamp voltage to maximum
    if (voltage_mv > max_voltage) {
        voltage_mv = max_voltage;
    }

    // Calculate DAC value: DAC = (Vout * 65535) / Vmax
    uint32_t dac_value = ((uint32_t)voltage_mv * 65535) / max_voltage;

    return DAC80501_SetValue(hdac, (uint16_t)dac_value);
}

/**
 * @brief Set gain (1x or 2x)
 */
HAL_StatusTypeDef DAC80501_SetGain(DAC80501_Handle_t *hdac, bool gain_2x) {
    if (hdac == NULL) {
        return HAL_ERROR;
    }

    hdac->gain_2x = gain_2x;
    uint16_t gain_value = gain_2x ? DAC80501_GAIN_2X : DAC80501_GAIN_1X;

    return DAC80501_WriteRegister(hdac, DAC80501_REG_GAIN, gain_value);
}

/**
 * @brief Power down/up the DAC
 */
HAL_StatusTypeDef DAC80501_PowerDown(DAC80501_Handle_t *hdac, bool powerdown) {
    if (hdac == NULL) {
        return HAL_ERROR;
    }

    uint16_t config_value = 0x0000;

    if (powerdown) {
        config_value = DAC80501_CONFIG_DAC_PWDWN | DAC80501_CONFIG_REF_PWDWN;
    }

    return DAC80501_WriteRegister(hdac, DAC80501_REG_CONFIG, config_value);
}

/**
 * @brief Perform software reset
 */
HAL_StatusTypeDef DAC80501_SoftwareReset(DAC80501_Handle_t *hdac) {
    if (hdac == NULL) {
        return HAL_ERROR;
    }

    // Write reset code to TRIGGER register
    HAL_StatusTypeDef status = DAC80501_WriteRegister(hdac, DAC80501_REG_TRIGGER, 0x000A);

    if (status == HAL_OK) {
        HAL_Delay(1); // Wait for reset to complete
    }

    return status;
}
