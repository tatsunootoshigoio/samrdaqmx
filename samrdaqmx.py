#------------------------------------------------------#
# SAMR measure and plot with nidaqmx v0.3   	       #
# author: tatsunootoshigo, 7475un00705hi90@gmail.com   #
#------------------------------------------------------#

import nidaqmx
#from pynput import keyboard
#from pynput.keyboard import Key, KeyCode, Listener, Controller
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
ac_nSamples = 10000 # samples
ac_fs = 63 #Hz
ac_a0 = 5
ac_t0 = np.linspace(0, ac_nSamples, num=ac_nSamples) # time series
ac_sig = ac_a0*np.sin(2*np.pi*ac_fs*ac_t0)

# dc pulse parameter = DC voltage

#task_ch1_out.write([1.1, 1.1, 1.1, 1.1, 1.1, 1.1], auto_start=True)
# terrible spike up to 3.5V if num=1001 or less for 1V
#rise_1V = np.linspace(0.0, 1.0, num=2000)
# nice fall without spikes even for num=1001 for 1V
#stay_1V = np.ones(2000)
#fall_1V = np.linspace(1.0, 0.0, num=2000)
#dc_pulse = np.concatenate([rise_1V, stay_1V, fall_1V])

# dc square pulse train = DC voltage 
#dc_nSamples = 10000 # samples
#dc_fs = 34 #Hz
#dc_t0 = np.linspace(0, dc_nSamples, num=dc_nSamples) # time series
#dc_sig = signal.square(2*np.pi*dc_fs*dc_t0, duty=0.5)

# dc square pulse train = DC voltage (baseline adjusted) 
dc_nSamples = 10000 # samples
dc_fs = 34 #Hz
dc_t0 = np.linspace(0, dc_nSamples, num=dc_nSamples) # time series
dc_sig = 0.5*(signal.square(2*np.pi*dc_fs*dc_t0, duty=0.5) + 1.0)

# samples to read for ac_gen_volt ac_signal (size of buffer allocation)
ac_gen_volt_samples_per_chan_no = 10*ac_nSamples
dc_gen_volt_samples_per_chan_no = 10*dc_nSamples

# adjust sampling rates for i/o channels
task_ch0_out_sampling_rate = 2*ac_nSamples
task_ch0_in_sampling_rate = 1*ac_nSamples
task_ch1_out_sampling_rate = 2*dc_nSamples
task_ch1_in_sampling_rate = 1*dc_nSamples

# tasks to be run by the acquisition card
task_ch0_in = nidaqmx.Task() 
task_ch1_in = nidaqmx.Task()
#task_ch0_out = nidaqmx.Task()
#task_ch1_out = nidaqmx.Task()

# channel names
ch0_in_name = "Dev1/ai0"
ch1_in_name = "Dev1/ai1"
ch0_out_name = "Dev1/ao0"
ch1_out_name = "Dev1/ao1"

# multiple channels
ch01_in_name = "Dev/ai0:1" 

# input output channels on the card (consult piount)
ch0_in = task_ch0_in.ai_channels.add_ai_voltage_chan(ch0_in_name)
ch1_in = task_ch1_in.ai_channels.add_ai_voltage_chan(ch1_in_name)

task_ch0_in.timing.cfg_samp_clk_timing(rate=task_ch0_in_sampling_rate, sample_mode=AcquisitionType.FINITE, samps_per_chan=ac_gen_volt_samples_per_chan_no)

task_ch1_in.timing.cfg_samp_clk_timing(rate=task_ch1_in_sampling_rate, sample_mode=AcquisitionType.CONTINUOUS)

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
	task_ch0_out.timing.cfg_samp_clk_timing(rate=task_ch0_out_sampling_rate, sample_mode= AcquisitionType.FINITE, samps_per_chan=ac_gen_volt_samples_per_chan_no)

	task_ch0_out.write(ac_sig, auto_start=True)
	task_ch0_out.wait_until_done()
	task_ch0_out.stop()
	task_ch0_out.close()
	#print(ac_df_fft)

# defining button events for the plot
def gen_dc_start(event):
	#print(CheckButtons.get_status(chk_btn))
	print('Plotting selected DC datasets...')
	task_ch1_out = nidaqmx.Task()
	task_ch1_out.ao_channels.add_ao_voltage_chan(ch1_out_name)
	task_ch1_out.timing.cfg_samp_clk_timing(rate=task_ch1_out_sampling_rate, sample_mode= AcquisitionType.FINITE, samps_per_chan=dc_gen_volt_samples_per_chan_no)
	
	print(dc_sig)
	task_ch1_out.write(dc_sig, auto_start=True)
	task_ch1_out.wait_until_done()
	task_ch1_out.stop()
	task_ch1_out.close()
	#print(ac_df_fft)	

def gen_ac_clear(event):
	#print(CheckButtons.get_status(chk_btn))
	print('Clearing plot...')
	ac_gen_xy_fft.clear()

def exit_program(event): 
	print('Exiting program...')
	global aq_start
	aq_start = False;

# some neat labels for the plots
#plt.xticks([-1.5*np.pi, -np.pi, -np.pi/2, 0, np.pi/2, np.pi, 1.5*np.pi],[r'$-\frac{3}{2}\pi$',r'$-\pi$', r'$-\pi/2$', r'$0$', r'$+\pi/2$', r'$+\pi$', r'$\frac{3}{2}\pi$'])

#plt.yticks([-1, 0, +1],[r'$-1$', r'  ', r'$+1$'])
	
ax = plt.gca()
#for label in ax.get_xticklabels() + ax.get_yticklabels():
#	label.set_fontsize(12)
#	label.set_bbox(dict(facecolor='white', edgecolor='None', alpha=0.65 ))

""" plot i/o buttons """
# gen DC button
plot_dc_btn_ax = plt.axes([0.01, 0.34, 0.06, 0.03], frameon=True)
plot_dc_btn = Button(plot_dc_btn_ax, 'DC start', color='0.85', hovercolor='0.95')
plot_dc_btn.on_clicked(gen_dc_start)

# gen AC button
plot_ac_btn_ax = plt.axes([0.01, 0.30, 0.06, 0.03], frameon=True)
plot_ac_btn = Button(plot_ac_btn_ax, 'AC start', color='0.85', hovercolor='0.95')
plot_ac_btn.on_clicked(gen_ac_start)

# clear AC FFT plot button 
plot_ac_clear_btn_ax = plt.axes([0.01, 0.26, 0.06, 0.03], frameon=True)
plot_ac_clear_btn = Button(plot_ac_clear_btn_ax, 'AC clear', color='0.85', hovercolor='0.95')
plot_ac_clear_btn.on_clicked(gen_ac_clear)

# terminate program breaks while acquisition loop
exit_btn_ax = plt.axes([0.01, 0.22, 0.06, 0.03], frameon=True)
exit_btn = Button(exit_btn_ax, 'Exit', color='0.85', hovercolor='0.95')
exit_btn.on_clicked(exit_program)

# turn on interactive mode for plots
plt.ion()

""" main acquisition loop to read data and update plots """
aq_start = True
while aq_start == True:

	# reads AC from ch0_out
	acvolt_in = task_ch0_in.read(number_of_samples_per_channel=ac_nSamples)
	time.sleep(1)
	actime_in = ac_t0
	ac_data_row = pd.Series(acvolt_in, actime_in)
	
	data_row = pd.Series(acvolt_in, actime_in)
	ac_df = data_row

	ac_gen_xy.clear()
	
	# plot the ac voltage signal
	ac_gen_xy.plot(ac_t0, ac_sig, color="blue", linewidth=0.5, linestyle="-")
	
	# plot aquired voltage singal
	ac_gen_xy.plot(ac_df, color='r', linewidth=1.0)

	# plot FFT of the aquired signal 
	ac_df_fft = np.fft.fft(ac_df)
	ac_gen_xy_fft.plot(ac_df_fft, color='g', linewidth=1.0)
	
	plt.pause(0.0001)
	time.sleep(.01)
	plt.show()

# free NI cards' resources on exit
task_ch0_in.close()
task_ch1_in.close()