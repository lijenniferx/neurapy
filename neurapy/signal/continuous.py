"""Some methods for dealing with continuous data. We assume that the original data is in files and that they are
annoyingly large. So all the methods here work on buffered input, using memory maps.
"""
import pylab
from scipy.signal import filtfilt, iirdesign

#Some useful presets for loading continuous data dumped from the Neuralynx system
lynxlfp = {
  'fmt': 'i',
  'fs' : 32556,
  'fl' : 5,
  'fh' : 100,
  'gpass' : 0.1,
  'gstop' : 15,
  'buffer_len' : 100000,
  'overlap_len': 100,
  'max_len': -1
}

lynxspike = {
  'fmt': 'i',
  'fs' : 32556,
  'fl' : 500,
  'fh' : 8000,
  'gpass' : 0.1,
  'gstop' : 15,
  'buffer_len' : 100000,
  'overlap_len': 100,
  'max_len': -1
}
"""Use these presets as follows

from neurapy.utility import continuous as cc
y,b,a = cc.butterfilt('chan_000.raw', 'test.raw', **cc.lynxlfp)"""


def butterfilt(finname, foutname, fmt, fs, fl=5.0, fh=100.0, gpass=1.0, gstop=30.0, ftype='butter', buffer_len=100000, overlap_len=100, max_len=-1):
  """Given sampling frequency, low and high pass frequencies design a butterworth filter and filter our data with it."""
  fso2 = fs/2.0
  wp = [fl/fso2, fh/fso2]
  ws = [0.8*fl/fso2,1.4*fh/fso2]
  import pdb; pdb.set_trace()
  b, a = iirdesign(wp, ws, gpass=gpass, gstop=gstop, ftype=ftype, output='ba')
  y = filtfiltlong(finname, foutname, fmt, b, a, buffer_len, overlap_len, max_len)
  return y, b, a

def filtfiltlong(finname, foutname, fmt, b, a, buffer_len=100000, overlap_len=100, max_len=-1):
  """Use memmap and chunking to filter continuous data.
  Inputs:
    finname -
    foutname    -
    fmt         - data format eg 'i'
    b,a         - filter coefficients
    buffer_len  - how much data to process at a time
    overlap_len - how much data do we add to the end of each chunk to smooth out filter transients
    max_len     - how many samples to process. If set to -1, processes the whole file
  Outputs:
    y           - The memmapped array pointing to the written file


  Notes on algorithm:
    1. The arrays are memmapped, so we let pylab (numpy) take care of handling large arrays
    2. The filtering is done in chunks:

    Chunking details:

                |<------- b1 ------->||<------- b2 ------->|
    -----[------*--------------{-----*------]--------------*------}----------
         |<-------------- c1 -------------->|
                               |<-------------- c2 -------------->|

    From the array of data we cut out contiguous buffers (b1,b2,...) and to each buffer we add some extra overlap to
    make chunks (c1,c2). The overlap helps to remove the transients from the filtering which would otherwise appear at
    each buffer boundary.

  """
  x = pylab.memmap(finname, dtype=fmt, mode='r')
  if max_len == -1:
    max_len = x.size
  y = pylab.memmap(foutname, dtype=fmt, mode='w+', shape=max_len)

  for buff_st_idx in xrange(0, max_len, buffer_len):
    chk_st_idx = max(0, buff_st_idx - overlap_len)
    buff_nd_idx = min(max_len, buff_st_idx + buffer_len)
    chk_nd_idx = min(x.size, buff_nd_idx + overlap_len)
    rel_st_idx = buff_st_idx - chk_st_idx
    rel_nd_idx = buff_nd_idx - chk_st_idx
    this_y_chk = filtfilt(b, a, x[chk_st_idx:chk_nd_idx])
    y[buff_st_idx:buff_nd_idx] = this_y_chk[rel_st_idx:rel_nd_idx]

  return y