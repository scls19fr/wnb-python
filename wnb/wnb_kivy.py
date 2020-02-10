import i18n

import os

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider

from math import sin
from kivy_garden.graph import Graph, MeshLinePlot, ScatterPlot

from wnb import (
    YAML_LOADER_DEFAULT,
    load_index,
    load_config,
    create_loads_list,
    calculate_cg,
    inside_centrogram,
)

ALLOWED_XAXIS = ["lever_arm", "moment"]


def define_load_slider_properties(slider_properties):
    slider_properties.current_value = slider_properties.default
    if not hasattr(slider_properties, "step"):
        slider_properties.step = 1
    if hasattr(slider_properties, "min") and hasattr(slider_properties, "max"):
        slider_properties.enabled = True
    else:
        slider_properties.min = slider_properties.default - slider_properties.step
        slider_properties.max = slider_properties.default + slider_properties.step
        slider_properties.enabled = False
    return slider_properties


class SlidersLayout(GridLayout):
    sliders = []
    lbl_values = []

    def __init__(self, cfg, loads, **kwargs):
        super(SlidersLayout, self).__init__(**kwargs)
        self.cols = 3
        self.cfg = cfg
        self.loads = loads
        for load in self.loads:
            txt = load.designation
            txt = i18n.t(txt)
            lbl = Label(text=txt)
            self.add_widget(lbl)
            if hasattr(load, "mass"):
                lbl.text += " (kg)"
                slider_properties = define_load_slider_properties(load.mass)
            elif hasattr(load, "volume"):
                lbl.text += " (L)"
                slider_properties = define_load_slider_properties(load.volume)
            slider = Slider(
                min=slider_properties.min,
                max=slider_properties.max,
                value=slider_properties.default,
            )
            slider.disabled = not slider_properties.enabled
            self.sliders.append(slider)
            self.add_widget(self.sliders[-1])
            self.lbl_values.append(Label(text="Valeur"))
            self.add_widget(self.lbl_values[-1])
        self.update()

    def update(self):
        for i, slider in enumerate(self.sliders):
            self.lbl_values[i].text = "%d" % slider.value
            if hasattr(self.loads[i], "mass"):
                self.loads[i].mass.current_value = slider.value
            elif hasattr(self.loads[i], "volume"):
                self.loads[i].volume.current_value = slider.value


class AircraftLoadLayout(GridLayout):
    def __init__(self, xaxis, aircraft_config, **kwargs):
        super(AircraftLoadLayout, self).__init__(**kwargs)
        self.cols = 1
        self.cfg = load_config(aircraft_config)
        self.loads = create_loads_list(self.cfg)

        self.sliders = SlidersLayout(self.cfg, self.loads)
        self.add_widget(self.sliders)

        self.lbl_center_gravity = Label(text="")
        self.add_widget(self.lbl_center_gravity)

        self.graph = Graph(xlabel='X', ylabel='Y', x_ticks_minor=0.05,
        x_ticks_major=0.5, y_ticks_major=100,
        y_grid_label=True, x_grid_label=True, padding=5,
        x_grid=True, y_grid=True, xmin=0.7, xmax=1.1, ymin=0, ymax=1000)
        self.mesh_line_plot = MeshLinePlot(color=[0, 0, 1, 1])
        self.mesh_line_plot.points = [(pt.lever_arm, pt.mass) for pt in self.cfg.centrogram]
        self.mesh_line_plot.points.append(self.mesh_line_plot.points[0])
        self.graph.add_plot(self.mesh_line_plot)

        self.add_widget(self.graph)

        #point = Point(0.8, 400)
        #plot = ScatterPlot(color=(1,0,0,1), pointsize=5)
        self.scatter_plot = ScatterPlot(color=[1, 0, 0, 1], point_size=5)
        #plot.points.append((0.8, 400))
        self.graph.add_plot(self.scatter_plot)

        self.update_label_plot()


    def on_touch_move(self, touch):
        print("AircraftLoadLayout.on_touch_move")
        self.sliders.update()
        self.update_label_plot()

    def update_label_plot(self):
        G = calculate_cg(self.cfg, self.loads)
        is_inside_centrogram = inside_centrogram(G, self.cfg.centrogram)
        self.lbl_center_gravity.text = (
            "G: (mass=%.1f kg, lever_arm=%.2f m, moment=%.1f kg.m)"
            % (G.mass, G.lever_arm, G.moment)
        )
        if is_inside_centrogram:
            self.lbl_center_gravity.disabled = False
            self.lbl_center_gravity.color = (0, 1, 0, 1)
            self.mesh_line_plot.color = (0, 0, 1, 1)
        else:
            self.lbl_center_gravity.disabled = True
            self.lbl_center_gravity.color = (1, 0, 0, 1)
            self.mesh_line_plot.color = (1, 0, 0, 1)
        self.scatter_plot.points = [(G.lever_arm, G.mass)]


class AircraftSelectLayout(GridLayout):
    def __init__(self, **kwargs):
        super(AircraftSelectLayout, self).__init__(**kwargs)


class MyApp(App):
    def __init__(self, xaxis, index, aircraft_config, **kwargs):
        self.xaxis = xaxis
        self.index = index
        self.aircraft_config = aircraft_config
        super(MyApp, self).__init__(**kwargs)

    def build(self):
        return AircraftLoadLayout(self.xaxis, self.aircraft_config)


def main():
    xaxis = "lever_arm"
    index = "."
    aircraft_config = "data/f-bubk.yml"

    script_path, _ = os.path.split(os.path.abspath(__file__))
    i18n.load_path.append(os.path.join(script_path, "translations"))
    i18n.set("filename_format", "{locale}.{format}")  # remove i18n namespace
    import locale

    cur_locale = locale.getlocale()[0][:2]
    i18n.set("locale", cur_locale)

    MyApp(xaxis, index, aircraft_config).run()


if __name__ == "__main__":
    main()
