#------------------------------------------------------#
# SAMR measure and plot with nidaqmx v0.3              #
# pulse train signal  	                               #
# author: tatsunootoshigo, 7475un00705hi90@gmail.com   #
#------------------------------------------------------#

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import time
import sys
from scipy import signal

# dc square pulse train = DC voltage 
dc_nSamples = 10000 # samples
dc_fs = 34 #Hz
dc_t0 = np.linspace(0, dc_nSamples, num=dc_nSamples) # time series
dc_sig = 0.5*(signal.square(2*np.pi*dc_fs*dc_t0, duty=0.5) + 1.0)
print(dc_sig)

# define figure and subplots
fig = plt.figure(figsize=(9,6), dpi=80)
spec = gridspec.GridSpec(ncols=1, nrows=1, figure=fig)
plt.tight_layout()
#plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
dc_gen_xy = fig.add_subplot(spec[0, 0])

# plot the dc voltage signal
dc_gen_xy.plot(dc_t0, dc_sig, color="blue", linewidth=1.0, linestyle="-")

plt.show()