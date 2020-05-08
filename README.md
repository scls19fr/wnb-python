# wnb-python

Calculate weight and balance of aircraft

## Install the dependencies

Install Python (Anaconda Python) / Kivy / click

## Console

### Index of aircrafts

```bash
$ python wnb/wnb_console.py --index data/index.yml
```

### Load of an aicraft

```bash
$ python wnb/wnb_console.py --config data/f-bubk.yml
```

## GUI

```bash
$ python wnb/wnb_kivy.py data/f-bubk.yml
```

![screenshot1](screenshot1.png "Screenshot1")
![screenshot2](screenshot2.png "Screenshot2")

## Unit tests

```bash
$ pytest
```
