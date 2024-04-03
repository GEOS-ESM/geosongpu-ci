program test
   use stub_interface_mod, only: python_function_f, data_t

   implicit none

   type(data_t) :: d
   d = data_t(42, 24)
   call python_function_f(d, 39)

   print *, 'test'
end program test

