def one_gpu_srun(log, time="00:10:00") -> str:
    return (
        "srun -A j1013 -C rome --qos=4n_a100 --partition=gpu_a100 "
        f" --mem-per-gpu=40G --gres=gpu:1 --time={time} "
        f" --output={log}"
    )
