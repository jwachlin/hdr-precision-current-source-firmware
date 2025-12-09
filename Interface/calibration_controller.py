import metashunt_v2 as ms2
import HDRPrecisionCurrentSupply as pcs
import json
import copy
import time
import numpy as np

pre_cal_filename = "pre_cal_cfg.json"
post_cal_filename = "post_cal_cfg.json"

def try_configure(filename, ms, num_attempts):
    for i in range(num_attempts):
        if(ms.configure(config_file_name=filename)):
            break

if __name__ == "__main__":

    print("Plug in MetaShunt and supply and press enter")
    input()
    this_ms2 = ms2.MetaShuntV2()
    this_ms2.connect()

    this_pcs = pcs.HDRPrecisionCurrentSupply(supply_type=pcs.CurrentSupplyType.FIXED_REFERENCE)
    this_pcs.connect()
    this_pcs.command_stage(7)

    config_data = {}
    config_data["R19"] = this_ms2.get_config_param("R19")
    config_data["R17"] = this_ms2.get_config_param("R17")
    config_data["R15"] = this_ms2.get_config_param("R15")
    config_data["R13"] = this_ms2.get_config_param("R13")
    config_data["R11"] = this_ms2.get_config_param("R11")
    config_data["R9"] = this_ms2.get_config_param("R9")
    config_data["R2"] = this_ms2.get_config_param("R2")
    config_data["R1"] = this_ms2.get_config_param("R1")
    config_data["R_FET"] = this_ms2.get_config_param("R_FET")

    with open(pre_cal_filename, 'w') as outf:
        json.dump(config_data, outf)

    # Move through all stages, take measurement, and update calibration
    num_retries = 5
    expected_current_stages_ma = np.flip(np.array([0.0003, 0.0033, 0.0300, 0.300, 3.00, 30.0, 234.0, 389.0]))
    stages = range(7, -1, -1)
    pre_cal_avg_ma = []
    truth_ma = []
    errors = []
    ratios = []
    for stage in stages:
        for attempt in range(num_retries):
            time.sleep(0.1)
            this_pcs.command_stage(stage)
            current_commanded_ma = this_pcs.get_current_setting_ma()
            if current_commanded_ma is not None:
                if (np.abs(current_commanded_ma - expected_current_stages_ma[stage]) / expected_current_stages_ma[stage]) < 0.05:
                    print("Set stage correctly for stage {0}, current {1}".format(stage, current_commanded_ma))
                    truth_ma.append(current_commanded_ma)
                    break
        
        time.sleep(0.01)
        this_ms2.measure(0.5) # Dummy measure first
        this_ms2.clear_measurements()
        this_ms2.measure(4.0)
        (num_meas, avg_ma, std_dev_ma) = this_ms2.measurement_stats()
        meas = this_ms2.get_measurements()
        pre_cal_avg_ma.append(avg_ma)

        error = (current_commanded_ma-avg_ma)/current_commanded_ma
        print("Currently, measurement at stage {0} is off by {1:.2f} percent from {2:.6f}mA".format(stage, 100.0*error, current_commanded_ma))
        errors.append(error)
        ratios.append(avg_ma / current_commanded_ma)

    # End at low current
    this_pcs.command_stage(7)
    this_pcs.command_stage(7)
    this_pcs.command_stage(7)

    # Compute calibration
    updated_config_data = copy.copy(config_data)

    # First, compute what actual r_eff was
    r_eff_current = np.zeros((8,1))
    r_eff_current[0] = config_data["R19"]
    r_eff_current[1] = 1.0/((1.0/(config_data["R17"]+config_data["R_FET"])) + (1.0/r_eff_current[0]))
    r_eff_current[2] = 1.0/((1.0/(config_data["R15"]+config_data["R_FET"])) + (1.0/r_eff_current[1]))
    r_eff_current[3] = 1.0/((1.0/(config_data["R13"]+config_data["R_FET"])) + (1.0/r_eff_current[2]))
    r_eff_current[4] = 1.0/((1.0/(config_data["R11"]+config_data["R_FET"])) + (1.0/r_eff_current[3]))
    r_eff_current[5] = 1.0/((1.0/(config_data["R9"]+config_data["R_FET"])) + (1.0/r_eff_current[4]))
    r_eff_current[6] = 1.0/((1.0/(config_data["R2"]+config_data["R_FET"])) + (1.0/r_eff_current[5]))
    r_eff_current[7] = 1.0/((1.0/(config_data["R1"]+config_data["R_FET"])) + (1.0/r_eff_current[6]))

    # Then compute what r_eff should be
    r_eff_actual = np.array([r_eff_current[i] * ratio for i, ratio in enumerate(ratios)])

    # Then, compute configs based on this
    # At stage 7, only R19
    r_eff_updated = np.zeros((8,1))
    updated_config_data["R19"] = ratios[0] * config_data["R19"]
    r_eff_updated[0] = updated_config_data["R19"]
    
    # Stage 6
    updated_config_data["R17"] = (( 1.0 / ((1.0 / r_eff_actual[1]) - (1.0 / r_eff_updated[0]))) - updated_config_data["R_FET"]).item()
    r_eff_updated[1] = 1.0/((1.0/(updated_config_data["R17"]+updated_config_data["R_FET"])) + (1.0/r_eff_updated[0]))

    # Stage 5
    updated_config_data["R15"] = (( 1.0 / ((1.0 / r_eff_actual[2]) - (1.0 / r_eff_updated[1]))) - updated_config_data["R_FET"]).item()
    r_eff_updated[2] = 1.0/((1.0/(updated_config_data["R15"]+updated_config_data["R_FET"])) + (1.0/r_eff_updated[1]))

    # Stage 4
    updated_config_data["R13"] = (( 1.0 / ((1.0 / r_eff_actual[3]) - (1.0 / r_eff_updated[2]))) - updated_config_data["R_FET"]).item()
    r_eff_updated[3] = 1.0/((1.0/(updated_config_data["R13"]+updated_config_data["R_FET"])) + (1.0/r_eff_updated[2]))

    # Stage 3
    updated_config_data["R11"] = (( 1.0 / ((1.0 / r_eff_actual[4]) - (1.0 / r_eff_updated[3]))) - updated_config_data["R_FET"]).item()
    r_eff_updated[4] = 1.0/((1.0/(updated_config_data["R11"]+updated_config_data["R_FET"])) + (1.0/r_eff_updated[3]))

    # Stage 2
    updated_config_data["R9"] = (( 1.0 / ((1.0 / r_eff_actual[5]) - (1.0 / r_eff_updated[4]))) - updated_config_data["R_FET"]).item()
    r_eff_updated[5] = 1.0/((1.0/(updated_config_data["R9"]+updated_config_data["R_FET"])) + (1.0/r_eff_updated[4]))

    # Stage 1
    updated_config_data["R2"] = (( 1.0 / ((1.0 / r_eff_actual[6]) - (1.0 / r_eff_updated[5]))) - updated_config_data["R_FET"]).item()
    r_eff_updated[6] = 1.0/((1.0/(updated_config_data["R2"]+updated_config_data["R_FET"])) + (1.0/r_eff_updated[5]))

    # Stage 0
    updated_config_data["R1"] = (( 1.0 / ((1.0 / r_eff_actual[7]) - (1.0 / r_eff_updated[6]))) - updated_config_data["R_FET"]).item()
    r_eff_updated[7] = 1.0/((1.0/(updated_config_data["R1"]+updated_config_data["R_FET"])) + (1.0/r_eff_updated[6]))

    with open(post_cal_filename, 'w') as outf:
        json.dump(updated_config_data, outf)

    try_configure(filename=post_cal_filename, ms=this_ms2, num_attempts=3)

    this_ms2.disconnect()
    this_pcs.disconnect()

    print("Now checking calibration, unplug supply then MetaShunt. Then plug in MetaShunt and plug in supply")
    input()

    this_pcs.connect()
    this_ms2.connect()

    for stage in stages:
        for attempt in range(num_retries):
            time.sleep(0.1)
            this_pcs.command_stage(stage)
            current_commanded_ma = this_pcs.get_current_setting_ma()
            if current_commanded_ma is not None:
                if (np.abs(current_commanded_ma - expected_current_stages_ma[stage]) / expected_current_stages_ma[stage]) < 0.05:
                    print("Set stage correctly for stage {0}, current {1}".format(stage, current_commanded_ma))
                    truth_ma.append(current_commanded_ma)
                    break
        
        time.sleep(0.01)
        this_ms2.measure(0.5) # Dummy measure first
        this_ms2.clear_measurements()
        this_ms2.measure(4.0)
        (num_meas, avg_ma, std_dev_ma) = this_ms2.measurement_stats()
        error = (current_commanded_ma-avg_ma)/current_commanded_ma
        print("After calibration, measurement at stage {0} is off by {1:.2f} percent from {2:.6f}mA".format(stage, 100.0*error, current_commanded_ma))

    # End at low current
    this_pcs.command_stage(7)
    this_pcs.command_stage(7)
    this_pcs.command_stage(7)

    this_ms2.disconnect()
    this_pcs.disconnect()
