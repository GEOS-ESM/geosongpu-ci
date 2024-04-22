#pragma once
#include <stdbool.h>

typedef struct
{
    float x;
    int y;
    bool b;
    // Magic number, see Fortran
    int i_am_123456789;
} data_t;

typedef union
{
    void *void_ptr;
    int int_value;
} union_t;

extern void python_function(data_t *, union_t *);
