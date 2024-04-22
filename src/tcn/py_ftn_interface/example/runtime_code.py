from data_desc import Data_py_t
import inspect


def check_function(data: Data_py_t):
    print(f"Data comes as {data} of type {type(data)}")
    members = inspect.getmembers(Data_py_t)
    keys = list(
        list(filter(lambda x: x[0] == "__dataclass_fields__", members))[0][1].values()
    )
    for k in keys:
        print(f"{k.name} of value {getattr(data, k.name)}")
