#pragma once
#include <stdbool.h>

typedef struct
{
    float x;
    int y;
    bool b;
} data_t;

typedef union
{
    void *void_ptr;
    int int_value;
} union_t;

extern void python_function(data_t *, union_t *);
