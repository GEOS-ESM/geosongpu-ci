import socket
import json
from tcn.tools.hws.constants import SOCKET_FILENAME, CLIENT_CMDS


def client_main(order: str, dump_name: str):
    filtered_order = CLIENT_CMDS[order]
    filtered_order["dump_name"] = dump_name
    data = json.dumps(filtered_order)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.connect(SOCKET_FILENAME)
    server.send(data.encode("utf8"))


def cli(command: str, dump_name: str):
    if command in CLIENT_CMDS.keys():
        client_main(command, dump_name)
    else:
        raise RuntimeError(
            f"[HWS Client] Unknown cmds {command} as first argument of the executable"
        )
