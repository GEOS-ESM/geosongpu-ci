import subprocess
from time import sleep
from dataclasses import dataclass


@dataclass
class SlurmConfiguration:
    account: str = "j1013"
    constraint: str = "rome"
    qos: str = "4n_a100"
    partition: str = "gpu_a100"
    nodes: int = 1
    ntasks: int = 1
    ntasks_per_node: int = 1
    sockets_per_node: int = 1
    gpus_per_node: int = 0
    mem_per_gpu: str = "40G"
    time: str = "02:00:00"
    output: str = "log.%t.out"

    def srun_bash(self, wrapper: str, executable_name: str) -> str:
        if self.gpus_per_node != 0:
            gpu_line = (
                f"--gpus-per-node={self.gpus_per_node} --mem-per-gpu={self.mem_per_gpu}"
            )
        else:
            gpu_line = ""
        return (
            "srun -A j1013 -C rome "
            f" --qos={self.qos} --partition={self.partition} "
            f" --nodes={self.nodes} --ntasks={self.ntasks} "
            f" --ntasks-per-node={self.ntasks_per_node} "
            f" --sockets-per-node={self.sockets_per_node} "
            f" {gpu_line} "
            f" --time={self.time} "
            f" --output={self.output} "
            f" {wrapper} {executable_name}",
        )


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
