import socket
import json
from geosongpu_ci.tools.hws.constants import SOCKET_FILENAME, CLIENT_CMDS


def client_main(order=str):
    data = json.dumps(CLIENT_CMDS[order])
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.connect(SOCKET_FILENAME)
    server.send(data.encode("utf8"))


def cli(command: str):
    if command in CLIENT_CMDS.keys():
        client_main(command)
    else:
        raise RuntimeError(
            f"[HWS Client] Unknown cmds {command} as first argument of the executable"
        )
