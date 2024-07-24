# DSL Patterns

A repository of small self-contained examples to demonstrate how to write different algorithmics patterns under DSL or document failure to port such patterns (and eventually the workarounds)

The folder should remain as flat as possible and each file should follow the naming pattern: [Do/Dont/Cant/WIP]_[DescriptiveName].py, with:

 - `Do`: the stack knows how to handle this pattern in a satisfactory way for now. No work planned.
 - `Dont`: the stack _disallows_ this pattern. Provide a _why_, an expected error example and potentially a workaround when applicable.
 - `Cant`: the stack lacks the feature to handle this case. Show the Numpy/Python workaround.
 - `WIP`: a workaround exist but is unsatisfactory. Show said workaround.

Then the top of the file should have a docstrings with:
 
 - Date last updated
 - Ticket link (if applicable)
 - Description of the pattern
 - Original Fortran code (if applicable)
 - Performance related explanation (if applicable)

