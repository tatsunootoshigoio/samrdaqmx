#------------------------------------------------------#
# SAMR measure and plot with nidaqmx v0.3   	       #
# author: tatsunootoshigo, 7475un00705hi90@gmail.com   #
#------------------------------------------------------#

import nidaqmx
from pynput import keyboard
from pynput.keyboard import Key, KeyCode, Listener, Controller
from nidaqmx.constants import AcquisitionType, FuncGenType
from matplotlib.widgets import CheckButtons, Button
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import time
import sys
from scipy import signal
import threading
from matplotlib import style
import pandas as pd

# plots style
#style.use('fivethirtyeight')

# nidaqmx initialization stuff
nidaqmx_sys = nidaqmx.system.system.System.local()

print('DAQmx Driver Version:{0}.{1}.{2}'.format(nidaqmx_sys.driver_version.major_version, nidaqmx_sys.driver_version.minor_version, nidaqmx_sys.driver_version.update_version))
for device in nidaqmx_sys.devices:
    print('Device Name: {0}, Product Category: {1}, Product Type: {2}'.format(device.name, device.product_category, device.product_type))

# sine fucntion parameters = AC voltage
fs = 50 #Hz
T = 3
nSamples = int(T * fs) #samples

a0 = 5
f0 = 3
t0_ac = np.arange(nSamples)/fs
sig = a0*np.sin(2*np.pi*f0*t0_ac)

# samples to read for ac_gen_volt signal
ac_gen_volt_samples_per_chan_no = 250
dc_gen_volt_samples_per_chan_no = 250

# if these don't mach signal plots don't mach
task_ch0_out_timing_rate = 100
task_ch0_in_timing_rate = 100
task_ch1_out_timing_rate = 20001
task_ch1_in_timing_rate = 20001
# tasks to be run by the aquisition card
task_ch0_in = nidaqmx.Task() 
task_ch1_in = nidaqmx.Task()
#task_ch0_out = nidaqmx.Task()
#task_ch1_out = nidaqmx.Task()

ch0_in_name = "Dev1/ai0"
ch1_in_name = "Dev1/ai1"
ch0_out_name = "Dev1/ao0"
ch1_out_name = "Dev1/ao1"

# input output channels on the card (consult piount)
ch0_in = task_ch0_in.ai_channels.add_ai_voltage_chan(ch0_in_name)
ch1_in = task_ch1_in.ai_channels.add_ai_voltage_chan(ch1_in_name)

task_ch0_in.timing.cfg_samp_clk_timing(rate=task_ch0_in_timing_rate, sample_mode=AcquisitionType.CONTINUOUS)

task_ch1_in.timing.cfg_samp_clk_timing(rate=task_ch1_in_timing_rate, sample_mode=AcquisitionType.CONTINUOUS)

# print(task_ch0_out.timing.samp_clk_rate)

# define figure and subplots
fig = plt.figure(figsize=(16,8), dpi=80)
spec = gridspec.GridSpec(ncols=1, nrows=2, figure=fig)
plt.tight_layout()
#plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
ac_gen_xy = fig.add_subplot(spec[0, 0])
ac_gen_xy_fft = fig.add_subplot(spec[1, 0])
#dc_gen_xy = fig.add_subplot(spec[0, 1])
# DataFrames to collect samples
ac_df = pd.DataFrame()
ac_df_fft = pd.DataFrame()

# defining button events for the plot
def gen_ac_start(event):
	#print(CheckButtons.get_status(chk_btn))
	print('Plotting selected AC datasets...')
	task_ch0_out = nidaqmx.Task()
	ch0_out = task_ch0_out.ao_channels.add_ao_voltage_chan(ch0_out_name)
	task_ch0_out.timing.cfg_samp_clk_timing(rate=task_ch0_out_timing_rate, sample_mode=AcquisitionType.FINITE, samps_per_chan=ac_gen_volt_samples_per_chan_no)

	task_ch0_out.write(sig, auto_start=True)
	task_ch0_out.wait_until_done()
	task_ch0_out.stop()
	task_ch0_out.close()
	print(ac_df_fft)

def gen_ac_clear(event):
	#print(CheckButtons.get_status(chk_btn))
	print('Clearing plot...')
	ac_gen_xy_fft.clear()

def exit_program(event): 
	print('Exiting program...')
	global aq_start
	aq_start = False;

#plt.xticks([-1.5*np.pi, -np.pi, -np.pi/2, 0, np.pi/2, np.pi, 1.5*np.pi],[r'$-\frac{3}{2}\pi$',r'$-\pi$', r'$-\pi/2$', r'$0$', r'$+\pi/2$', r'$+\pi$', r'$\frac{3}{2}\pi$'])

#plt.yticks([-1, 0, +1],[r'$-1$', r'  ', r'$+1$'])
	
ax = plt.gca()
#for label in ax.get_xticklabels() + ax.get_yticklabels():
#	label.set_fontsize(12)
#	label.set_bbox(dict(facecolor='white', edgecolor='None', alpha=0.65 ))

# plot buttons
plot_ac_btn_ax = plt.axes([0.01, 0.30, 0.06, 0.03], frameon=True)
plot_ac_btn = Button(plot_ac_btn_ax, 'AC start', color='0.85', hovercolor='0.95')
plot_ac_btn.on_clicked(gen_ac_start)

plot_dc_btn_ax = plt.axes([0.01, 0.26, 0.06, 0.03], frameon=True)
plot_dc_btn = Button(plot_dc_btn_ax, 'AC clear', color='0.85', hovercolor='0.95')
plot_dc_btn.on_clicked(gen_ac_clear)

exit_btn_ax = plt.axes([0.01, 0.22, 0.06, 0.03], frameon=True)
exit_btn = Button(exit_btn_ax, 'Exit', color='0.85', hovercolor='0.95')
exit_btn.on_clicked(exit_program)

plt.ion()

aq_start = True
while aq_start == True:
	acvolt_in = task_ch0_in.read(number_of_samples_per_channel=np.size(t0_ac))
	time.sleep(1)
	actime_in = t0_ac
	ac_data_row = pd.Series(acvolt_in, actime_in)
	
	data_row = pd.Series(acvolt_in, actime_in)
	ac_df = data_row

	ac_gen_xy.clear()
	# plot the defined sinusoidal ac voltage function
	ac_gen_xy.plot(t0_ac, sig, color="blue", linewidth=0.5, linestyle="-")
	ac_gen_xy.plot(ac_df, color='r', linewidth=1.0)

	ac_df_fft = np.fft.fft(ac_df)
	ac_gen_xy_fft.plot(ac_df_fft, color='g', linewidth=1.0)
	
	plt.pause(0.0001)
	time.sleep(.01)
	plt.show()

# free NI cards' recources on exit
task_ch0_in.close()
task_ch1_in.close()