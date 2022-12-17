from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeySequence, QFont
from PyQt5.QtCore import pyqtSignal, Qt, QThread, pyqtSlot

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
import matplotlib.animation as animation
from matplotlib.backend_bases import MouseButton
matplotlib.use('Qt5Agg')

import json
import matplotlib
import os
import wave
import time
from sys import exit as sysExit
import numpy as np
import pandas as pd
from pydub import AudioSegment
from pydub.playback import play



class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=7, height=4, dpi=100):
        self.fig = Figure(figsize=(9,3))
        self.ax1 = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)

class Widget(QDialog):
    def __init__(self,parent=None):
        super(Widget, self).__init__(parent)
       
        # Initialize main sections of UI
        self.createPlotArea()
        self.createAudioControlArea()
        self.createSamplesArea()
        self.createImportExportArea()
        self.createSegmentationToolsArea()
        self.createLabelsArea()
        
        # Place individual UI components in grid
        mainLayout = QGridLayout()
        mainLayout.addWidget(self.canvas,1,0,1,4)
        mainLayout.addWidget(self.audio_controls_layout,2,0,1,4)
        mainLayout.addWidget(self.samples_layout,3,0,8,1)
        mainLayout.addWidget(self.import_export_layout,3,2,1,2)
        mainLayout.addWidget(self.segmentation_tools_layout,4,2,1,2)
        mainLayout.addWidget(self.labels_layout,5,2,1,2)
        self.setLayout(mainLayout)

        # Build function which takes care of all the interaction 
        self.buildDataFrame()
        self.interactionListener()
        self.sample_segmentations.currentCellChanged.connect(self.updatePlot)

    # Initialize canvas where data is plotted
    def createPlotArea(self):
        self.canvas = MplCanvas(self)
        self.canvas.fig.tight_layout()
        self.canvas.fig.patch.set_facecolor('#ececeb')
        
        self.canvas.ax1.set_yticklabels([])
        self.canvas.ax1.set_xlabel("Time [s]",fontsize=8)
        self.canvas.ax1.set_ylabel("Amplitude [-]", fontsize=8)
        
        for label in (self.canvas.ax1.get_xticklabels() + self.canvas.ax1.get_yticklabels()):
            label.set_fontsize(8)
        
    # Initialize audio control area where playing is controlled
    def createAudioControlArea(self):
 
        # Add layout title
        self.audio_controls_layout = QGroupBox("Audio controls")
        
        # Widgets are added in a horizontal direction
        layout = QVBoxLayout()

        # Build play audio button
        self.btn_play_audio = QPushButton("Play audio")

        # Add buttons to layout
        layout.addWidget(self.btn_play_audio)
 
        # Add listeners to audio controls
        self.btn_play_audio.clicked.connect(self.playAudio)
      
        # Set layout
        self.audio_controls_layout.setLayout(layout) 
    
    # Initialize area where filenames & segmentations are stored
    def createSamplesArea(self):
        
        # Layout title
        self.samples_layout = QGroupBox("Audiosamples and Segmentations")
        
        # Widgets are added in a horizontal direction
        layout = QHBoxLayout()
        
        # Use self so that ListWidgets can be modified afterwards
        #self.samples_stored = QListWidget()
        self.samples_stored = QTableWidget()
        self.sample_segmentations = QTableWidget()
        
        # Set samples settings
        self.samples_stored.setColumnCount(1)
        self.samples_stored.setFont(QFont('Arial',12))
        self.samples_stored.setHorizontalHeaderLabels(['Filenames'])
        
        self.samples_stored.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.samples_stored.setSelectionBehavior(QTableView.SelectRows)
        self.samples_stored.horizontalHeader().setStretchLastSection(True) 
        self.samples_stored.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.samples_stored.setSelectionMode(QAbstractItemView.SingleSelection)
        self.samples_stored.setSortingEnabled(True)

        # Set segmentations settings
        self.sample_segmentations.setColumnCount(3)
        self.sample_segmentations.setFont(QFont('Arial', 12))
        self.sample_segmentations.setHorizontalHeaderLabels(['Label','Start [s]','Stop [s]'])
        self.sample_segmentations.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sample_segmentations.setSelectionBehavior(QTableView.SelectRows)
        self.sample_segmentations.horizontalHeader().setStretchLastSection(True) 
        self.sample_segmentations.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sample_segmentations.setSelectionMode(QAbstractItemView.SingleSelection)

        # Initialize visible scrollbars in case lists are too long
        scroll_bar_samples_stored = QScrollBar(self)
        scroll_bar_sample_segmentations = QScrollBar(self)

        # Add scrollbars
        self.samples_stored.setVerticalScrollBar(scroll_bar_samples_stored)
        self.sample_segmentations.setVerticalScrollBar(scroll_bar_sample_segmentations)
        
        # Add each widget to the horizontal layout
        layout.addWidget(self.samples_stored, stretch=1)
        layout.addWidget(self.sample_segmentations, stretch=1)
        
        # Set layout
        self.samples_layout.setLayout(layout)

    def getLabels(self):
        try: 
            with open(os.getcwd() + '/labels.json', 'r') as json_file:
                return json.load(json_file)
        except IOError: return {}

    # Initialize area where labels are placed
    def createLabelsArea(self):
        
        # Set layout title
        self.labels_layout = QGroupBox("Labels")
        
        # Widgets are added in a vertical direction 
        self.rb_layout = QVBoxLayout()

        # Read settings file and build labels accordinly
        self.labels={}
        for idx, (label, color) in enumerate(self.getLabels().items()):
            
            # Build a random color and add to dictionary
            self.labels.update({label : color})
            
            # Add to layout
            radioButton = QRadioButton(label)
            self.rb_layout.addWidget(radioButton)
            
            # Add a listener checking if button is toggled or not
            radioButton.toggled.connect(self.updateLabel)
            
            # Add shortcut for label based on number
            rbs = QShortcut(QKeySequence(str(idx+1)),self)
            rbs.activated.connect(lambda a=idx: self.rb_shortcut(a))
        
        # Set last radioButton to be selected by default
        self.active_label = label
        radioButton.setChecked(True)

        # Set layout
        self.labels_layout.setLayout(self.rb_layout)
           
    def rb_shortcut(self, value):
        self.rb_layout.itemAt(value).widget().setChecked(True)

    # This function updates the label based on toggling
    def updateLabel(self, value):
        
        # Get the sender
        rbtn = self.sender()

        # Get the label of the checked button
        if rbtn.isChecked() == True:
            self.active_label = rbtn.text()

    # Initialize area where dict is imported & exported
    def createImportExportArea(self):
        
        # Add layout title
        self.import_export_layout = QGroupBox("Import and Export")
        
        # Widgets are added in a horizontal direction
        layout = QHBoxLayout()

        # Build import and export buttons for dictionary
        self.btn_import = QPushButton("Import")
        self.btn_export = QPushButton("Export")

        # Add buttons to layout
        layout.addWidget(self.btn_import)
        layout.addWidget(self.btn_export)
 
        # Add listeners to both buttons
        self.btn_import.clicked.connect(self.importData)
        self.btn_export.clicked.connect(self.exportData)
      
        # Set layout
        self.import_export_layout.setLayout(layout) 

    # Create segmentation tools area
    def createSegmentationToolsArea(self):
        
        # Add layout title
        self.segmentation_tools_layout = QGroupBox("Segmentation tools")

        # Add widgets in vertical direction
        layout = QVBoxLayout()

        # Build delete button
        self.btn_accept = QPushButton("Accept")
        self.btn_delete = QPushButton("Delete")
        self.btn_failed = QPushButton("Failed Sample")

        # Add button to layout
        layout.addWidget(self.btn_accept)
        layout.addWidget(self.btn_delete)
        layout.addWidget(self.btn_failed)

        # Add listeners
        self.btn_accept.clicked.connect(self.accept)
        self.btn_delete.clicked.connect(self.delete)
        self.btn_failed.clicked.connect(self.failed)

        # Set layout
        self.segmentation_tools_layout.setLayout(layout)
        
        # Add shortcuts
        shortcut_delete = QShortcut(QKeySequence("d"),self)
        shortcut_delete.activated.connect(self.delete)
        
        shortcut_accept = QShortcut(QKeySequence("a"),self)
        shortcut_accept.activated.connect(self.accept)
        
        shortcut_failed = QShortcut(QKeySequence("f"),self)
        shortcut_failed.activated.connect(self.failed)
                
        # Add shortcut for label based on number
        up = QShortcut(QKeySequence("w"),self)
        up.activated.connect(self.up)
        
        down = QShortcut(QKeySequence("s"),self)
        down.activated.connect(self.down)

           
    def up(self):
        self.samples_stored.selectRow(self.samples_stored.currentRow()-1)
        
    def down(self):
        self.samples_stored.selectRow(self.samples_stored.currentRow()+1)
        
    # Mark sample as failed
    def failed(self):
        
        start = 0
        stop = self.filenames[self.current_filename]['time'][-1]
            
        # Update dataframe
        self.df.loc[len(self.df)] = [self.current_filename, "failed", start, stop]
        self.df = self.df.sort_values(['filename', 'start'], ascending=True)
        self.df = self.df.reset_index(drop=True)
        
        # Get the right location to place row
        subframe = self.df[self.df.filename == self.current_filename]
        subframe = subframe.reset_index(drop = True)
        idx = subframe[(subframe.start == start) & (subframe.stop == stop)].index[0]
        
        # Add to table
        time_start = QTableWidgetItem(str(start)) 
        time_start.setTextAlignment(Qt.AlignCenter)

        time_end = QTableWidgetItem(str(stop))
        time_end.setTextAlignment(Qt.AlignCenter)

        self.sample_segmentations.insertRow(idx)
        self.sample_segmentations.setItem(idx, 0, QTableWidgetItem("failed"))
        self.sample_segmentations.setItem(idx, 1, time_start)
        self.sample_segmentations.setItem(idx, 2, time_end)

        # Update plot
        self.segmentation_span.insert(idx,self.canvas.ax1.axvspan(start, stop, facecolor=self.labels["failed"], ec = 'k',  alpha=0.2))
        
        self.canvas.fig.canvas.draw()

    # This function deletes the current segmentation block
    def delete(self):
        try: 
            # Delete area selector first
            self.area_selector.remove()
        
            # Get the current row number
            row = self.sample_segmentations.currentRow()
            
            # Remove selected row based on number
            self.sample_segmentations.removeRow(row)
            act_item = self.segmentation_span.pop(row)
            act_item.remove()

            # Redraw plot
            self.canvas.fig.canvas.draw()

            # Delete underlying dataframe
            subframe = self.df[self.df.filename == self.current_filename]
            idx = self.df[self.df.filename == self.current_filename].index[row]
            self.df = self.df.drop(idx)
            self.df = self.df.reset_index(drop=True)
            
        except Exception as e: print(e)
        

        
    def accept(self):
        
        for start, stop in self.times:
            start = round(start,2)
            stop = round(stop,2)
    
            # Update dataframe
            self.df.loc[len(self.df)] = [self.current_filename, self.active_label, start, stop]
            self.df = self.df.sort_values(['filename', 'start'], ascending=True)
            self.df = self.df.reset_index(drop=True)
            
            # Get the right location to place row
            subframe = self.df[self.df.filename == self.current_filename]
            subframe = subframe.reset_index(drop = True)
            idx = subframe[(subframe.start == start) & (subframe.stop == stop)].index[0]
            
            # Add to table
            time_start = QTableWidgetItem(str(start)) 
            time_start.setTextAlignment(Qt.AlignCenter)
    
            time_end = QTableWidgetItem(str(stop))
            time_end.setTextAlignment(Qt.AlignCenter)
    
            self.sample_segmentations.insertRow(idx)
            self.sample_segmentations.setItem(idx, 0, QTableWidgetItem(self.active_label))
            self.sample_segmentations.setItem(idx, 1, time_start)
            self.sample_segmentations.setItem(idx, 2, time_end)
    
            # Update plot
            self.segmentation_span.insert(idx,self.canvas.ax1.axvspan(start, stop, facecolor=self.labels[self.active_label], ec = 'k',  alpha=0.2))
        
        self.canvas.fig.canvas.draw()
        
    # Function connected to import button
    def importData(self):

        # Make sure that user cannot import records many times
        if self.samples_stored.rowCount() == 0:
            
            # Initialize list where spans are added
            self.segmentation_span = []
            self.filenames = {}
            
            # Build a counter for number of samples
            idx = 0

            # Load audiofiles
            for r, d, f in os.walk(os.getcwd() + '/audiofiles/'):
                for file in f:
                    if file.endswith(".wav"):
                            
                        # Read time & signal into memory
                        raw = wave.open(os.getcwd() + '/audiofiles/' + file)            
                        f_rate = raw.getframerate()
                        signal = raw.readframes(-1)
                        signal = np.frombuffer(signal, dtype ="int16")
                        time = np.linspace(0,len(signal) / f_rate,num = len(signal))
                        self.filenames.update({file : {'signal' : signal, 'time' : time, 'f_rate' : f_rate}})
                        #self.samples_stored.addItem(file)
                                 
                        self.samples_stored.insertRow(idx)
                        self.samples_stored.setItem(idx, 0, QTableWidgetItem(file))
           
            # Try to read stored segmentations
            try: self.df = pd.read_excel("segmentations.xlsx")
            except: pass
            
            self.samples_stored.sortItems(0)

            # Add a listener for when the current item is changed
            self.samples_stored.currentCellChanged.connect(self.itemActivated)
        
            # Select first item in list
            self.samples_stored.selectRow(0)
            
    # Function connected to export button
    def exportData(self):
        # If you want to hinder user from having multiple different labels
        #df.groupby('record_id')['label'].nunique().max()
        self.df.to_excel("segmentations.xlsx", index=False)

    # Function connected to when list item changes in samples_stored
    def itemActivated(self, item):

        # Current filename
        self.current_filename = self.samples_stored.currentItem().text()

        # Initially zero so that audio is played from start to stop
        self.start_audio = self.filenames[self.current_filename]['time'][0]
        self.stop_audio = self.filenames[self.current_filename]['time'][-1]

        # Delete previous spans
        self.segmentation_span.clear()

        # Plot data
        try: self.plotSignal()
        except: pass

        # Move vertical line to right location
        try: self.line.remove()
        except: pass

        self.line = self.canvas.ax1.axvline(self.start_audio, color = 'r')
        
        # Clear widget containing previous segmentations (row texts)
        self.sample_segmentations.setRowCount(0)
        
        # Update segmentation table
        subframe = self.df[self.df.filename == self.current_filename]
        if len(subframe) > 0:
            for idx, (_, row) in enumerate(subframe.iterrows()):
        
                # Add to table
                time_start = QTableWidgetItem(str(round(row['start'],2))) 
                time_start.setTextAlignment(Qt.AlignCenter)

                time_end = QTableWidgetItem(str(round(row['stop'],2)))
                time_end.setTextAlignment(Qt.AlignCenter)

                self.sample_segmentations.insertRow(idx)
                self.sample_segmentations.setItem(idx, 0, QTableWidgetItem(row['label']))
                self.sample_segmentations.setItem(idx, 1, time_start)
                self.sample_segmentations.setItem(idx, 2, time_end)
                
                self.segmentation_span.append(self.canvas.ax1.axvspan(row['start'], row['stop'],facecolor=self.labels[row['label']], ec='k',alpha = 0.2))
       
        # Initialize right button span selector
        self.audio_span = SpanSelector(self.canvas.ax1, self.on_audio_select, "horizontal", minspan=0.02,useblit=True,rectprops=dict(alpha=0.2, facecolor="black"), button=3)

        # Initialize span selector which allows area selections to be made
        self.span = SpanSelector(self.canvas.ax1,self.onselect,"horizontal",minspan=0.02,useblit=True,rectprops=dict(alpha=0.1, facecolor=self.labels[self.active_label]), button=1)
        
        # Redraw plot
        self.canvas.fig.canvas.draw()
    
    # SpanSelector for audio
    def on_audio_select(self, start, stop):
        # Set start and stop for audio
        self.start_audio = start
        self.stop_audio = stop
        
        # Remove audio selector span
        try: self.audio_selector_span.remove()
        except: pass

        # Update plot
        self.audio_selector_span = self.canvas.ax1.axvspan(start, stop, facecolor="black", alpha=0.1)

        # Move vertical line to right location
        try: self.line.remove()
        except: pass
        self.line = self.canvas.ax1.axvline(start, color = 'r')

    # Plot audiogram
    def plotSignal(self):

        # Build title
        current = str(self.samples_stored.currentRow()+1)
        total = str(len(self.filenames))
        title = "Audiofile " + current + "/" + total + ": " + self.current_filename

        # Time and sigal data
        time = self.filenames[self.current_filename]['time']
        signal = self.filenames[self.current_filename]['signal']
        
        # Clear previous plot and build new plot
        self.canvas.ax1.cla()
        self.canvas.ax1.plot(time, signal, 'k', lw = 0.9)
                
        # Scale time axis based on limits 
        self.canvas.ax1.set_xlim([time[0],time[-1]])
        self.canvas.ax1.set_yticklabels([])
        self.canvas.ax1.set_xlabel("Time [s]",fontsize=8)
        self.canvas.ax1.set_ylabel("Amplitude [-]", fontsize=8)
        self.canvas.ax1.set_title(title, fontsize=10) 
        
        for label in (self.canvas.ax1.get_xticklabels() + self.canvas.ax1.get_yticklabels()):
            label.set_fontsize(8)

        self.canvas.fig.canvas.draw()
     
    def animate(self,i,start,diff):
        location = start + time.time()-self.t
        self.line.set_xdata(location)  # update the data.
        if location >= self.stop_audio:
            self.on_done()
        return self.line,

    def on_done(self):
        self.ani.event_source.stop()
        self.playing = False
        self.line.remove()
        self.line = self.canvas.ax1.axvline(self.start_audio, color = 'r')
        self.canvas.fig.canvas.draw()
        self.enableGUIElements(True)
    
    def on_job_done(self):
        try:
            self.line.remove()
            self.line = self.canvas.ax1.axvline(self.start_audio, color = 'r')
            self.canvas.fig.canvas.draw()
        except: pass

    def playAudio(self):
        self.playing = True
        self.enableGUIElements(False)
        start = self.start_audio
        stop = self.stop_audio
        diff = stop - start
        song = AudioSegment.from_wav(os.getcwd() + '/audiofiles/' + self.current_filename)
        sound = song[int(start*1000):int(stop*1000)]
        self.worker_thread = WorkerThread(sound)
        self.worker_thread.job_done.connect(self.on_job_done)
        self.t = time.time()
        self.worker_thread.start()
        self.ani = animation.FuncAnimation(self.canvas.fig, self.animate, interval=20, fargs=(start,diff,), blit=True, repeat=False)
        self.canvas.fig.canvas.draw()
   
    # Helper function which makes enabling/disabling elements easy
    def enableGUIElements(self, boolean):
        self.btn_play_audio.setEnabled(boolean)
        self.samples_stored.setEnabled(boolean)
        self.btn_import.setEnabled(boolean)
        self.btn_export.setEnabled(boolean)
        self.btn_delete.setEnabled(boolean)
        self.sample_segmentations.setEnabled(boolean)
        
        #items = (self.rb_layout.itemAt(i) for i in range(self.rb_layout.count())) 
        #for w in items:
        #    w.widget().setCheckable(boolean)
            #w.setCheckable(boolean)
            
    # This function updates plot based on row change
    def updatePlot(self, row):
        
        # Remove selector
        try: self.area_selector.remove()
        except: pass
        
        # Build area selector
        if row != -1:
            # Get the current filename
            subframe = self.df[self.df.filename == self.current_filename].iloc[row]
            start = subframe['start']
            stop = subframe['stop']
            
            # Plot section and update
            self.area_selector = self.canvas.ax1.axvspan(start, stop, ec = 'r', lw = 1.5)
            self.area_selector.set_fill(False)
            self.canvas.fig.canvas.draw()
   
    def buildDataFrame(self):
        column_names = ["filename", "label", "start", "stop"]
        self.df = pd.DataFrame(columns = column_names)

    # This function checks which row has been selected
    def interactionListener(self):
        
        # This function is called when user clicks are in plot
        def onclick(event):
            
            # Set audio playing span
            if event.button == MouseButton.RIGHT:
                if not (self.start_audio <= event.xdata <= self.stop_audio):
                    self.audio_selector_span.remove()
                    self.start_audio = self.filenames[self.current_filename]['time'][0]
                    self.stop_audio = self.filenames[self.current_filename]['time'][-1]
                    self.line.set_xdata(self.start_audio)
            
            # Set segmentation span
            if event.button == MouseButton.LEFT:
                subframe = self.df[self.df.filename == self.current_filename]
                if len(subframe) > 0:
                    for index,(_, row) in enumerate(subframe.iterrows()):
                        start = row['start']
                        stop = row['stop']
                        if start <= event.xdata <= stop:
                            self.sample_segmentations.selectRow(index)
                            break
        
        # Add clicklistener for selecting span in plot
        self.canvas.fig.canvas.mpl_connect('button_release_event', onclick)
    
    # SpanSelector calls this function which updates the plot
    def onselect(self, start, stop):
        start = round(start,2)
        stop = round(stop,2)

        # Update dataframe
        self.df.loc[len(self.df)] = [self.current_filename, self.active_label, start, stop]
        self.df = self.df.sort_values(['filename', 'start'], ascending=True)
        self.df = self.df.reset_index(drop=True)
        
        # Get the right location to place row
        subframe = self.df[self.df.filename == self.current_filename]
        subframe = subframe.reset_index(drop = True)
        idx = subframe[(subframe.start == start) & (subframe.stop == stop)].index[0]
        
        # Add to table
        time_start = QTableWidgetItem(str(start)) 
        time_start.setTextAlignment(Qt.AlignCenter)

        time_end = QTableWidgetItem(str(stop))
        time_end.setTextAlignment(Qt.AlignCenter)

        self.sample_segmentations.insertRow(idx)
        self.sample_segmentations.setItem(idx, 0, QTableWidgetItem(self.active_label))
        self.sample_segmentations.setItem(idx, 1, time_start)
        self.sample_segmentations.setItem(idx, 2, time_end)

        # Update plot
        self.segmentation_span.insert(idx,self.canvas.ax1.axvspan(start, stop, facecolor=self.labels[self.active_label], ec = 'k',  alpha=0.2))
 
        # Select current row
        self.sample_segmentations.selectRow(idx)
        
    def closeEvent(self, event):
        self.exportData()        

class WorkerThread(QThread):
        job_done = pyqtSignal()

        def __init__(self, sound,parent=None):
            super(WorkerThread, self).__init__(parent)
            self.sound = sound

        def do_work(self):
            play(self.sound)            
            self.job_done.emit()
        
        def run(self):
            self.do_work()

# MAIN
if __name__ == "__main__":
    MainEventHandler = QApplication([])
    
    # Build layout
    application = Widget()
    application.show() 
    
    sysExit(MainEventHandler.exec_())

