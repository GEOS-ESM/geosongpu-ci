program test
   use stub_interface_mod, only: python_function_f
   use iso_c_binding, only: c_f_pointer

   implicit none

   integer :: x, y
   real, allocatable :: u(:,:,:)

   allocate(u(2, 2, 2))
   u = 36

   x = 42

   y = 24

   call python_function_f(x, y)

   print *, 'test'
end program test

