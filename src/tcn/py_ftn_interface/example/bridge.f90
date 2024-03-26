module stub_interface_mod

   use iso_c_binding, only: c_int, c_float, c_double, c_ptr

   implicit none

   private
   public :: python_function_f

   ! CAN'T DO: Fortran doesn't allow to have C bindable array in user type
   !           we have to use the very verbose "list of parameters" approach
   ! type, bind(c) :: data_t
   !    integer(c_int) :: x
   !    integer(c_int) :: y
   ! end type

   interface

      subroutine python_function_f(x,y) bind(c, name='python_function')
         import c_int, c_float, c_double, c_ptr
         implicit none
         integer(c_int), intent(in) :: x,y
         ! real(c_float), dimension(*), intent(inout) :: u

      end subroutine python_function_f

   end interface

end module stub_interface_mod


