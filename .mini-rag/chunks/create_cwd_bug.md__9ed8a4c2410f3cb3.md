## Root Cause (suspected)
The `create` command likely uses `Path.cwd()` instead of resolving the `-s` argument to an absolute path.
