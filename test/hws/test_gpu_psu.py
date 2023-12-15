import cupy as cp
import multiprocessing as mp
from geosongpu_ci.tools.hws.server import cli
from geosongpu_ci.tools.hws.client import client_main
import time
import os
from geosongpu_ci.tools.hws.constants import DUMP_HWLOAD_FILENAME


def GPU_work():
    A = cp.random.random(10000)
    B = cp.random.random(10000)
    for _ in range(0, 1000000):
        C = A * B  # noqa


def test_gpu_psu_sampling():
    p_server = mp.Process(target=cli)
    p_server.start()
    time.sleep(2)  # asyncness needs some time to start
    client_main("start")
    p_work = mp.Process(target=GPU_work)
    p_work.start()
    # measures should be recorded here
    p_work.join()
    client_main("dump")
    client_main("stop")
    p_server.join()

    assert os.path.exists(f"{DUMP_HWLOAD_FILENAME}.npz")


if __name__ == "__main__":
    test_gpu_psu_sampling()
