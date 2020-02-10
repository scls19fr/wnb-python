import yaml
import munch
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

YAML_LOADER_DEFAULT = yaml.FullLoader


def load_index(filename, Loader=YAML_LOADER_DEFAULT):
    with open(filename) as file:
        index = yaml.load(file, Loader=Loader)
        index = munch.munchify(index)
        assert index.application == "wnb"
        assert index.usage == "aircrafts-index"
        assert index.file_format_version == "0.0.1"  # ToDo: use semver
        return index


def load_config(filename, Loader=YAML_LOADER_DEFAULT):
    with open(filename) as file:
        cfg = yaml.load(file, Loader=Loader)
        cfg = munch.munchify(cfg)
        assert cfg.application == "wnb"
        assert cfg.usage == "aircraft-wnb-data"
        assert cfg.file_format_version == "0.0.1"  # ToDo: use semver
        for i, pt in enumerate(cfg.centrogram):
            if hasattr(pt, "lever_arm") and hasattr(pt, "mass"):
                cfg.centrogram[i].moment = pt.lever_arm * pt.mass
            elif hasattr(pt, "moment") and hasattr(pt, "mass"):
                cfg.centrogram[i].lever_arm = pt.moment / pt.mass
            elif (
                hasattr(pt, "lever_arm")
                and hasattr(pt, "moment")
                and hasattr(pt, "mass")
            ):
                raise NotImplementedError(
                    "only 2 attributes out of 3 ('lever_arm', 'moment', 'mass') are required"
                )
            else:
                raise NotImplementedError("centrogram point attribute error")
        return cfg


def create_loads_list(cfg):
    loads = []
    for load in cfg.loads:
        if hasattr(load, "mass"):
            new_load = load
            new_load.mass.current_value = new_load.mass.default
            loads.append(new_load)
        elif hasattr(load, "volume"):
            new_load = load
            new_load.volume.current_value = new_load.volume.default
            loads.append(new_load)
        else:
            new_load = munch.munchify({})
            loads.append(new_load)
    return loads


def calculate_cg(cfg, loads):
    total_mass = 0.0
    total_moment = 0.0

    for i in range(len(loads)):
        load = loads[i]
        if hasattr(load, "mass"):
            mass = load.mass.current_value
        elif hasattr(load, "volume"):
            mass = (
                load.volume.current_value * cfg.constants.liquids[load.liquid].density
            )
        total_mass += mass
        moment = mass * load.lever_arm
        total_moment += moment
    lever_arm = total_moment / total_mass
    G = munch.munchify(
        {"mass": total_mass, "lever_arm": lever_arm, "moment": total_moment}
    )
    return G


def inside_centrogram(G, centrogram):
    polygon = []
    for pt in centrogram:
        polygon.append((pt.lever_arm, pt.mass))
    polygon = Polygon(polygon)
    point = Point(G.lever_arm, G.mass)
    return polygon.contains(point)
