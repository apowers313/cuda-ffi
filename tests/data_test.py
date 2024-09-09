import ctypes

from cudaffi.module import CudaData


class TestData:
    def test_int(self) -> None:
        d = CudaData(1)
        assert d.data == 1
        assert d.ctype == ctypes.c_uint
