import subprocess
from time import sleep


def wait_for_sbatch(job_id: str):
    sleep(5)  # wait 5 seconds for SLURM to enter prolog
    running = True
    while running:
        sacct_result = subprocess.run(
            ["sacct", "-j", job_id, "-o", "state"], stdout=subprocess.PIPE
        ).stdout.decode("utf-8")
        running = False
        for state in sacct_result.split("\n")[2:]:
            if state.strip() in ["RUNNING", "PENDING"]:
                running = True
                break
