module stub_interface_mod

   use iso_c_binding, only: c_int, c_float, c_double

   implicit none

   private
   public :: python_function_f, data_t

   type, bind(c) :: data_t
      integer(c_int) :: x
      integer(c_int) :: y
   end type

   interface

      subroutine python_function_f(data) bind(c, name='python_function')
         import data_t

         implicit none
         type(data_t), intent(in) :: data

      end subroutine python_function_f

   end interface

end module stub_interface_mod


