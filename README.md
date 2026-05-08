# Activate venv

```
.\.venv\Scripts\activate
```

## Run DPy

```
.\DPy.exe [path]
```

## Run pylint

Experimental. Checks for duplicate code and protected access respectively.

```
pylint --disable=all --enable=R0801,W0212
```

## Run pydeps

```
pydeps [path]
```

Edges point from the imported module unless the `--reverse` tag is set:
an edge from module A -> B means B imports A.
A module with many outgoing edges is likely a god module.
