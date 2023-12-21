from typing import Dict, Type


class Registry:
    registry: Dict[str, Type] = {}

    @classmethod
    def register(cls, to_register_cls: Type):
        if not isinstance(to_register_cls, type):
            raise RuntimeError("Register only registers function")
        cls.registry[to_register_cls.__name__] = to_register_cls

        return to_register_cls
