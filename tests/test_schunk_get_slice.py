########################################################################
#
#       Author:  The Blosc development team - blosc@blosc.org
#
########################################################################

import numpy
import pytest

import blosc2


@pytest.mark.parametrize("contiguous", [True, False])
@pytest.mark.parametrize("urlpath", [None, "b2frame"])
@pytest.mark.parametrize("mode", ["w", "a"])
@pytest.mark.parametrize(
    "cparams, dparams, nchunks, start, stop",
    [
        ({"codec": blosc2.Codec.LZ4, "clevel": 6, "typesize": 4}, {}, 10, 0, 100),
        ({"typesize": 4}, {"nthreads": 4}, 1, 7, 23),
        ({"splitmode": blosc2.SplitMode.ALWAYS_SPLIT, "nthreads": 5, "typesize": 4},
         {"schunk": None}, 5, 21, 200 * 2 * 100),
        ({"codec": blosc2.Codec.LZ4HC, "typesize": 4}, {}, 7, None, None),
        ({"blocksize": 200 * 100, "typesize": 4}, {}, 5, -2456, -234),
        ({"blocksize": 200 * 100, "typesize": 4}, {}, 4, 2456, -234),
        ({"blocksize": 100 * 100, "typesize": 4}, {}, 2, -200 * 100 + 234, 40000),
    ],
)
def test_schunk_get_slice(contiguous, urlpath, mode, cparams, dparams, nchunks, start, stop):
    storage = {"contiguous": contiguous, "urlpath": urlpath, "cparams": cparams, "dparams": dparams}
    blosc2.remove_urlpath(urlpath)

    data = numpy.arange(200 * 100 * nchunks, dtype="int32")
    schunk = blosc2.SChunk(chunksize=200 * 100 * 4, data=data, mode=mode, **storage)

    start_, stop_ = start, stop
    if start is None:
        start_ = 0
    if stop is None:
        stop_ = data.size

    sl = data[start_:stop]
    res = schunk.get_slice(start, stop)
    assert res == sl.tobytes()

    res = schunk[start:stop]
    assert res == sl.tobytes()

    out = numpy.empty(sl.shape, dtype="int32")
    schunk.get_slice(start, stop, out)
    assert numpy.array_equal(data[start_:stop_], out)

    schunk.get_slice(start, stop, memoryview(out))
    assert numpy.array_equal(data[start_:stop_], out)

    out = bytearray(res)
    schunk.get_slice(start, stop, out)
    assert out == bytearray(data)[start_*4:stop_*4]

    blosc2.remove_urlpath(urlpath)


def test_schunk_get_slice_raises():
    storage = {"contiguous": True, "urlpath": "schunk.b2frame", "cparams": {"typesize": 4}, "dparams": {}}
    blosc2.remove_urlpath(storage["urlpath"])

    nchunks = 2
    data = numpy.arange(200 * 100 * nchunks, dtype="int32")
    schunk = blosc2.SChunk(chunksize=200 * 100 * 4, data=data, **storage)

    start = 200 * 100
    stop = 200 * 100 * nchunks
    with pytest.raises(IndexError):
        res = schunk[start:stop:2]

    out = numpy.empty(stop - start - 1, dtype="int32")
    with pytest.raises(ValueError):
        schunk.get_slice(start, stop, out)

    start = -1
    stop = -4
    with pytest.raises(ValueError):
        res = schunk[start:stop]

    start = 200 * 100 * nchunks
    stop = start + 4
    with pytest.raises(ValueError):
        res = schunk[start:stop]

    blosc2.remove_urlpath(storage["urlpath"])
