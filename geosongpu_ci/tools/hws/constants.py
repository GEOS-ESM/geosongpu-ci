import os

# Socket details
SOCKET_DIRECTORY = "./hwsampler-sockets"
SOCKET_FILENAME = f"{SOCKET_DIRECTORY}/stats_wrapper"

# All commands that the serve can process
SERV_ORDER_START = "START"
SERV_ORDER_STOP = "STOP"
SERV_ORDER_DUMP = "DUMP"
SERV_ORDER_TICK = "TICK"

# Start the recording at dt intervals
CLIENT_CMD_START = "start"
# Stop recording, kill servers
CLIENT_CMD_STOP = "stop"
# Dump data into a format controlled by env var
# HWS_DUMP_FORMAT = {npz, json}
CLIENT_CMD_DUMP = "dump"
CLIENT_CMD_TICK = "tick"

CLIENT_CMDS = {
    CLIENT_CMD_START: {
        "action": SERV_ORDER_START,
        "dt": 0.01,
    },
    CLIENT_CMD_STOP: {"action": SERV_ORDER_STOP},
    CLIENT_CMD_DUMP: {"action": SERV_ORDER_DUMP},
    CLIENT_CMD_TICK: {"action": SERV_ORDER_TICK},
}

HWS_HWLOAD_FILENAME = "hwload_dump"
HWS_DUMP_NPZ = "npz"
HWS_DUMP_JSON = "json"
HWS_DUMP_FORMAT = os.getenv("HWSAMPLER_DUMP_FORMAT", HWS_DUMP_NPZ)

# Hardware specs
LBL_EPYC_7402 = "EPYC 7402"
LBL_A100 = "A100_SX40"
HWS_HARDWARE_SPECS = {
    LBL_EPYC_7402: {
        "PSU_IDLE": 60,  # From bench report on the internet
        "PSU_TDP": 180,  # From spec sheet
    },
    LBL_A100: {"PSU_TDP": 400, "MAX_VRAM": 40536},  # From spec sheet
}


HWS_HW_CPU = os.getenv("HWS_HW_CPU", LBL_EPYC_7402)
HWS_HW_GPU = os.getenv("HWS_HW_GPU", LBL_A100)
