# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MicrographMembraneSubtraction_Radonfit.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MicrographMembraneSubtraction_Radonfit(object):
    def setupUi(self, MicrographMembraneSubtraction_Radonfit):
        MicrographMembraneSubtraction_Radonfit.setObjectName("MicrographMembraneSubtraction_Radonfit")
        MicrographMembraneSubtraction_Radonfit.resize(622, 332)
        self.horizontalLayoutWidget = QtWidgets.QWidget(MicrographMembraneSubtraction_Radonfit)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(10, 10, 601, 41))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.particles_selected_starfile_label = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.particles_selected_starfile_label.setObjectName("particles_selected_starfile_label")
        self.horizontalLayout.addWidget(self.particles_selected_starfile_label)
        self.particles_selected_starfile_lineEdit = QtWidgets.QLineEdit(self.horizontalLayoutWidget)
        self.particles_selected_starfile_lineEdit.setObjectName("particles_selected_starfile_lineEdit")
        self.horizontalLayout.addWidget(self.particles_selected_starfile_lineEdit)
        self.particles_selected_starfile_browse_pushButton = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.particles_selected_starfile_browse_pushButton.setObjectName("particles_selected_starfile_browse_pushButton")
        self.horizontalLayout.addWidget(self.particles_selected_starfile_browse_pushButton)
        self.gridLayoutWidget = QtWidgets.QWidget(MicrographMembraneSubtraction_Radonfit)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(10, 60, 601, 41))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.cpus_lineEdit = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.cpus_lineEdit.setObjectName("cpus_lineEdit")
        self.gridLayout.addWidget(self.cpus_lineEdit, 0, 1, 1, 1)
        self.cpus_label = QtWidgets.QLabel(self.gridLayoutWidget)
        self.cpus_label.setObjectName("cpus_label")
        self.gridLayout.addWidget(self.cpus_label, 0, 0, 1, 1)
        self.batch_size_label = QtWidgets.QLabel(self.gridLayoutWidget)
        self.batch_size_label.setObjectName("batch_size_label")
        self.gridLayout.addWidget(self.batch_size_label, 0, 2, 1, 1)
        self.batch_size_lineEdit = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.batch_size_lineEdit.setObjectName("batch_size_lineEdit")
        self.gridLayout.addWidget(self.batch_size_lineEdit, 0, 3, 1, 1)
        self.line = QtWidgets.QFrame(MicrographMembraneSubtraction_Radonfit)
        self.line.setGeometry(QtCore.QRect(10, 140, 601, 16))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayoutWidget_2 = QtWidgets.QWidget(MicrographMembraneSubtraction_Radonfit)
        self.horizontalLayoutWidget_2.setGeometry(QtCore.QRect(10, 109, 601, 32))
        self.horizontalLayoutWidget_2.setObjectName("horizontalLayoutWidget_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.kill_pushButton = QtWidgets.QPushButton(self.horizontalLayoutWidget_2)
        self.kill_pushButton.setObjectName("kill_pushButton")
        self.horizontalLayout_2.addWidget(self.kill_pushButton)
        self.launch_pushButton = QtWidgets.QPushButton(self.horizontalLayoutWidget_2)
        self.launch_pushButton.setObjectName("launch_pushButton")
        self.horizontalLayout_2.addWidget(self.launch_pushButton)
        self.LOG_label = QtWidgets.QLabel(MicrographMembraneSubtraction_Radonfit)
        self.LOG_label.setGeometry(QtCore.QRect(300, 150, 31, 16))
        self.LOG_label.setObjectName("LOG_label")
        self.LOG_textBrowser = QtWidgets.QTextBrowser(MicrographMembraneSubtraction_Radonfit)
        self.LOG_textBrowser.setGeometry(QtCore.QRect(10, 170, 601, 151))
        self.LOG_textBrowser.setObjectName("LOG_textBrowser")

        self.retranslateUi(MicrographMembraneSubtraction_Radonfit)
        QtCore.QMetaObject.connectSlotsByName(MicrographMembraneSubtraction_Radonfit)

    def retranslateUi(self, MicrographMembraneSubtraction_Radonfit):
        _translate = QtCore.QCoreApplication.translate
        MicrographMembraneSubtraction_Radonfit.setWindowTitle(_translate("MicrographMembraneSubtraction_Radonfit", "Micrograph Membrane Subtraction - MemXTerminator"))
        self.particles_selected_starfile_label.setText(_translate("MicrographMembraneSubtraction_Radonfit", "Particles selected starfile"))
        self.particles_selected_starfile_browse_pushButton.setText(_translate("MicrographMembraneSubtraction_Radonfit", "Browse..."))
        self.cpus_lineEdit.setText(_translate("MicrographMembraneSubtraction_Radonfit", "15"))
        self.cpus_label.setText(_translate("MicrographMembraneSubtraction_Radonfit", "Cpus"))
        self.batch_size_label.setText(_translate("MicrographMembraneSubtraction_Radonfit", "Batch size"))
        self.batch_size_lineEdit.setText(_translate("MicrographMembraneSubtraction_Radonfit", "30"))
        self.kill_pushButton.setText(_translate("MicrographMembraneSubtraction_Radonfit", "Kill"))
        self.launch_pushButton.setText(_translate("MicrographMembraneSubtraction_Radonfit", "Launch"))
        self.LOG_label.setText(_translate("MicrographMembraneSubtraction_Radonfit", "LOG"))
