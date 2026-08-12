# Run instructions

## Limitations

Currently it only allows matching from a BIN file (encoded + mask) and does not do the whole processing workflow from a single image:

This may be modified in the future to use XXX-one commands, but the current iris recognition project supports the purpose of this research.

## Workflow

```
python -m venv .venv
source .venv/bin/activate
pip install -r implementation/requirements.txt

python implementation/iris.py scan data/CASIA-Iris-Interval/ --output dataset.csv
python implementation/iris.py segment dataset.csv --output segmentation.csv --overlay overlay/
python implementation/iris.py normalize segmentation.csv --output-dir normalized --output-masks-dir masks/
python implementation/iris.py encode normalized/ masks/ --output-dir encoded/ --output-masks-dir encoded-masks/

python implementation/iris.py match-one encoded/007/L/S1007L01.bin encoded-masks/007/L/S1007L01.bin encoded/007/L/S1007L02.bin encoded-masks/007/L/S1007L02.bin

python implementation/iris.py identify data/CASIA-Iris-Interval/084/L/S1084L01.jpg encoded/ encoded-masks/
```

Remove 084 L .bin files for the first image on both encoded and encoded masks before running the last command.

Expected result:

```
Code: encoded/084/L/S1084L02.bin

Closest subject: 084, L
Hamming distance: 0.115
Match: True

Status: success
```
