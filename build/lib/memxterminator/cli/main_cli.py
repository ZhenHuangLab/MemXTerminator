import sys
import mrcfile
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QApplication, QDialog
from ..GUI.mainwindow_gui import Ui_MainWindow
from .radonfit_cli import RadonApp, MembraneAnalyzerApp, MembraneSubtractionApp, MicrographMembraneSubtraction_Radon_App
from .bezierfit_cli import MembraneAnalyzer_Bezier_App, ParticleMembraneSubtraction_Bezier_App, MicrographMembraneSubtraction_Bezier_App
import argparse

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.radon_button.clicked.connect(self.open_radon_analysis)
        self.mem_analyze_button.clicked.connect(self.open_membrane_analyzer)
        self.mem_subtraction_button.clicked.connect(self.open_membrane_subtraction)
        self.micrograph_membrane_subtraction_pushButton.clicked.connect(self.open_radon_micrograph_membrane_subtraction)
        self.mem_analyze_bezier_button.clicked.connect(self.open_membrane_analyzer_bezier)
        self.mem_subtraction_bezier_button.clicked.connect(self.open_membrane_subtraction_bezier)
        self.micrograph_membrane_subtraction_bezier_pushButton.clicked.connect(self.open_micrograph_membrane_subtraction_bezier)

    def open_radon_analysis(self):
        self.radon_dialog = RadonApp(self)
        self.radon_dialog.show()

    def open_membrane_analyzer(self):
        reply = QMessageBox.question(self, 'Membrane Analyzer - Radonfit - MemXTerminator', 'Ensure you have completed Radon Analysis Blinking. \nContinue?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            self.membrane_analyzer_dialog = MembraneAnalyzerApp(self)
            self.membrane_analyzer_dialog.show()

    def open_membrane_subtraction(self):
        reply = QMessageBox.question(self, 'Particles Membrane Subtraction - Radonfit - MemXTerminator', 'Ensure you have completed Membrane Analysis and the obtained averaged membranes and masks are as expected. \nContinue?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            self.membrane_subtraction_dialog = MembraneSubtractionApp(self)
            self.membrane_subtraction_dialog.show()
    
    def open_radon_micrograph_membrane_subtraction(self):
        reply = QMessageBox.question(self, 'Micrograph Membrane Subtraction - MemXTerminator', 'Ensure you have completed Particles Membrane Subtraction. \nContinue?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            self.micrograph_membrane_subtraction_dialog = MicrographMembraneSubtraction_Radon_App(self)
            self.micrograph_membrane_subtraction_dialog.show()

    def open_membrane_analyzer_bezier(self):
        self.membrane_analyzer_bezier_dialog = MembraneAnalyzer_Bezier_App(self)
        self.membrane_analyzer_bezier_dialog.show()

    def open_membrane_subtraction_bezier(self):
        reply = QMessageBox.question(self, 'Particles Membrane Subtraction - Bezierfit - MemXTerminator', 'Ensure you have completed Membrane Analysis. \nContinue?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            self.membrane_subtraction_bezier_dialog = ParticleMembraneSubtraction_Bezier_App(self)
            self.membrane_subtraction_bezier_dialog.show()

    def open_micrograph_membrane_subtraction_bezier(self):
        reply = QMessageBox.question(self, 'Micrograph Membrane Subtraction - MemXTerminator', 'Ensure you have completed Particles Membrane Subtraction, and converted the particles_selected.cs file to particles_selected.star file for Micrograph Membrane Subtraction. \nContinue?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        if reply == QMessageBox.Ok:
            self.micrograph_membrane_subtraction_bezier_dialog = MicrographMembraneSubtraction_Bezier_App(self)
            self.micrograph_membrane_subtraction_bezier_dialog.show()

def fix_mrc_file(fp):
    """Try to fix .mrc file Map ID."""
    try:
        with mrcfile.open(fp, "r+", permissive=True) as mrc:
            if not mrc.header.map == mrcfile.constants.MAP_ID:
                mrc.header.map = mrcfile.constants.MAP_ID
            if mrc.data is not None:
                mrc.update_header_from_data()
            else:
                print(f"ERROR with {fp}: data is None!")
        try:
            with mrcfile.open(fp, "r") as mrc:
                print(f"File {fp} opened successfully after fix.")
        except ValueError as e:
            print(f"ERROR with {fp}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred with {fp}: {e}")

def main():
    """main client"""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    parser_gui = subparsers.add_parser('gui')
    parser_fixmapid = subparsers.add_parser('fixmapid')
    parser_fixmapid.add_argument('file', nargs='+', help='Path to .mrc file(s)')
    args = parser.parse_args()

    if args.command == 'gui':
        app = QApplication(sys.argv)
        mainWin = MainWindow()
        mainWin.show()
        sys.exit(app.exec_())

    if args.command == 'fixmapid':
        for file_path in sys.argv[2:]:
            fix_mrc_file(file_path)
