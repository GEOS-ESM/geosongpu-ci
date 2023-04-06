from typing import Callable, ClassVar


class Registry:
    registry = {}

    @classmethod
    def register(cls) -> Callable:
        def inner_wrapper(wrapped_class: type) -> type:
            if not isinstance(wrapped_class, function):
                raise RuntimeError("Register only registers function")
            cls.registry[wrapped_class.__name__] = wrapped_class
            return wrapped_class

        return inner_wrapper
