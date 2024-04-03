from data_desc import Data_py_t


def some_function(data: Data_py_t):
    print(data)
    print((type(data)))
    print(hasattr(data, "x"))
