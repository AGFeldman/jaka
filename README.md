[![Build Status](https://travis-ci.org/AGFeldman/jaka.svg?branch=master)](https://travis-ci.org/AGFeldman/jaka)

Example usage:

`python run.py cases/case0.json`

Or, if you want to be fancy:

`time python -m cProfile -s time run.py cases/case0.json case0`

Run some tests with `bash test_all.sh`.

Usage is `python run.py case_name.json [output_name]`. If `output_name` is not provided, then it defaults to `"output"`. Two files are generated: `output_name.log` and `output_name.pdf`. `output_name.pdf` has graphs of all the stats.

Conventions

If a module involves any division, use `from __future__ import division`

Internal unit conventions: All time units are in seconds. All size units are in *bits*. So, rate units are bits per second. 

Unit conventions for quantities that users specify should be consistent with these internal conventions. So, input `64 * 10**3 * 8` for a 64 KB buffer size.

Statistical information given to the user should specify its own units and doesn't need to follow the above conventions.
