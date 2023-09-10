import math

import matplotlib
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle, Circle
from matplotlib.widgets import Button
import tkinter as tk
from tkinter import filedialog

matplotlib.use('TkAgg')
from matplotlib import pyplot as plt

import ctypes, time
from PIL import Image

screen_width = ctypes.windll.user32.GetSystemMetrics(0)
screen_height = ctypes.windll.user32.GetSystemMetrics(1)


class simplePaintingTool:
    def __init__(self):
        self.fig = plt.figure(
            figsize=(8, 8),
            num="Paint",
        )
        self.fig.canvas.manager.window.wm_geometry(f"+{0}+{0}")

        grid = plt.GridSpec(40, 28)

        self.drawing_ax = self.fig.add_subplot(grid[:-2, :])

        self.drawing_ax.set_xlim([-5, 5])
        self.drawing_ax.set_ylim([-5, 5])
        self.drawing_ax.set_aspect(1)

        self.drawing_ax.tick_params(axis='both', which='both', bottom=False, top=False, left=False, right=False,
                                    labelbottom=False, labeltop=False, labelleft=False, labelright=False)

        self.palette_ax = self.fig.add_subplot(grid[-2:, :15])
        self.palette_ax.set_xticks([])
        self.palette_ax.set_yticks([])
        self.colors = [
            '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', '#800080',
            '#FFA500', '#008000', '#FF4500', '#000000', '#C0C0C0', '#808080',
            '#800000', '#008080', '#800080', '#808000', '#00FF80', '#FF0080', '#FFFFFF'
        ]
        self.palette_ax.set_xlim([0, len(self.colors)])
        for i, color in enumerate(self.colors):
            rect = Rectangle((i, 0), 1, 1, facecolor=color, edgecolor='none')
            self.palette_ax.add_patch(rect)
        self.selected_color = self.colors[0]
        self.selected_color_marker = self.palette_ax.scatter([0.5], [0.5], marker='*', color='#000000')

        a = 15
        slider_ax1 = self.fig.add_subplot(grid[-2:, a:a+3])
        slider_ax1.set_ylim([0, 1])
        slider_ax1.text(0, 0.5, 'size', verticalalignment='center')
        slider_ax1.axis('off')

        self.slider_val = 10
        slider_ax2 = self.fig.add_subplot(grid[-2:, a+2:a+4])
        slider_ax2.set_ylim([0, 1])
        self.slider_val_text = slider_ax2.text(0, 0.5, str(self.slider_val), verticalalignment='center')
        slider_ax2.axis('off')

        less_button_axis = self.fig.add_subplot(grid[-2:, a+1:a+2])
        less_button = Button(less_button_axis, label='<')
        less_button.on_clicked(self.less_button_pressed)

        more_button_axis = self.fig.add_subplot(grid[-2:, a+3:a+4])
        more_button = Button(more_button_axis, label='>')
        more_button.on_clicked(self.more_button_pressed)

        undo_button_axis = self.fig.add_subplot(grid[-2:, 19:22])
        undo_button = Button(undo_button_axis, label='undo(z)')
        undo_button.on_clicked(self.undo_button_clicked)

        save_button_axis = self.fig.add_subplot(grid[-2:, 22:25])
        save_button = Button(save_button_axis, label='save')
        save_button.on_clicked(self.extract_drawn_image)

        load_button_axis = self.fig.add_subplot(grid[-2:, 25:28])
        load_button = Button(load_button_axis, label='load')
        load_button.on_clicked(self.load_drawn_image)

        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self.update_crosshair)

        self.fig.set_tight_layout(True)

        self.drawing = False
        self.points = np.array([]).reshape(-1, 2)
        self.current_lines = None

        self.added_lines_stack = []
        self.cross_hair_patch = None

        plt.show()

    def update_crosshair(self, event):
        data_points_ratio = self.fig.dpi_scale_trans.transform((1, 1))[0]
        if event.inaxes == self.drawing_ax:
            size_in_data = (self.slider_val - 2) / data_points_ratio
            if self.cross_hair_patch is None:
                self.cross_hair_patch = \
                    Circle(
                        xy=(event.xdata, event.ydata), radius=size_in_data, linewidth=1,
                        fill=False, color=self.selected_color
                    )
                self.drawing_ax.add_patch(self.cross_hair_patch)
            else:
                self.cross_hair_patch.set_center((event.xdata, event.ydata))
                self.cross_hair_patch.set_edgecolor(self.selected_color)
                self.cross_hair_patch.set_color(self.selected_color)
        else:
            if self.cross_hair_patch is not None:
                self.cross_hair_patch.remove()
                self.cross_hair_patch = None
        self.fig.canvas.draw()

    def less_button_pressed(self, _):
        if self.slider_val > 4:
            self.slider_val -= 2
            self.slider_val_text.set_text(str(self.slider_val))
            self.fig.canvas.draw()

    def more_button_pressed(self, _):
        if self.slider_val < 29:
            self.slider_val += 2
            self.slider_val_text.set_text(str(self.slider_val))
            self.fig.canvas.draw()

    def on_key_press(self, event):
        if event.key == 'z':
            self.undo_button_clicked(None)

    def undo_button_clicked(self, _):
        if len(self.added_lines_stack):
            self.added_lines_stack.pop().remove()
            self.fig.canvas.draw()

    def on_press(self, event):
        if event.inaxes == self.drawing_ax:
            self.drawing = True
            self.points = np.concatenate([self.points, np.array([[event.xdata, event.ydata]])])
            data_points_ratio = self.fig.dpi_scale_trans.transform((1, 1))[0]
            size_in_data = self.slider_val / data_points_ratio
            patch = Circle(xy=(event.xdata, event.ydata), radius=size_in_data, edgecolor='none', fill=True,
                           facecolor=self.selected_color)
            self.drawing_ax.add_patch(patch)
            self.added_lines_stack.append(patch)
        if event.inaxes == self.palette_ax:
            self.selected_color = self.colors[math.floor(event.xdata)]
            self.selected_color_marker.remove()
            self.selected_color_marker = \
                self.palette_ax.scatter([math.floor(event.xdata) + 0.5], [0.5], marker='*', color='#000000')
        self.fig.canvas.draw()

    def on_motion(self, event):
        if self.drawing:
            self.points = np.concatenate([self.points, np.array([[event.xdata, event.ydata]])])
            if self.current_lines is None:
                self.added_lines_stack.pop().remove()
                self.current_lines = LineCollection([self.points], linestyle='-', capstyle='round',
                                                    linewidth=self.slider_val, color=self.selected_color)
                self.drawing_ax.add_collection(self.current_lines)
                self.added_lines_stack.append(self.current_lines)
            else:
                self.current_lines.set_paths([self.points])
            self.fig.canvas.draw()

    def on_release(self, _):
        self.drawing = False
        self.current_lines = None
        self.points = np.array([]).reshape(-1, 2)

    def extract_drawn_image(self, _):
        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )

        if not file_path:
            return

        try:
            extent = self.drawing_ax.get_window_extent()
            buffer = self.fig.canvas.copy_from_bbox(extent)
            image = np.asarray(buffer)
            Image.fromarray(image).save(file_path)
            print(f"Image saved as {file_path}")
        except Exception as e:
            print(f"Error saving the image: {e}")

    def load_drawn_image(self, _):
        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            loaded_image = Image.open(file_path)
            self.drawing_ax.clear()
            self.drawing_ax.imshow(loaded_image, extent=[-5, 5, -5, 5], aspect='auto')
            self.fig.canvas.draw()
            print(f"Image loaded from {file_path}")
        except Exception as e:
            print(f"Error loading the image: {e}")


if __name__ == "__main__":
    simplePaintingTool()