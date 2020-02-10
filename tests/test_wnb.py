import pytest
import wnb


def test_load_sample_config():
    cfg = wnb.load_config("./data/f-bubk.yml")
    assert cfg.file_format_version == "0.0.1"

    assert cfg.weight_and_balance.version == "1"
    assert cfg.weight_and_balance.date == "21/03/2006"

    assert cfg.aircraft.designation == "Cessna 150"
    assert cfg.aircraft.type == "C150"
    assert cfg.aircraft.immat == "F-BUBK"
    assert cfg.aircraft.picture == "f-bubk.png"
    assert cfg.aircraft.owner == "Aéro-Club du Poitou"
    assert cfg.aircraft.owner_picture == "acp.png"
    assert cfg.aircraft.comment == ""

    assert cfg.constants.liquids.fuel_100LL.density == 0.72

    assert len(cfg.centrogram) == 5
    for i, centrogram_point in enumerate(cfg.centrogram):
        assert centrogram_point.designation == "Pt%d" % (i + 1)

    assert cfg.centrogram[0].designation == "Pt1"
    assert cfg.centrogram[0].mass == 250
    assert cfg.centrogram[0].lever_arm == 0.8

    assert len(cfg.loads) == 5
    assert cfg.loads[0].designation == "Empty aircraft"
    assert cfg.loads[0].lever_arm == 0.862
    assert cfg.loads[0].mass.default == 520
    assert cfg.loads[0].comment == ""
    assert cfg.loads[1].designation == "Pilot"
    assert cfg.loads[1].lever_arm == 0.993
    assert cfg.loads[1].mass.default == 77
    assert cfg.loads[1].mass.min == 0
    assert cfg.loads[1].mass.max == 150
    assert cfg.loads[1].mass.step == 1
    assert cfg.loads[1].comment == ""


def test_build_settings():
    cfg = wnb.load_config("./data/f-bubk.yml")
    settings = wnb.build_settings(cfg)
    for i in range(len(cfg.loads)):
        if hasattr(cfg.loads[i], "mass"):
            assert settings.loads[i].mass.current_value == cfg.loads[i].mass.default
        elif hasattr(cfg.loads[i], "volume"):
            assert settings.loads[i].volume.current_value == cfg.loads[i].volume.default


def test_calculate_center_of_gravity():
    cfg = wnb.load_config("./data/f-bubk.yml")
    settings = wnb.build_settings(cfg)
    G = wnb.calculate_cg(cfg, settings)
    assert G.mass == 668.2
    assert G.lever_arm == pytest.approx(0.907, abs=0.001)
    assert G.moment == pytest.approx(606.375, abs=0.001)


def test_inside_centrogram():
    cfg = wnb.load_config("./data/f-bubk.yml")

    # in range
    settings = wnb.build_settings(cfg)
    G = wnb.calculate_cg(cfg, settings)
    assert wnb.inside_centrogram(G, cfg.centrogram)

    # overweight
    settings = wnb.build_settings(cfg)
    settings.loads[2].mass.current_value = 60  # Passenger
    G = wnb.calculate_cg(cfg, settings)
    assert not wnb.inside_centrogram(G, cfg.centrogram)

    # out of range / back limit
    settings = wnb.build_settings(cfg)
    settings.loads[1].mass.current_value = 90  # Pilot
    settings.loads[3].mass.current_value = 54  # Luggage
    G = wnb.calculate_cg(cfg, settings)
    assert not wnb.inside_centrogram(G, cfg.centrogram)

    # out of range / front limit
    # settings = wnb.build_settings(cfg
    # settings.loads[1].mass.current_value = 100;  // Pilot
    # settings.loads[2].mass.current_value = 0;  // Passenger
    # settings.loads[3].mass.current_value = 0;  // Luggage
    # settings.loads[4].volume.current_value = 0 / cfg.constants.liquids.fuel_100LL.density;  // Fuel
    # G = wnb.calculate_cg(cfg, settings
    # console.log(G
    # assert not wnb.inside_centrogram(G, cfg.centrogram)

    # too light
    settings = wnb.build_settings(cfg)
    settings.loads[0].mass.current_value = 200  # Empty aircraft
    settings.loads[1].mass.current_value = 0  # Pilot
    settings.loads[2].mass.current_value = 0  # Passenger
    settings.loads[3].mass.current_value = 0  # Luggage
    settings.loads[4].volume.current_value = (
        0 / cfg.constants.liquids.fuel_100LL.density
    )  # Fuel
    G = wnb.calculate_cg(cfg, settings)
    assert not wnb.inside_centrogram(G, cfg.centrogram)
