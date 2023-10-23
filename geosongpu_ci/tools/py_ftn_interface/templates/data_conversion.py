import cffi
import numpy as np
from math import prod
from typing import Tuple, Optional, List, Union
from types import ModuleType

try:
    import cupy as cp
except ImportError:
    cp = None
if cupy is not None:
    # Cupy might be available - but not the device
    try:
        cupy.cuda.runtime.deviceSynchronize()
    except cupy.cuda.runtime.CUDARuntimeError:
        cp = None

DeviceArray = cp.ndarray if cp else None
PythonArray = Union[np.ndarray, (cp.ndarray if cp else None)]


class FortranPythonConversion:
    """
    Convert Fortran arrays to NumPy and vice-versa
    """

    def __init__(self, numpy_module: ModuleType):
        # Python numpy-like module is given by the caller leaving
        # optional control of upload/download in the case
        # of GPU/CPU system
        self._target_np = numpy_module

        # Device parameters
        self._python_targets_gpu = self._target_np == cp
        if self._python_targets_gpu:
            self._stream_A = cp.cuda.Stream(non_blocking=True)
            self._stream_B = cp.cuda.Stream(non_blocking=True)
            self._current_stream = self._stream_A

        # cffi init
        self._ffi = cffi.FFI()
        self._TYPEMAP = {
            "float": np.float32,
            "double": np.float64,
            "int": np.int32,
        }

    def _device_sync(self):
        """Synchronize the working CUDA streams"""
        self._stream_A.synchronize()
        self._stream_B.synchronize()

    def _fortran_to_numpy(
        self,
        fptr: "cffi.FFI.CData",
        dim: List[int],
    ) -> np.ndarray:
        """
        Input: Fortran data pointed to by fptr and of shape dim = (i, j, k)
        Output: C-ordered double precision NumPy data of shape (i, j, k)
        """
        ftype = self._ffi.getctype(self._ffi.typeof(fptr).item)
        assert ftype in self._TYPEMAP
        return np.frombuffer(
            self._ffi.buffer(fptr, prod(dim) * self._ffi.sizeof(ftype)),
            self._TYPEMAP[ftype],
        )

    def _upload_and_transform(
        self,
        host_array: np.ndarray,
        dim: List[int],
        swap_axes: Optional[Tuple[int, int]] = None,
    ) -> DeviceArray:
        """Upload to device & transform to Pace compatible layout"""
        with self._current_stream:
            device_array = cp.asarray(host_array)
            final_array = self._transform_from_fortran_layout(
                device_array,
                dim,
                swap_axes,
            )
            self._current_stream = (
                self._stream_A
                if self._current_stream == self._stream_B
                else self._stream_B
            )
            return final_array

    def _transform_from_fortran_layout(
        self,
        array: PythonArray,
        dim: List[int],
        swap_axes: Optional[Tuple[int, int]] = None,
    ) -> PythonArray:
        """Transform from Fortran layout into a Pace compatible layout"""
        trf_array = array.reshape(tuple(reversed(dim))).transpose().astype(Float)
        if swap_axes:
            trf_array = self._target_np.swapaxes(
                trf_array,
                swap_axes[0],
                swap_axes[1],
            )
        return trf_array

    def _fortran_to_python_trf(
        self,
        fptr: np.ndarray,
        dim: List[int],
        swap_axes: Optional[Tuple[int, int]] = None,
    ) -> PythonArray:
        """Move fortran memory into python space"""
        np_array = self._fortran_to_numpy(fptr, dim)
        if self._python_targets_gpu:
            return self._upload_and_transform(np_array, dim, swap_axes)
        else:
            return self._transform_from_fortran_layout(
                np_array,
                dim,
                swap_axes,
            )

    def _transform_and_download(
        self,
        device_array: DeviceArray,
        dtype: type,
        swap_axes: Optional[Tuple[int, int]] = None,
    ) -> np.ndarray:
        with self._current_stream:
            if swap_axes:
                device_array = cp.swapaxes(
                    device_array,
                    swap_axes[0],
                    swap_axes[1],
                )
            host_array = cp.asnumpy(
                device_array.astype(dtype).flatten(order="F"),
            )
            self._current_stream = (
                self._stream_A
                if self._current_stream == self._stream_B
                else self._stream_B
            )
            return host_array

    def _transform_from_python_layout(
        self,
        array: PythonArray,
        dtype: type,
        swap_axes: Optional[Tuple[int, int]] = None,
    ) -> np.ndarray:
        """Copy back a numpy array in python layout to Fortran"""

        if self._python_targets_gpu:
            numpy_array = self._transform_and_download(array, dtype, swap_axes)
        else:
            numpy_array = array.astype(dtype).flatten(order="F")
            if swap_axes:
                numpy_array = np.swapaxes(
                    numpy_array,
                    swap_axes[0],
                    swap_axes[1],
                )
        return numpy_array

    def _python_to_fortran_trf(
        self,
        array: PythonArray,
        fptr: "cffi.FFI.CData",
        ptr_offset: int = 0,
        swap_axes: Optional[Tuple[int, int]] = None,
    ) -> np.ndarray:
        """
        Input: Fortran data pointed to by fptr and of shape dim = (i, j, k)
        Output: C-ordered double precision NumPy data of shape (i, j, k)
        """
        ftype = self._ffi.getctype(self._ffi.typeof(fptr).item)
        assert ftype in self._TYPEMAP
        dtype = self._TYPEMAP[ftype]
        numpy_array = self._transform_from_python_layout(
            array,
            dtype,
            swap_axes,
        )
        self._ffi.memmove(fptr + ptr_offset, numpy_array, 4 * numpy_array.size)
