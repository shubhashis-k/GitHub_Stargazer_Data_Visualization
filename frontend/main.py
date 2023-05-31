import requests
import pyqtgraph as pg
from requests import Response
import sys
from typing import Any, Callable, List,  Optional

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont

# This acts as a frontend for the application. It is responsible for fetching the data from the backend and displaying it to the user. 
# The frontend is built using PyQt5 and pyqtgraph.

# Represents a single data point in the graph.
class Starpoint:
    def __init__(self, year: int, month: int, total_stars: int) -> None:
        self.year = year
        self.month = month
        self.total_stars = total_stars

# Represents a single GitHub project that contains the official project name, the total number of stars, and all of the data points that will be displayed on the graph.
class GitHub_Project:
    def __init__(self, project_name: str, number_of_stars:int, starpoints: List[Starpoint]) -> None:
        self.project_name = project_name
        self.number_of_stars = number_of_stars
        self.starpoints = starpoints

# Needed for offloading tasks from UI thread to a separate thread so that we don't block the UI thread.
class Worker(QtCore.QRunnable):
    def __init__(self, func: Callable[[], Any]) -> None:
        super(Worker, self).__init__()
        self.func = func
        self.signals = WorkerSignals()

    @QtCore.pyqtSlot()
    def run(self) -> None:
        data = self.func()
        self.signals.result.emit(data)

# Needed to emit signals from the worker thread to the UI thread so that we don't need to update some UI components from the worker thread.
class WorkerSignals(QtCore.QObject):
    result: QtCore.pyqtSignal = QtCore.pyqtSignal(object)

class MainWindow(QtWidgets.QMainWindow):
    # For now, we're using a local server.
    server_address: str = "http://localhost:8000"

    # Fetches project names from the server.
    def get_project_names(self) -> List[str]:
        url: str = f'{self.server_address}/stargazer_data/'
        response: Response = requests.get(url)
        if response.status_code != 200:
            return []
        return response.json()
    
    # Fetches project details from the server.
    def get_project_details(self, project_name: str) -> Optional[GitHub_Project]:
        url: str = f'{self.server_address}/stargazer_data/{project_name}'
        response: Response = requests.get(url)
        
        if response.status_code != 200:
            return None
        
        data: dict = response.json()
        fetched_project_name: str = data.get('project_name', "")
        number_of_stars: int = data.get('number_of_stars', 0)
        starpoints: List[dict] = data.get('starpoints', [])

        starpoints_array: List[Starpoint] = []

        for starpoint in starpoints:
            year: int = starpoint.get('year', 0)
            month: int = starpoint.get('month', 0)
            total_stars: int = starpoint.get('total_stars', 0)

            starpoints_array.append(Starpoint(year, month, total_stars))

        return GitHub_Project(fetched_project_name, number_of_stars, starpoints_array)

    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(MainWindow, self).__init__(*args, **kwargs)

        # Set a fixed size window for now
        self.resize(1000, 1000)

        # Main Layout
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()

        # Set up Labels and Graphs and Dropdown list
        self.select_project_label: QtWidgets.QLabel = QtWidgets.QLabel("Select Project:")
        self.select_project_label.setStyleSheet("font-size: 20px;") 
        
        self.current_project_label: QtWidgets.QLabel = QtWidgets.QLabel("")
        self.current_project_label.setStyleSheet("font-size: 20px;")

        self.plot: pg.PlotWidget = pg.PlotWidget()
        self.plot.setBackground('w')
        self.plot.getAxis('bottom').setStyle(tickFont = QFont("Arial", 11)) 
        self.plot.getAxis('left').setStyle(tickFont = QFont("Arial", 11)) 

        self.combo_box: QtWidgets.QComboBox = QtWidgets.QComboBox()
        self.combo_box.setStyleSheet("font-size: 20px;") 

        # Arrange the UI components
        hbox: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.select_project_label)
        hbox.addWidget(self.current_project_label)
        hbox.addWidget(self.combo_box)
        
        layout.addLayout(hbox)
        layout.addWidget(self.plot)

        widget: QtWidgets.QWidget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Until we fetch the project names, we'll display a loading message.
        self.combo_box.addItem("Loading...")
        self.fetch_project_names()
        
    def fetch_project_names(self) -> None:
        # Offload to another thread so that we don't freeze the UI
        worker: QtCore.pyqtSignal = Worker(lambda: self.get_project_names())
        worker.signals.result.connect(self.update_combo_box)
        QtCore.QThreadPool.globalInstance().start(worker)
    
    @QtCore.pyqtSlot(object)
    def update_combo_box(self, projects: str) -> None:
        self.combo_box.clear()
        self.combo_box.addItems(projects)

        # After updating the project list, we can enable the combo box to fetch project details when the user selects a project.
        self.combo_box.currentTextChanged.connect(self.fetch_project_details)

    def fetch_project_details(self) -> None:
        selected_project_name: str = self.combo_box.currentText()
        worker = Worker(lambda: self.get_project_details(selected_project_name))
        worker.signals.result.connect(self.update_graph)
        QtCore.QThreadPool.globalInstance().start(worker)

    @QtCore.pyqtSlot(GitHub_Project)
    def update_graph(self, project_data: GitHub_Project) -> None:
        if not project_data:
            print("Failed to fetch data from the server.")
            return

        self.current_project_label.setText(project_data.project_name + " - " + str(project_data.number_of_stars) + " stars")

        x_values = [point.year + (point.month - 1) / 12 for point in project_data.starpoints]
        y_values = [point.total_stars for point in project_data.starpoints]

        # Clear the old plot before drawing the new one
        self.plot.clear()
        self.plot.plot(x_values, y_values, pen='b', symbol='o', symbolBrush='b')

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()