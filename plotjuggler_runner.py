import os
import subprocess


class PlotjugglerHelper:
    def __init__(self):
        self.path = "/home/"

    def open_plotjuggler(self):
        if os.path.exists(self.path):
            os.chdir(self.path)
            self.open_plotjuggler = subprocess.run(["plotjuggler"])
            if (
                self.open_plotjuggler.returncode == 0
            ):  # Check if 'ade enter' was successful
                print("Plotjuggler started successfully.")
            else:
                print("Failed to open Plotjuggler. Plotjuggler will not be started.")
        else:
            print(f"Path does not exist: {self.path}")


pl = PlotjugglerHelper()
pl.open_plotjuggler()
