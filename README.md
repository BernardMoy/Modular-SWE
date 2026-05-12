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
uv run pytest scb-problems-sols-tests/dag_execution/tests/test_checkpoint_1.py \
    --entrypoint "python scb-problems-sols-tests/dag_execution/solutions/checkpoint_1/launch.py" \
    --checkpoint checkpoint_1
```

When doing this make sure the launch file is actually named launch.py.

## Docker container, and run agent

BEFORE DOING THIS, RUN `pip freeze > requirements.txt` TO UPDATE IT

Build the docker container using

```
docker build -t scb .
```

To ensure a fresh environment everytime the agent works on an issue, and to ensure it only has access
to the current problem description (Not the solutions or the tests), run

.claude (settings) and .claudeignore is copied, may be removed later if not used.
Only the checkpoint_N.md file and the config.yaml file under a problem is copied for a specific checkpoint.

To run the container: Start from the root directory

1. Make a directory (clear the previous directory first)

```
rm -rf agent_workspace
mkdir -p agent_workspace
```

2. Copy what is available for the agent to read, including

- checkpoint_N.md
- config.yaml
- checkpoint\_(N-1)/ (previous implementation, if available)

```
cp "$PWD/datasets/slopCodeBench/scb-problems/cfgpipe/config.yaml" agent_workspace/
cp "$PWD/datasets/slopCodeBench/scb-problems/cfgpipe/checkpoint_1.md" agent_workspace/
```

Only when checkpoint_N N>1

```
cp -r "$PWD/datasets/slopCodeBench/scb-problems/cfgpipe/implementations/checkpoint_1" agent_workspace/
```

3. Create volume mounts and run docker container as a non root user, copying only the `agent_workspace` directory
   (Currently, it will show I have no name! -- to be fixed later. -e is for claude to work. )

```
docker run --rm -it \
  --user "$(id -u):$(id -g)" \
  -e HOME=/home/bernardmoy \
  -v "$HOME/.claude:/home/bernardmoy/.claude" \
  -v "$HOME/.claude.json:/home/bernardmoy/.claude.json" \
  -v "$PWD/agent_workspace:/agent_workspace" \
  scb bash
```

this way it creates the container "scb" and is removed on exit.

4. Implement solution in a folder named checkpoint_N/ by calling the agent

5. Exit the container, then move the solution back to the problem implementation:
   The implementations directory need to be created, otherwise it gets renamed to checkpoint_N

```
mkdir -p datasets/slopCodeBench/scb-problems/cfgpipe/implementations
mv agent_workspace/checkpoint_1 datasets/slopCodeBench/scb-problems/cfgpipe/implementations/
```

6. Run the tests! (In the root dir)

With reference solution (All should pass):

```
uv run pytest datasets/slopCodeBench/scb-problems-sols-tests/cfgpipe/tests/test_checkpoint_1.py \
  --entrypoint "python datasets/slopCodeBench/scb-problems-sols-tests/cfgpipe/solutions/checkpoint_1/cfgpipe.py" \
  --checkpoint checkpoint_1
```

With implemented solution (Only some tests should pass):

```
uv run pytest datasets/slopCodeBench/scb-problems-sols-tests/cfgpipe/tests/test_checkpoint_1.py  \
  --entrypoint "python datasets/slopCodeBench/scb-problems/cfgpipe/implementations/checkpoint_1/cfgpipe.py" \
  --checkpoint checkpoint_1
```
