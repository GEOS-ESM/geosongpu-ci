import pathlib
import pandas as pd
import plotly.express as px
import json
from tcn.plots.colors import COLORS_RETRO_HIGH_CONTRAST

THIS_DIR = pathlib.Path(__file__).parent.resolve()
RESULT_DIR = THIS_DIR / "../"


def summary(project_dir: str, data_name: str):
    with open(f"{project_dir}/{data_name}") as f:
        data = json.load(f)

    df = pd.DataFrame(
        [
            data["latency"]["message_size"],
            data["latency"]["sles12"],
            data["latency"]["sles15"],
        ]
    ).T
    df.columns = ["message_size", "sles12", "sles15"]  # type:ignore
    fig = px.line(
        df,
        x="message_size",
        y=["sles12", "sles15"],
        log_x=True,
        color_discrete_sequence=list(COLORS_RETRO_HIGH_CONTRAST.values()),
        title="Latency on Discover (lower is better)",
        template="simple_white",
        labels={
            "message_size": "Message size (B)",
            "value": "Bandwidth (B/s)",
            "variable": "OS",
        },
    )
    fig.write_image(f"{project_dir}/latency.png")

    df = pd.DataFrame(
        [
            data["bandwith_d_d"]["message_size"],
            data["bandwith_d_d"]["discover"],
            data["bandwith_d_d"]["discover_host"],
            data["bandwith_d_d"]["perlmutter"],
        ]
    ).T
    df.columns = [
        "message_size",
        "discover",
        "discover_host",
        "perlmutter",
    ]  # type:ignore
    fig = px.line(
        df,
        x="message_size",
        y=["discover", "discover_host", "perlmutter"],
        log_x=True,
        color_discrete_sequence=list(COLORS_RETRO_HIGH_CONTRAST.values()),
        title="Peak bandwith (higher is better)",
        template="simple_white",
        labels={
            "message_size": "Message size (B)",
            "value": "Bandwidth (B/s)",
            "variable": "Machine",
        },
    )
    fig.write_image(f"{project_dir}/bandwith.png")


if __name__ == "__main__":
    summary(
        project_dir=str(RESULT_DIR / "mpi_gpu_rdma"),
        data_name="24W7.json",
    )
