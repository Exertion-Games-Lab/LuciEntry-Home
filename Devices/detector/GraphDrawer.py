import logging
import queue
import time
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore



#queue for data
class EEGDataQueue:
    def __init__(self, channels_num):
        self.data = []
        self.channels_num = channels_num
        for i in range(channels_num):
            self.data.append(queue.Queue())
    def put_data(self, data):
        for i in range(self.channels_num):
            self.data[i].put(data[i])
    def get_data(self,channel):
        try:
            return self.data[channel].get(timeout=1)
        except queue.Empty:
            logging.warning("Queue is empty")
            return [0] * self.channels_num
# EEG_data_queue = None


class Graph:
    def __init__(self, board_shim=None):
        self.board_id = board_shim.board_id
        self.board_shim = board_shim
        self.num_channels = board_shim.num_channels
        self.sampling_rate = board_shim.sampling_rate
        self.update_speed_ms = 50
        self.window_size = 4
        self.num_points = self.window_size * self.sampling_rate

        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow(title='BrainFlow Plot', size=(800, 600))
        self.data = []
        self.eeg_data_queue = EEGDataQueue(self.num_channels)
        self._init_timeseries()

        
        

    def _init_timeseries(self):
        self.plots = list()
        self.curves = list()
        for i in range(self.num_channels):
            p = self.win.addPlot(row=i, col=0)
            p.setYRange(-250,250,padding=0)
            p.showAxis('left', True)
            p.setMenuEnabled('left', False)
            p.showAxis('bottom', False)
            p.setMenuEnabled('bottom', False)
            if i == 0:
                p.setTitle('TimeSeries Plot')
            self.plots.append(p)
            curve = p.plot()
            self.curves.append(curve)
    def setData(self, data):
        self.eeg_data_queue.put_data(data)
    def update_graph(self):
    # ... (your existing code to get eog_data_filtered_left and eog_data_filtered_right)
        for i in range(self.num_channels):
            # plot timeseries
            data = self.eeg_data_queue.get_data(i)
            self.curves[i].setData(data)
    def update_loop(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update_graph)
        timer.start(self.update_speed_ms)
        print("Starting graph")
        QtGui.QApplication.instance().exec_()
