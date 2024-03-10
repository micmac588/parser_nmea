import logging
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import multiprocessing

from controlled_animation import ControlledAnimation

class ScatterPlotter(multiprocessing.Process):

    def __init__(self, queue, logger):
        super().__init__()
        self.__queue = queue
        self.__data = []
        self.__logger = logger

    def run(self):
        self.fig, self.ax = plt.subplots()
        self.controlled_animation = ControlledAnimation(self.fig, self.update, frames=100, interval=5, init=self.setup_plot)
        self.controlled_animation.start()

    def setup_plot(self):
        """Initial drawing of the scatter plot."""
        self.scat = self.ax.scatter(0,0,s=1,c=100,alpha=0.1, marker='.')
        self.ax.axis([0, 360, -40, 40])
        return self.scat,
   
    def update(self, i):
        """Update the scatter plot."""
        self.__logger.debug("wait for data to plot")
        elem = self.__queue.get()

        if elem[0] == 'Start':
            self.__logger.debug("Start animation")
            self.ax.set_title(elem[1])
            self.ax.set_ylabel(elem[2])
            self.ax.set_xlabel(elem[3])
            return self.scat,

        if elem[0] == 'Stop':
            self.__logger.debug("Stop animation")
            self.stop()
            return self.scat,

        self.__data.append([elem[1], elem[0]])
        self.__logger.debug("add %s, %s" % (elem[1], elem[0]))

        self.scat.set_offsets(self.__data)
        return self.scat,

    def stop(self):
        self.controlled_animation.stop()
