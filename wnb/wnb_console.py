import click
import os
import yaml
from termcolor import colored, cprint


from wnb import (
    YAML_LOADER_DEFAULT,
    load_index,
    load_config,
    build_settings,
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
            print("Index out of range (must be in [%d;%d])" % (1, len(index.aircrafts)))
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


def choose_loads(cfg):
    settings = build_settings(cfg)
    for i, load in enumerate(settings.loads):
        # print(load)
        print(f"{load.designation} ", end="")
        if hasattr(load, "mass"):
            new_val = input(f"mass value (default: {load.mass.default}): ")
            if new_val == "":
                new_val = load.mass.default
            else:
                new_val = float(new_val)
            settings.loads[i].mass.current_value = new_val
        elif hasattr(load, "volume"):
            new_val = input(f"volume value (default: {load.volume.default}): ")
            if new_val == "":
                new_val = load.volume.default
            else:
                new_val = float(new_val)
            settings.loads[i].volume.current_value = new_val
        else:
            raise NotImplementedError("load should have mass or volume attribute")
    print("")
    return settings


@click.command()
@click.option("--index", default="")
@click.option("--config", default="")
def load(index, config):
    if index != "" and config == "":
        index_path, _ = os.path.split(index)
        index = load_index(index)
        cfg = choose_config(index, index_path)
    elif index == "" and config != "":
        cfg = load_config(config)
    else:
        raise NotImplementedError("Both index and config can't be empty")

    # display_config_basic_format(cfg)
    display_config(cfg)

    settings = choose_loads(cfg)

    G = calculate_cg(cfg, settings)
    print("G:")
    display_config_basic_format(G, spaces=2)

    if inside_centrogram(G, cfg.centrogram):
        text = colored("G is inside centrogram", "green", attrs=["reverse"])
        cprint(text)
    else:
        text = colored(
            "!!! G is outside centrogram !!!", "red", attrs=["reverse", "blink"]
        )
        cprint(text)


if __name__ == "__main__":
    load()
