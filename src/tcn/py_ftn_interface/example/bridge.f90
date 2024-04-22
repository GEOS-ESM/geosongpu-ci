module stub_interface_mod

   use iso_c_binding, only: c_int, c_float, c_double, c_bool

   implicit none

   private
   public :: python_function_f, data_t

   type, bind(c) :: data_t
      real(c_float) :: x
      integer(c_int) :: y
      logical(c_bool) :: b
   end type

   interface

      subroutine python_function_f(data, value) bind(c, name='python_function')
         import data_t, c_int

         implicit none
         type(data_t), intent(in) :: data
         integer(kind=c_int), intent(in) :: value

      end subroutine python_function_f

   end interface

end module stub_interface_mod


