import metashunt_v2 as ms2
import HDRPrecisionCurrentSupply as pcs
import json
import copy
import time
import matplotlib.pyplot as plt
import numpy as np



def try_measure(this_pcs, this_ms2, command_ma):
    time.sleep(0.1)
    this_pcs.command_current_ma(command_ma)
    current_command_actual_ma = this_pcs.get_current_setting_ma()
    if current_command_actual_ma is not None and ( np.abs((command_ma - current_command_actual_ma) / command_ma) < 0.01):
        time.sleep(0.01)
        this_ms2.measure(0.5) # Dummy measure first
        this_ms2.clear_measurements()
        this_ms2.measure(1.0)
        (num_meas, avg_ma, std_dev_ma) = this_ms2.measurement_stats()
        if avg_ma is not None:
            return (current_command_actual_ma, num_meas, avg_ma, std_dev_ma)
        else:
            return (None, None, None, None)
    else:
        return (None, None, None, None)

if __name__ == "__main__":

    num_levels = 75
    current_commands_ma = np.geomspace(0.00005, 250.0, num=num_levels, endpoint=True)
    current_commands_actual_ma = np.zeros(num_levels)
    current_measured_ma = np.zeros(num_levels)
    error_pct = np.zeros(num_levels)
    error_2sigma_pct = np.zeros(num_levels)

    print("Plug in MetaShunt and supply and press enter")
    input()
    this_ms2 = ms2.MetaShuntV2()
    this_ms2.connect()

    this_pcs = pcs.HDRPrecisionCurrentSupply(supply_type=pcs.CurrentSupplyType.ADJUSTABLE_REFERENCE)
    this_pcs.connect()

    for index, command_ma in enumerate(current_commands_ma):
        for attempt in range(3):
            (current_command_actual_ma, num_meas, avg_ma, std_dev_ma) = try_measure(this_pcs=this_pcs, this_ms2=this_ms2, command_ma=command_ma)
            if avg_ma is not None:
                current_commands_actual_ma[index] = current_command_actual_ma
                current_measured_ma[index] = avg_ma
                error_pct[index] = 100.0 * (current_measured_ma[index] - current_commands_actual_ma[index]) / current_commands_actual_ma[index]
                print("Currently, measurement at index {0} is off by {1:.5f} percent from {2:.6f}mA".format(index, error_pct[index], current_measured_ma[index]))
                if current_measured_ma[index] > current_commands_actual_ma[index]:
                    current_meas_2sigma_ma = avg_ma + 2.0*std_dev_ma
                    error_2sigma_pct[index] = 100.0 * (current_meas_2sigma_ma - current_commands_actual_ma[index]) / current_commands_actual_ma[index]
                else:
                    current_meas_2sigma_ma = avg_ma - 2.0*std_dev_ma
                    error_2sigma_pct[index] = 100.0 * (current_meas_2sigma_ma - current_commands_actual_ma[index]) / current_commands_actual_ma[index]
                break

    # End at low current
    this_pcs.command_current_ma(0.01)
    this_pcs.command_current_ma(0.01)
    this_pcs.command_current_ma(0.01)

    # Disconnect
    this_ms2.disconnect()
    this_pcs.disconnect()

    print(current_commands_actual_ma)
    print(error_pct)
    print(error_2sigma_pct)

    # Plots
    fig, ax = plt.subplots()
    ax.semilogx(current_commands_actual_ma*0.001, error_pct, '.-',label='Error of Mean')
    ax.semilogx(current_commands_actual_ma*0.001, error_2sigma_pct, '.-',label='Error of Mean + 2 Sigma')

    ax.set(xlabel='Current Supply, A', ylabel='Error, %',
        title='MetaShunt V2 Accuracy vs. Current Supply')
    ax.legend()
    ax.minorticks_on()
    ax.grid(which='both')

    plt.show()
