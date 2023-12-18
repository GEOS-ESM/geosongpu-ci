import asyncio
import json
import os
import socket
from typing import List

import numpy as np
import psutil
from pynvml import (
    nvmlDeviceGetCount,
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetMemoryInfo,
    nvmlDeviceGetName,
    nvmlDeviceGetPowerUsage,
    nvmlDeviceGetUtilizationRates,
    nvmlInit,
    nvmlSystemGetDriverVersion,
)

from tcn.tools.hws.constants import (
    HWS_DUMP_FORMAT,
    HWS_DUMP_JSON,
    HWS_DUMP_NPZ,
    HWS_HARDWARE_SPECS,
    HWS_HW_CPU,
    SERV_ORDER_DUMP,
    SERV_ORDER_START,
    SERV_ORDER_STOP,
    SERV_ORDER_TICK,
    SOCKET_DIRECTORY,
    SOCKET_FILENAME,
)


async def psu_utlz_read(
    gpu_psu: List[float],
    gpu_exe_utl: List[float],
    gpu_mem_utl: List[float],
    gpu_mem: List[float],
    cpu_exe_utl: List[float],
    cpu_psu: List[float],
    record_dt: float,
    handle,
):
    while True:
        # NVML reads
        gpu_psu.append(nvmlDeviceGetPowerUsage(handle) / 1000)
        nvmlUtlz = nvmlDeviceGetUtilizationRates(handle)
        gpu_exe_utl.append(nvmlUtlz.gpu)
        gpu_mem_utl.append(nvmlUtlz.memory)
        nvmlMem = nvmlDeviceGetMemoryInfo(handle)
        gpu_mem.append(nvmlMem.used / (1024 * 1024))
        # CPU - EPYC 7402
        cpu_use = psutil.cpu_percent()
        cpu_exe_utl.append(cpu_use)
        # linear regression for power on CPU from utl
        idle = HWS_HARDWARE_SPECS[HWS_HW_CPU]["PSU_IDLE"]
        tdp = HWS_HARDWARE_SPECS[HWS_HW_CPU]["PSU_TDP"]
        cpu_psu.append(max(cpu_use / 100 * tdp, idle))
        # Sleep the dt
        await asyncio.sleep(record_dt)


async def main():
    # # Setup
    print("NVML server up & waiting for connection")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    os.makedirs(SOCKET_DIRECTORY, exist_ok=True)
    if os.path.exists(SOCKET_FILENAME):
        os.remove(SOCKET_FILENAME)
    server.bind(SOCKET_FILENAME)
    server.listen(1)
    server.setblocking(False)

    # Actions
    record_dt = 1
    hardware_load = {}
    hardware_load["gpu_psu"] = []
    hardware_load["gpu_exe_utl"] = []
    hardware_load["gpu_mem_utl"] = []
    hardware_load["gpu_mem"] = []
    hardware_load["cpu_exe_utl"] = []
    hardware_load["cpu_psu"] = []
    ticks = []

    # Spin NVML
    nvmlInit()
    print("[NVML SERVER] Driver Version:", nvmlSystemGetDriverVersion())
    deviceCount = nvmlDeviceGetCount()
    assert deviceCount == 1
    handle = nvmlDeviceGetHandleByIndex(0)
    name = nvmlDeviceGetName(handle)
    print(f"[NVML SERVER] Device: {name}")

    # asyncio
    loop = asyncio.get_event_loop()

    # Server loop
    while True:
        # Deal with client/server
        client, _ = await loop.sock_accept(server)
        print(f"[NVML SERVER] Connection from {client}")

        # Process request
        request = (await loop.sock_recv(client, 255)).decode("utf8")
        order = json.loads(request)

        # We have a valid message
        if order["action"] == SERV_ORDER_STOP:
            print("[NVML SERVER] Closing...")
            client.close()
            break
        elif order["action"] == SERV_ORDER_START:
            record_dt = order["dt"]
            loop.create_task(
                psu_utlz_read(
                    hardware_load["gpu_psu"],
                    hardware_load["gpu_exe_utl"],
                    hardware_load["gpu_mem_utl"],
                    hardware_load["gpu_mem"],
                    hardware_load["cpu_exe_utl"],
                    hardware_load["cpu_psu"],
                    record_dt,
                    handle,
                )
            )
            print(f"[NVML SERVER] Recording every {record_dt} seconds")
        elif order["action"] == SERV_ORDER_DUMP:
            hws_dump_name = order["dump_name"]
            if HWS_DUMP_FORMAT == HWS_DUMP_NPZ:
                np.savez_compressed(f"./{hws_dump_name}.npz", **hardware_load)
            elif HWS_DUMP_FORMAT == HWS_DUMP_JSON:
                json_data = json.dumps(hardware_load, indent=4)
                with open(f"{hws_dump_name}.json", "w") as f:
                    f.write(json_data)
            else:
                raise RuntimeWarning(f"Can't dump in unknown format {HWS_DUMP_FORMAT}")
        elif order["action"] == SERV_ORDER_TICK:
            ticks.append(len(hardware_load))
            print(f"[NVML SERVER] Recorded tick at {ticks[-1]}")
        else:
            print(f"[NVML SERVER] Received unknown {order}")

        # One-time client
        client.close()
    # psu_read_task.cancel()
    server.close()


def cli():
    asyncio.run(main())
