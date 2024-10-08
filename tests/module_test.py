import ctypes

import pytest

from cudaffi.module import (
    CudaCompilationError,
    CudaCompilationWarning,
    CudaData,
    CudaFunction,
    CudaFunctionNameNotFound,
    CudaModule,
)


class TestModule:
    def test_exists(self) -> None:
        CudaModule.from_file("tests/helpers/simple.cu")

    def test_compilation_error(self) -> None:
        with pytest.raises(CudaCompilationError, match='error: expected a ";"'):
            CudaModule(
                """
            __global__ void thingy() {
            printf("this is a test\\n") // missing semicolon
            }
            """
            )

    def test_compilation_warning(self) -> None:
        with pytest.warns(
            CudaCompilationWarning, match="the format string requires additional arguments"
        ):
            CudaModule(
                """
            __global__ void thingy() {
            printf("this is a test %d\\n"); // missing argument
            }
            """
            )

    def test_no_extern(self) -> None:
        mod = CudaModule(
            """
            extern "C" __global__ void thingy() {
            printf("this is a test\\n");
            }
            """,
            no_extern=True,
        )
        fn = mod.get_function("thingy")
        assert isinstance(fn, CudaFunction)

    def test_compile_options(self) -> None:
        mod = CudaModule(
            """
            __global__ void thingy() {
            printf("this is a test\\n");
            }
            """,
            compile_options=["--fmad=false"],
        )
        assert len(mod.compile_args) == 2
        assert mod.compile_args[0] == b"--fmad=false"

    def test_include_paths(self) -> None:
        mod = CudaModule(
            """
            #include "dummy.h"

            __global__ void thingy() {
            printf("this is a test: %d\\n", DUMMY);
            }
            """,
            include_dirs=["tests/helpers/include"],
        )
        assert len(mod.compile_args) == 3
        assert mod.compile_args[1] == b"-I"
        assert mod.compile_args[2] == b"tests/helpers/include"

    def test_bad_compile_option(self) -> None:
        with pytest.raises(
            CudaCompilationError, match="unrecognized option --thisisanoptionthatdoesnotexist"
        ):
            CudaModule(
                """
                __global__ void thingy() {
                printf("this is a test\\n");
                }
                """,
                compile_options=["--thisisanoptionthatdoesnotexist"],
            )


class TestFunction:
    def test_basic(self) -> None:
        mod = CudaModule(
            """
        __global__ void thingy() {
          printf("this is a test\\n");
        }
        """
        )
        fn = mod.get_function("thingy")
        assert isinstance(fn, CudaFunction)
        mod.thingy()

    def test_from_file(self) -> None:
        mod = CudaModule.from_file("tests/helpers/simple.cu")
        fn = mod.get_function("simple")
        assert isinstance(fn, CudaFunction)
        mod.simple()

    def test_one_arg(self) -> None:
        mod = CudaModule.from_file("tests/helpers/one_arg.cu")
        fn = mod.get_function("one")
        assert isinstance(fn, CudaFunction)
        mod.one(1)

    def test_wrong_name(self) -> None:
        mod = CudaModule.from_file("tests/helpers/one_arg.cu")
        with pytest.raises(CudaFunctionNameNotFound):
            mod.doesnotexist(1)

    def test_arg_type_string(self) -> None:
        mod = CudaModule.from_file("tests/helpers/string_arg.cu")
        mod.printstr("blah")


class TestData:
    def test_int(self) -> None:
        d = CudaData(1)
        assert d.data == 1
        assert d.ctype == ctypes.c_uint
