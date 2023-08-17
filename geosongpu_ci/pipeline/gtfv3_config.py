from dataclasses import dataclass
from typing import Optional


@dataclass
class GTFV3Config:
    """Configuration for GTFV3"""

    FV3_DACEMODE: str = "BuildAndRun"
    PACE_CONSTANTS: str = "GEOS"
    PACE_FLOAT_PRECISION: int = 32
    PACE_LOGLEVEL: str = "DEBUG"
    GTFV3_BACKEND: str = "dace:gpu"

    def sh(self) -> str:
        return (
            f"export FV3_DACEMODE={self.FV3_DACEMODE}\n"
            f"export PACE_CONSTANTS={self.PACE_CONSTANTS}\n"
            f"export PACE_FLOAT_PRECISION={self.PACE_FLOAT_PRECISION}\n"
            f"export PACE_LOGLEVEL={self.PACE_LOGLEVEL}\n"
            f"export GTFV3_BACKEND={self.GTFV3_BACKEND}\n"
            f"export PER_DEVICE_PROCESS=12\n"  # default for Discover
            f"export PYTHONOPTIMIZE=1\n"
        )

    @classmethod
    def dace_gpu_32_bit_BAR(cls, dacemode: Optional[str] = None) -> "GTFV3Config":
        return cls(FV3_DACEMODE=dacemode or cls.FV3_DACEMODE)

    @classmethod
    def fortran(cls) -> "GTFV3Config":
        return cls(FV3_DACEMODE="Python", GTFV3_BACKEND="fortran")

    def backend_sanitized(self):
        return self.GTFV3_BACKEND.replace(":", "")
