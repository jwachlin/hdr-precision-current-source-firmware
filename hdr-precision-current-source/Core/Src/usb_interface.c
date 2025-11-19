/*
 * usb_interface.c
 *
 *  Created on: Nov 18, 2025
 *      Author: jakewachlin
 */


#include "main.h"
#include "usb_device.h"
#include "usb_interface.h"
#include "usbd_cdc_if.h"
#include <string.h>


#define MESSAGE_SIZE				10

static bool usb_recv = false;
static usb_command_t cmd_recv;
static uint8_t usb_tx_buffer[MESSAGE_SIZE+1];
static uint8_t step = 0;

static bool process_byte(uint8_t b)
{

	static uint8_t count = 0;
	static uint8_t chk = 0;

	if(step == 0)
	{
		if(b == 0xAA)
		{
			step++;
			chk = 0;
		}
	}
	else if(step == 1)
	{
		cmd_recv.msg_type = b;
		chk += b;
		step++;
	}
	else if(step == 2)
	{
		cmd_recv.length = b;
		chk += b;
		step++;
		count = 0;
	}
	else if(step == 3)
	{
		cmd_recv.payload[count++] = b;
		chk += b;
		if(count >= cmd_recv.length)
		{
			step++;
		}
	}
	else if(step == 4)
	{
		step = 0;
		if(chk == b)
		{
			return true;
		}
	}
	return false;
}

bool is_usb_recv(usb_command_t * cmd)
{
	if(usb_recv)
	{
		*cmd = cmd_recv;
	}
	bool ret_value = usb_recv;
	usb_recv = false; // Reset once got

	return ret_value;
}

void usb_handle_recv(uint8_t * buf, uint32_t len)
{
	// ISR
	int i;
	step = 0;
	for(i = 0; i < len; i++)
	{
		uint8_t b = *(buf+i);
		if(process_byte(b))
		{
			usb_recv = true;
		}
	}
}


void transmit_config_value(uint8_t index, float config_value)
{
	usb_tx_buffer[0] = 0xAA;
	usb_tx_buffer[1] = CONFIG_RESPONSE;
	usb_tx_buffer[2] = index;
	memcpy(&usb_tx_buffer[3], &config_value, 4);
	uint8_t chk = 0;
	int32_t i;
	for(i = 1; i < 7; i++)
	{
		chk += usb_tx_buffer[i];
	}
	usb_tx_buffer[7] = chk;
	CDC_Transmit_HS(usb_tx_buffer, 8);
}
