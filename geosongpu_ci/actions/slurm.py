from dataclasses import dataclass
from typing import Optional


@dataclass
class SlurmConfiguration:
    """Slurm job options with common default for our project

    This class includes the common configuration we use to run validation
    and benchmarking.
    """

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
        """Code for an srun command"""
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
            f" {wrapper} {executable_name}"
        )

    @classmethod
    def slurm_6CPUs_6GPUs(cls, output: Optional[str] = None) -> "SlurmConfiguration":
        """1/2 node configuration on Discover with A100 & Rome Epyc"""
        return cls(
            nodes=2,
            ntasks=6,
            ntasks_per_node=3,
            sockets_per_node=2,
            gpus_per_node=3,
            mem_per_gpu="40G",
            output=output or cls.output,
        )

    @classmethod
    def slurm_72CPUs(cls, output: Optional[str] = None) -> "SlurmConfiguration":
        """1/2 node configuration on Discover with Rome Epyc"""
        return SlurmConfiguration(
            nodes=2,
            ntasks=72,
            ntasks_per_node=48,
            sockets_per_node=2,
            output=output or cls.output,
        )

    @classmethod
    def slurm_96CPUs_8GPUs(cls, output: Optional[str] = None) -> "SlurmConfiguration":
        """2 nodes configuration on Discover with A100 & Rome Epyc"""
        return cls(
            nodes=2,
            ntasks=96,
            ntasks_per_node=48,
            sockets_per_node=2,
            gpus_per_node=4,
            mem_per_gpu="40G",
            output=output or cls.output,
        )
