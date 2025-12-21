import numpy as np
import matplotlib.pyplot as plt

shunt_accuracy_percent = 0.1 # All shunt resistors 0.1%
fixed_ref_accuracy_percent = 0.2
fixed_ref_voltage = 3.0
dac_tue_fsr_percent = 0.06

ad8603_offset_voltages = 0.00005
ad8276_offset_voltage = 0.0005
ad8276_gain_error_percent = 0.05

r_fet_assumed_ohm = 0.048
r_fet_variability_ohm = 0.022

variable_reference_voltage_max = 2.5
variable_reference_v_levels = np.linspace(0.1, 2.5, 10)
num_variable_ref_v_levels = len(variable_reference_v_levels)

shunt_vals_ohms = np.zeros(8)
shunt_vals_ohms[0] = 10000000.0
shunt_vals_ohms[1] = 1000000.0
shunt_vals_ohms[2] = 100000.0
shunt_vals_ohms[3] = 10000.0
shunt_vals_ohms[4] = 1000.0
shunt_vals_ohms[5] = 100.0
shunt_vals_ohms[6] = 12.76666
shunt_vals_ohms[7] = 7.66

# Fixed reference analysis
fr_perfect_current_levels = np.zeros(8)
for i in range(8):
    fr_perfect_current_levels[i] = fixed_ref_voltage / (shunt_vals_ohms[i] + r_fet_assumed_ohm)

fr_worst_case_current_levels = np.zeros(8)
fr_errors_percent = np.zeros(8)
for i in range(8):
    fr_worst_case_current_levels[i] = ((1.0 + shunt_accuracy_percent*0.01) * (1.0 + ad8276_gain_error_percent*0.01) * fixed_ref_voltage ) / ( (1.0 + shunt_accuracy_percent*0.01) * (shunt_vals_ohms[i] + r_fet_assumed_ohm + r_fet_variability_ohm))
    fr_errors_percent[i] = 100.0 * (fr_perfect_current_levels[i] - fr_worst_case_current_levels[i]) / fr_perfect_current_levels[i]
    print("Fixed voltage reference level {0}, error is {1:.3f} percent, current is {2:.5f} mA".format(i, fr_errors_percent[i], fr_perfect_current_levels[i]*1000.0))

# Adjustable reference analysis
ar_perfect_current_levels = np.zeros((8,num_variable_ref_v_levels))
for i in range(8):
    for j in range(num_variable_ref_v_levels):
        ar_perfect_current_levels[i,j] = variable_reference_v_levels[j] / (shunt_vals_ohms[i] + r_fet_assumed_ohm)

ar_worst_case_current_levels = np.zeros((8,num_variable_ref_v_levels))
ar_errors_percent = np.zeros((8,num_variable_ref_v_levels))
for i in range(8):
    for j in range(num_variable_ref_v_levels):
        ar_worst_case_current_levels[i,j] = ( (1.0 + ad8276_gain_error_percent*0.01) * (variable_reference_v_levels[j] + (dac_tue_fsr_percent * 0.01 * variable_reference_voltage_max)) ) / ( (1.0 + shunt_accuracy_percent*0.01) * (shunt_vals_ohms[i] + r_fet_assumed_ohm + r_fet_variability_ohm))
        ar_errors_percent[i,j] = 100.0 * (ar_perfect_current_levels[i,j] - ar_worst_case_current_levels[i,j]) / ar_perfect_current_levels[i,j]
        print("Adjustable voltage reference shunt level {0}, V level {1}, error is {2:.3f} percent, current is {3:.5f} mA".format(i, j, ar_errors_percent[i,j], ar_perfect_current_levels[i,j]*1000.0))

ar_perfect_currents_flattened = ar_perfect_current_levels.flatten()
ar_errors_percent_flattened = ar_errors_percent.flatten()
sort_idx = np.argsort(ar_perfect_currents_flattened)

fig, ax = plt.subplots()
ax.semilogx(ar_perfect_currents_flattened[sort_idx], ar_errors_percent_flattened[sort_idx], '.-', label='Adjustable Reference')
ax.semilogx(fr_perfect_current_levels, fr_errors_percent, '.-', label='Fixed Reference')

ax.set(xlabel='Current Supply, A', ylabel='Error, %',
       title='High Dynamic Range Current Supply Maximum Error')
ax.legend()
ax.minorticks_on()
ax.grid(which='both')


plt.show()