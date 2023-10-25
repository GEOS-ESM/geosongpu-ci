# Python <-> Fortan interface generator

## Porting validation generator

Generates a call that will compare the outputs of the reference and the ported code.

WARNING: the generator work on the hypothesis that the fortran<>python interface and the reference fortran share the argument signature.

Yaml schema:

```yaml
bridge:
    - name: function_that_will_be_validated
      arguments:
        inputs: ...
        inouts: ...
        outputs: ...
      validation:
        reference:
          call: fortran_routine_name
          mod: fortran_module_name_to_use_to_get_to_call
```
