load("comp/gcc/12.3.0")
load("nvidia/nvhpc-nompi/23.9")

local version = getenv("DSLSW_VERSION")
local install_dir  = pathJoin(pathJoin("/discover/nobackup/projects/geosongpu/sw_sles15/live/src/", version), "install/")

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
local py_pkgdir = pathJoin(install_dir, "python3")
prepend_path("PATH",pathJoin(py_pkgdir,"bin"))
prepend_path("LD_LIBRARY_PATH",pathJoin(py_pkgdir,"lib"))
