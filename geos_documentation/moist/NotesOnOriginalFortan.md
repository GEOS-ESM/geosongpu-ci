# Notes on the Port

## Dead code

- Aer Activation (`GEOSmoist_GridComp/aer_actv_single_moment.F90`)
The pre-loop before computation in

```fortan
      !--- determing aerosol number concentration at cloud base
      DO j=1,JM
        Do i=1,IM 
             k            = kpbli(i,j)
             tk           = T(i,j,k)              ! K
             press        = plo(i,j,k)            ! Pa     
             air_den      = press*28.8e-3/8.31/tk ! kg/m3
      ENDDO;ENDDO
```
