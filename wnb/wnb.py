import yaml
import munch
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon


def load_config(filename, Loader=yaml.FullLoader):
    with open(filename) as file:
        cfg = yaml.load(file, Loader=Loader)
        cfg = munch.munchify(cfg)
        return cfg


def build_settings(cfg):
    settings = munch.munchify({"loads": []})
    for i in range(len(cfg.loads)):
        load = cfg.loads[i]
        if hasattr(load, "mass"):
            new_load = load
            new_load.mass.current_value = new_load.mass.default
            settings.loads.append(new_load)
        elif hasattr(load, "volume"):
            new_load = load
            new_load.volume.current_value = new_load.volume.default
            settings.loads.append(new_load)
        else:
            new_load = munch.munchify({})
            settings.loads.append(new_load)
    return settings


def calculate_cg(cfg, settings):
    total_mass = 0.0
    total_moment = 0.0

    for i in range(len(settings.loads)):
        load = cfg.loads[i]
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
