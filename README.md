# Activate venv

```
source .venv/bin/activate
```

## Run DPy

```
NOT YET INSTALLED ON WSL
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

## Run SCB tests

Specify the implementation path in the `--entrypoint` flag.

Or use the solutions/ folder to ensure all tests passes there.

```
uv run pytest scb-problems-sols-tests/dag_execution/tests/test_checkpoint_1.py --entrypoint "python scb-problems-sols-tests/dag_execution/solutions/checkpoint_1/launch.py" --checkpoint checkpoint_1
```

When doing this make sure the launch file is actually named launch.py.

## Docker container

BEFORE DOING THIS, RUN `pip freeze > requirements.txt` TO UPDATE IT

Build the docker container using

```
docker build -t scb .
```

To ensure a fresh environment everytime the agent works on an issue, and to ensure it only has access
to the current problem description (Not the solutions or the tests), run

.claude (settings) and .claudeignore is copied, may be removed later if not used.

```
docker run --rm -it -v "$HOME/.claude:/root/.claude" -v "$PWD/.claudeignore:/root/.claudeignore" -v "$PWD/datasets/slopCodeBench/scb-problems:/scb-problems" scb bash
```

this way it creates the container "scb" and is removed on exit.
