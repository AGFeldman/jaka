Example usage:

`python run.py cases/case0.json`

Or, if you want to be fancy:

`time python -m cProfile -s time run.py cases/case0.json > out`

Plots are saved as png files under the "output" directory.

Conventions

If a module involves any division, use `from __future__ import division`

Internal unit conventions: All time units are in seconds. All size units are in *bits*. So, rate units are bits per second. 

Unit conventions for quantities that users specify should be consistent with these internal conventions. So, input `64 * 10**3 * 8` for a 64 KB buffer size.

Statistical information given to the user should specify its own units and doesn't need to follow the above conventions.
