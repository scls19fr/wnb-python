"""
Calculate weight and balance of aircraft

$ pip install python-i18n[YAML]
$ pip install termcolor
$ 

Select from a list of aircrafts
$ python wnb/wnb_console.py --index data/index.yml

Choose weight and balance data of a given aircraft
and display centrogram with lever arm as x-axis
$ python wnb/wnb_console.py --config data/f-bubk.yml

Choose weight and balance data of a given aircraft
and display centrogram with moment as x-axis
$ python wnb/wnb_console.py --config data/f-bubk.yml --centrogram moment
"""

import click
import os
import yaml
import i18n
from termcolor import colored, cprint

DEFAULT_BACKEND = "matplotlib"
ALLOWED_BACKENDS = ["plotext", "matplotlib"]
ALLOWED_XAXIS = ["lever_arm", "moment"]

from wnb import (
    YAML_LOADER_DEFAULT,
    load_index,
    load_config,
    create_loads_list,
    calculate_cg,
    inside_centrogram,
)


def choose_config(index, index_path):
    while True:
        print("Index")
        print("Title: %s" % index.title)
        for i, aircraft in enumerate(index.aircrafts, 1):
            print(f"{i}: {aircraft}")
        try:
            aircraft_id = int(input("Aicraft: "))
            if aircraft_id in range(1, len(index.aircrafts) + 1):
                aircraft_fname = os.path.join(
                    index_path, index.aircrafts[aircraft_id - 1]
                )
            else:
                raise IndexError
            cfg = load_config(aircraft_fname)
            break
        except ValueError:
            pass
        except (KeyboardInterrupt, SystemExit):
            raise
        except IndexError:
            text = colored(
                "Index out of range (must be in [%d;%d])" % (1, len(index.aircrafts)),
                "magenta",
                attrs=["reverse"],
            )
            cprint(text)
            print()
        except:
            raise
    return cfg


def display_config_basic_format(cfg, spaces=0):
    s = yaml.safe_dump(cfg)
    for line in s.split("\n"):
        print(" " * spaces + line)


def display_config(cfg):
    print("aircraft:")
    print(f"  designation: {cfg.aircraft.designation}")
    print(f"  type: {cfg.aircraft.type}")
    print(f"  immat: {cfg.aircraft.immat}")
    print(f"  picture: {cfg.aircraft.picture}")
    print(f"  owner: {cfg.aircraft.owner}")
    print(f"  owner_picture: {cfg.aircraft.owner_picture}")
    print(f"  comment: {cfg.aircraft.comment}")
    print("")


def input_loads(cfg):
    loads = create_loads_list(cfg)
    for i, load in enumerate(loads):
        # print(load)
        if hasattr(load, "mass"):
            new_val = input(
                "%s mass (default: %.1f): " % (load.designation, load.mass.default)
            )
            if new_val == "":
                new_val = load.mass.default
            else:
                new_val = float(new_val)
            loads[i].mass.current_value = new_val
        elif hasattr(load, "volume"):
            new_val = input(
                "%s volume (default: %.1f): " % (load.designation, load.volume.default)
            )
            if new_val == "":
                new_val = load.volume.default
            else:
                new_val = float(new_val)
            loads[i].volume.current_value = new_val
        else:
            raise NotImplementedError("load should have mass or volume attribute")
    print("")
    return loads


def translate(cfg):
    for i, load in enumerate(cfg.loads):
        # txt = '.'.join(['messages', cfg.loads[i].designation])  # i18n with namespace
        txt = cfg.loads[i].designation
        cfg.loads[i].designation = i18n.t(txt)


@click.command()
@click.option(
    "--xaxis",
    default="lever_arm",
    help="x-axis of centrogram - must be in %s" % ALLOWED_XAXIS,
)
@click.option("--index", default="")
@click.option("--config", default="")
@click.option(
    "--backend",
    default=DEFAULT_BACKEND,
    help="Plotting backend - must be in %s" % ALLOWED_BACKENDS,
)
def load(xaxis, index, config, backend):
    script_path, _ = os.path.split(os.path.abspath(__file__))
    i18n.load_path.append(os.path.join(script_path, "translations"))
    i18n.set("filename_format", "{locale}.{format}")  # remove i18n namespace
    import locale

    cur_locale = locale.getlocale()[0][:2]
    i18n.set("locale", cur_locale)

    if xaxis not in ALLOWED_XAXIS:
        raise NotImplementedError(
            i18n.t("unknown_xaxis").format(xaxis=xaxis, allowed_xaxis=ALLOWED_XAXIS)
        )

    if index != "" and config == "":
        index_path, _ = os.path.split(index)
        index = load_index(index)
        cfg = choose_config(index, index_path)
    elif index == "" and config != "":
        cfg = load_config(config)
    else:
        raise NotImplementedError(i18n.t("error_index_config_both_empty"))

    if backend not in ALLOWED_BACKENDS:
        raise NotImplementedError(
            i18n.t("unknown_backend").format(
                backend=backend, allowed_backends=ALLOWED_BACKENDS
            )
        )

    translate(cfg)

    # display_config_basic_format(cfg)
    display_config(cfg)

    loads = input_loads(cfg)

    G = calculate_cg(cfg, loads)

    print("Centrogram:")
    display_config_basic_format(cfg.centrogram, spaces=2)

    print("G:")
    display_config_basic_format(G, spaces=2)

    y_label = "mass (kg)"
    if xaxis == "lever_arm":
        lst_x = [pt.lever_arm for pt in cfg.centrogram]
        lst_x.append(lst_x[0])
        lst_y = [pt.mass for pt in cfg.centrogram]
        lst_y.append(lst_y[0])
        xG, yG = G.lever_arm, G.mass
        x_label = "lever_arm (m)"
    elif xaxis == "moment":
        lst_x = [pt.moment for pt in cfg.centrogram]
        lst_x.append(lst_x[0])
        lst_y = [pt.mass for pt in cfg.centrogram]
        lst_y.append(lst_y[0])
        xG, yG = G.moment, G.mass
        x_label = "moment (kg.m)"

    is_inside_centrogram = inside_centrogram(G, cfg.centrogram)

    if is_inside_centrogram:
        text = colored(i18n.t("G_is_inside_centrogram"), "green", attrs=["reverse"])
        cprint(text)
        color_G = "green"
    else:
        text = colored(
            "!!! %s !!!" % i18n.t("G_is_outside_centrogram"),
            "red",
            attrs=["reverse", "blink"],
        )
        cprint(text)
        color_G = "red"
    print("")

    if backend == "plotext":
        import plotext.plot as plx

        lst_x.append(xG)
        lst_y.append(yG)
        plx.scatter(lst_x, lst_y, axes=True, cols=60, rows=20)
        plx.show()
    elif backend == "matplotlib":
        import matplotlib.pyplot as plt

        plt.plot(lst_x, lst_y)
        plt.scatter(xG, yG, c=color_G)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.show()


if __name__ == "__main__":
    load()
