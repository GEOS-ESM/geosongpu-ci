local install_dir  = "/home/fgdeconi/work/sw/stack/src/2024.08.LOCAL/install"
local ser_pkgdir = "/home/fgdeconi/work/git/serialbox/install"

-- Fix: GT4Py expects CUDA_HOME to be set --
-- setenv("CUDA_HOME", pathJoin(os.getenv("NVHPC_ROOT"), "cuda"))

-- UCX --
local ucx_pkgdir = pathJoin(install_dir, "ucx")
prepend_path("LD_LIBRARY_PATH",pathJoin(ucx_pkgdir,"lib"))

-- OMPI --
local ompi_pkgdir = pathJoin(install_dir, "ompi")

setenv("M_MPI_ROOT",ompi_pkgdir)
setenv("OPENMPI",ompi_pkgdir)
setenv("MPI_HOME",ompi_pkgdir)

prepend_path("PATH",pathJoin(ompi_pkgdir,"bin"))
prepend_path("LD_LIBRARY_PATH",pathJoin(ompi_pkgdir,"lib"))
prepend_path("INCLUDE",pathJoin(ompi_pkgdir,"include"))
prepend_path("MANPATH",pathJoin(ompi_pkgdir,"share/man"))

setenv("OMPI_MCA_orte_tmpdir_base","/tmp")
setenv("TMPDIR","/tmp")
setenv("OMP_STACKSIZE","1G")
setenv("OMPI_MCA_mca_base_component_show_load_errors","0")
setenv("PMIX_MCA_mca_base_component_show_load_errors","0")

-- BOOST HEADERS (as expected by gt4py) --
local boost_pkgdir = pathJoin(install_dir, "boost")
setenv("BOOST_ROOT", boost_pkgdir)

-- Python 3 --
-- USING LOCAL pyenv
-- local py_pkgdir = pathJoin(install_dir, "python3")
-- prepend_path("PATH",pathJoin(py_pkgdir,"bin"))
-- prepend_path("LD_LIBRARY_PATH",pathJoin(py_pkgdir,"lib"))
-- prepend_path("LD_LIBRARY_PATH",pathJoin(py_pkgdir,"lib64"))

-- Load venv --
-- local py_pkgdir = pathJoin(install_dir, "venv")
-- prepend_path("PATH",pathJoin(py_pkgdir,"bin"))
-- setenv("VIRTUAL_ENV", py_pkgdir)

-- Baselibs at a BASEDIR --
local baselibs_pkgdir = pathJoin(install_dir, "baselibs-7.17.1/install/x86_64-pc-linux-gnu/")
setenv("BASEDIR", baselibs_pkgdir)

-- Serialbox --
prepend_path("SERIALBOX_ROOT", ser_pkgdir)
prepend_path("PATH",pathJoin(ser_pkgdir,"python/pp_ser"))
prepend_path("LD_LIBRARY_PATH",pathJoin(ser_pkgdir,"lib"))
prepend_path("PYTHONPATH",pathJoin(ser_pkgdir,"python"))
