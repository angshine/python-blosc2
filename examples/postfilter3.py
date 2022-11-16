########################################################################
#
#       Author:  The Blosc development team - blosc@blosc.org
#
########################################################################

import blosc2
import numpy as np

nchunks = 10
input_dtype = np.dtype(np.int64)

# Set the compression and decompression parameters
cparams = {"codec": blosc2.Codec.LZ4, "typesize": input_dtype.itemsize}
dparams = {"nthreads": 2}
contiguous = False
urlpath = None
storage = {"contiguous": contiguous, "urlpath": urlpath, "cparams": cparams, "dparams": dparams}
# Remove previous SChunk
blosc2.remove_urlpath(urlpath)
# Create and set data
chunkshape = 20_000
data = np.zeros(chunkshape * nchunks, dtype=input_dtype)
schunk = blosc2.SChunk(chunksize=chunkshape * input_dtype.itemsize, data=data, **storage)

out1 = np.empty(chunkshape * nchunks, dtype=input_dtype)
schunk.get_slice(0, chunkshape * nchunks, out=out1)


# Set postfilter with decorator
@blosc2.postfilter(schunk, input_dtype)
def postfilter(input, output, offset):
    for i in range(input.size):
        output[i] = offset + i


out2 = np.empty(chunkshape * nchunks, dtype=input_dtype)
schunk.get_slice(0, chunkshape * nchunks, out=out2)

res = np.arange(out1.size, dtype=input_dtype)
# Check postfilter is applied
assert np.array_equal(res, out2)
