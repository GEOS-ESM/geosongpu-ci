import pathlib
import pandas as pd
import plotly.express as px
from tcn.plots.colors import COLORS_RETRO

THIS_DIR = pathlib.Path(__file__).parent.resolve()
RESULT_DIR = THIS_DIR / "../../../results"


def _pie_plots(df, column_name: str, plot_name: str):
    filtered = df.filter(items=[column_name]).fillna("TBD")
    fig = px.pie(
        filtered.value_counts().reset_index(),
        values="count",
        names=column_name,
        color_discrete_sequence=list(COLORS_RETRO.values()),
        title=f"{column_name} ({len(filtered)})",
        template="simple_white",
    )
    fig.update_traces(textinfo="value+percent")
    fig.write_image(f"{plot_name}.png")


def summary(project_dir: str, data_name: str):
    df = pd.read_csv(
        f"{project_dir}/{data_name}",
        sep="\t",
    )

    # Global pie plots
    _pie_plots(df, "Milestone (NASA)", f"{project_dir}/milestones_distrib")
    _pie_plots(df, "Category", f"{project_dir}/category_distrib")
    _pie_plots(df, "Task Readiness", f"{project_dir}/task_ready_distrib")


if __name__ == "__main__":
    summary(
        project_dir=str(RESULT_DIR / "project/24W7"),
        data_name="SMT 2024-2026 - Backlog.tsv",
    )
