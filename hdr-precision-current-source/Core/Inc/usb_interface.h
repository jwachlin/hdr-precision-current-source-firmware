/*
 * usb_interface.h
 *
 *  Created on: Nov 18, 2025
 *      Author: jakewachlin
 */

#ifndef INC_USB_INTERFACE_H_
#define INC_USB_INTERFACE_H_

#include <stdbool.h>

typedef enum
{
	SET_CURRENT = 0,
	SET_CONFIG = 1,
	GET_CONFIG = 2,
	CONFIG_RESPONSE = 3,
	SET_SCALE = 4,
	CURRENT_SET = 5
} MESSAGE_TYPE_t;

typedef struct
{
	MESSAGE_TYPE_t msg_type;
	uint8_t length;
	uint8_t payload[256];
} usb_command_t;

bool is_usb_recv(usb_command_t * cmd);
void usb_handle_recv(uint8_t * buf, uint32_t len);
void transmit_config_value(uint8_t index, float config_value);
void transmit_current_setting(float current_setting_mA);


#endif /* INC_USB_INTERFACE_H_ */
