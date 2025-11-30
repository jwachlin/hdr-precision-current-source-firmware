/*
 * dac80501.h
 *
 *  Created on: Nov 18, 2025
 *      Author: jakewachlin
 */

#ifndef INC_DAC80501_H_
#define INC_DAC80501_H_


#include "stm32l4xx_hal.h"
#include <stdint.h>
#include <stdbool.h>

/* DAC80501 Register Addresses */
#define DAC80501_REG_NOOP       0x00
#define DAC80501_REG_DEVID      0x01
#define DAC80501_REG_SYNC       0x02
#define DAC80501_REG_CONFIG     0x03
#define DAC80501_REG_GAIN       0x04
#define DAC80501_REG_TRIGGER    0x05
#define DAC80501_REG_STATUS     0x07
#define DAC80501_REG_DAC        0x08

/* Device ID */
#define DAC80501_DEVICE_ID      0x0115

/* Configuration Register Bits */
#define DAC80501_CONFIG_REF_PWDWN   (1 << 0)  // Reference power down
#define DAC80501_CONFIG_DAC_PWDWN   (1 << 1)  // DAC power down

/* Gain Register Values */
#define DAC80501_GAIN_1X        0x0000  // Reference divide by 1
#define DAC80501_GAIN_2X        0x0001  // Reference divide by 2

/* Status Register Bits */
#define DAC80501_STATUS_REF_ALARM   (1 << 0)

/* DAC80501 Handle Structure */
typedef struct {
    I2C_HandleTypeDef *hi2c;      // I2C handle
    uint8_t i2c_address;          // I2C address
    uint16_t vref_mv;             // Reference voltage in mV
    bool gain_2x;                 // Gain setting (false = 1x, true = 2x)
} DAC80501_Handle_t;

/* Function Prototypes */

/**
 * @brief Initialize DAC80501 with I2C interface
 * @param hdac: Pointer to DAC80501 handle structure
 * @param hi2c: Pointer to I2C handle
 * @param i2c_addr: I2C device address (7-bit: 0x48 or 0x49)
 * @param vref_mv: Reference voltage in millivolts
 * @retval HAL_StatusTypeDef
 */
HAL_StatusTypeDef DAC80501_Init(DAC80501_Handle_t *hdac, I2C_HandleTypeDef *hi2c,
                                 uint8_t i2c_addr, uint16_t vref_mv);

/**
 * @brief Write to a DAC80501 register
 * @param hdac: Pointer to DAC80501 handle structure
 * @param reg_addr: Register address
 * @param data: 16-bit data to write
 * @retval HAL_StatusTypeDef
 */
HAL_StatusTypeDef DAC80501_WriteRegister(DAC80501_Handle_t *hdac, uint8_t reg_addr, uint16_t data);

/**
 * @brief Read from a DAC80501 register
 * @param hdac: Pointer to DAC80501 handle structure
 * @param reg_addr: Register address
 * @param data: Pointer to store read data
 * @retval HAL_StatusTypeDef
 */
HAL_StatusTypeDef DAC80501_ReadRegister(DAC80501_Handle_t *hdac, uint8_t reg_addr, uint16_t *data);

/**
 * @brief Read device ID
 * @param hdac: Pointer to DAC80501 handle structure
 * @param device_id: Pointer to store device ID
 * @retval HAL_StatusTypeDef
 */
HAL_StatusTypeDef DAC80501_GetDeviceID(DAC80501_Handle_t *hdac, uint16_t *device_id);

/**
 * @brief Set DAC output value (16-bit)
 * @param hdac: Pointer to DAC80501 handle structure
 * @param value: 16-bit DAC value (0-65535)
 * @retval HAL_StatusTypeDef
 */
HAL_StatusTypeDef DAC80501_SetValue(DAC80501_Handle_t *hdac, uint16_t value);

/**
 * @brief Set DAC output voltage in millivolts
 * @param hdac: Pointer to DAC80501 handle structure
 * @param voltage_mv: Desired output voltage in millivolts
 * @retval HAL_StatusTypeDef
 */
HAL_StatusTypeDef DAC80501_SetVoltage(DAC80501_Handle_t *hdac, uint16_t voltage_mv);

/**
 * @brief Set gain (1x or 2x)
 * @param hdac: Pointer to DAC80501 handle structure
 * @param gain_2x: false for 1x gain, true for 2x gain
 * @retval HAL_StatusTypeDef
 */
HAL_StatusTypeDef DAC80501_SetGain(DAC80501_Handle_t *hdac, bool gain_2x);

/**
 * @brief Power down/up the DAC
 * @param hdac: Pointer to DAC80501 handle structure
 * @param powerdown: true to power down, false to power up
 * @retval HAL_StatusTypeDef
 */
HAL_StatusTypeDef DAC80501_PowerDown(DAC80501_Handle_t *hdac, bool powerdown);

/**
 * @brief Perform software reset
 * @param hdac: Pointer to DAC80501 handle structure
 * @retval HAL_StatusTypeDef
 */
HAL_StatusTypeDef DAC80501_SoftwareReset(DAC80501_Handle_t *hdac);


#endif /* INC_DAC80501_H_ */
