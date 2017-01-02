#!/usr/bin/env python
# -*- coding: utf-8 -*

from __future__ import print_function
from PyQt4 import QtCore, QtGui
from OPui_mwindow2 import Ui_OpenPalino
import sys
import os
from shutil import copy
from settings import sett
import datetime
from collections import defaultdict

# TODO:
# add sorting to mlist, according to selected options in menu
# add taxa modification from app
# add Merge Layers or COllumns
# add autosaving option as async


class Form(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(QtGui.QMainWindow, self).__init__(parent)
        self.ui = Ui_OpenPalino()
        self.ui.setupUi(self)
        self.ui.mList.setSortingEnabled(True)
        self.sett = sett()
        self.horizontalHeaderList = []  # blank horizontal header list
        self.colWidthIndex = 2  # index of width of column 2-resizetoContent
        self.showPercents = False  # trigger for showing percents in mList
        self.CountTable = recursivedefaultdict()  # dict with copied counts
        # time stamp to handle multiple results from autocompleter
        self.lastTime = datetime.datetime.now()

        self.setAutocompleter()

        # list of last 3 projects
        if self.sett.main_sett['lastproj'].find(';'):
            self.lastProj = self.sett.main_sett['lastproj'].split(';')
        else:
            self.lastProj = ''

        # path to scrpit catalog
        self.baseDir = os.path.dirname(os.path.abspath(__file__))

        self.prjDir = ''  # working directory
        self.prjName = ''  # project name

        # show important shortcuts below input place
        shortcutsLabel = ''
        i = 0
        Flist = ['F' + str(a) for a in range(1, 11)]
        for val in Flist:
            shortcutsLabel += val + "=" + self.sett.keySC[val]
            # add new line after second shortcut
            if i == 1:
                shortcutsLabel += '\n'
                i = -1
            else:
                shortcutsLabel += '\t\t'
            i += 1
        self.ui.l_keySCuts.setText(shortcutsLabel)

        self.importTaxa()

        # triggers for menu item
        self.ui.actionNew_Project.triggered.connect(self.newProject)
        self.ui.actionOpen_Project.triggered.connect(self.openProject)
        self.ui.actionSave_Project.triggered.connect(self.saveProject)
        self.ui.actionSave_as_Project.triggered.connect(self.saveProjectAs)

        # signals
        self.connect(self.ui.b_newLayer, QtCore.SIGNAL("clicked()"),
                     self.newLayer)
        self.connect(self.ui.b_delLayer, QtCore.SIGNAL("clicked()"),
                     self.deleteLayer)

        self.connect(
            self.ui.b_newCol, QtCore.SIGNAL("clicked()"), self.addCustomCol)
        self.connect(self.ui.b_delCol, QtCore.SIGNAL("clicked()"),
                     self.deleteColumn)

        self.connect(self.ui.inLine, QtCore.SIGNAL("textChanged(QString)"),
                     self.textInput)
        self.connect(self.ui.b_colWidth, QtCore.SIGNAL("clicked()"),
                     self.changeColumnWidth)
        self.ui.mList.cellChanged.connect(self.updateHistory)
        self.ui.mList.itemSelectionChanged.connect(self.updateTotals)
        self.ui.taxaList.itemDoubleClicked.connect(self.doubleClickedTaxa)
        self.connect(self.ui.b_numProc, QtCore.SIGNAL("clicked()"),
                     self.togglePercentValue)

    def setPaths(self, line):
        ''' Sets all necessary paths in settings
            line is full path to project file'''

        tempPathHolder = line.split(os.sep)
        self.prjDir = os.sep.join(tempPathHolder[:-1])

        # set project name
        self.sett.prjName = tempPathHolder[-2]

        # set project name in windows title
        self.setWindowTitle('Open Palino 0.1a - Project: ' +
                            unicode(self.sett.prjName))

        # read taxa and set it in project
        self.sett.taxaDefFile = os.path.join(self.prjDir,
                                             self.sett.main_sett['taxaFile'])

        # set path to history file in project catalog
        self.sett.taxaHistFile = os.path.join(
            self.prjDir,
            self.sett.main_sett['histFile'])

    def newProject(self):  # p
        self.prjFile = str(QtGui.QFileDialog.getSaveFileName(
            self,
            "Open new project",
            self.lastProj[0],
            "(*.txt *.csv)"
            ))

        self.setPaths(self.prjFile)
        # show window for choosing destinantion folder and basic settings

        # copy taxa file to project directory
        copy(os.path.join(self.baseDir, self.sett.taxaDefFile), self.prjDir)

        # insert datestamp in history as beginig of project history
        self.ui.taxaHist.setPlainText(self.sett.main_sett['histSep'].join([
             'Project',
             self.sett.prjName,
             datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n",
             ''
             ]))

        self.setAutocompleter()
        self.ui.mList.clear()

    def openProject(self):
        # get path to project
        self.prjFile = str(QtGui.QFileDialog.getOpenFileName(
            self,
            "Open project",
            self.lastProj[0],
            "(*.txt *.csv)"
            ))

        self.setPaths(self.prjFile)

        goOn = True  # is there taxalist corresponding to project, if not stop
        if QtCore.QFile.exists(self.sett.taxaDefFile):
            self.sett.readTaxaFile(self.sett.taxaDefFile)
            self.importTaxa()
        else:
            window = QtGui.QMessageBox()
            window.setText(
                'No taxa file in project directory, add one to carry on!')
            window.show()
            goOn = False

        if goOn:
            # load counts into mList
            fileBegin = True
            taxaTempList = []
            for row_raw in open(self.prjFile, 'r'):
                row = row_raw.rstrip('\r\n').decode('cp1250')
                if fileBegin:
                    self.horizontalHeaderList = row.split('\t')
                    fileBegin = False
                else:
                    taxaTempList.append(row.split('\t'))

            self.insertCountsToTable(taxaTempList)
            self.ui.mList.setHorizontalHeaderLabels(self.horizontalHeaderList)

            # load history file if exist
            if QtCore.QFile.exists(self.sett.taxaHistFile):
                fileread = open(self.sett.taxaHistFile, 'r').read()
                self.ui.taxaHist.setPlainText(fileread.rstrip('\r\n'))
            else:
                self.generateTaxaHistFile(taxaTempList)

            self.setHorizontalHeadersAlignment()
            self.setAutocompleter()

    def saveProject(self):
        self.saveCounts()
        self.saveHistory()
        self.saveTaxaList()

    def saveProjectAs(self):
        # get path to project
        self.prjFile = str(QtGui.QFileDialog.getSaveFileName(
            self,
            "Save project as",
            self.lastProj[0],
            "(*.txt *.csv)"
            ))

        self.setPaths(self.prjFile)

        # set new project name in history
        self.ui.taxaHist.appendPlainText(self.sett.main_sett['histSep'].join([
             'Project',
             self.sett.prjName,
             datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n",
             ''
             ]))

        self.saveHistory()
        self.saveCounts()
        self.saveTaxaList()

    def generateTaxaHistFile(self, taxa_list):
        histTemp = self.sett.main_sett['histSep'].join([
             'Project',
             self.sett.prjName,
             datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             ''
             ]) + "\r\n"

        for i, row in enumerate(taxa_list):
            row_name = str(row[self.horizontalHeaderList.index('Depth')])
            a = self.sett.main_sett['histSep'].join([
                "New Layer",
                row_name,
                "(" + str(i) + ")",
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]) + '\r\n'
            histTemp += a

            for j, cell in enumerate(row):
                if cell != '0':
                    a = self.sett.main_sett['histSep'].join([
                        str(cell),
                        self.horizontalHeaderList[j],
                        row_name,
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                        ) + '\r\n'
                    histTemp += a

        self.ui.taxaHist.setPlainText(histTemp)
        open(self.sett.taxaHistFile, 'w').write(histTemp)

    def insertCountsToTable(self, taxa_list):
        # taxa_list is list with levels, equal items in every layer
        self.ui.mList.blockSignals(True)
        self.ui.mList.clear()
        self.ui.mList.setRowCount(len(taxa_list)-1)
        self.ui.mList.setColumnCount(len(taxa_list[0])-1)

        for i, row in enumerate(taxa_list):
            for j, col in enumerate(row):
                if self.horizontalHeaderList[j] in self.sett.specDict.keys() +\
                        ['Depth']:
                    if not str(col.isdigit()) or str(col) == '0':
                        item = MyTableWidgetItem('0', 0)
                    else:
                        item = MyTableWidgetItem(str(col), int(col))
                else:
                    if col in ['']:
                        col = ' '
                    item = QtGui.QTableWidgetItem(col)
                self.ui.mList.setItem(i, j, item)

        self.ui.mList.blockSignals(False)

    def newLayer(self):  # p
        colCount = self.ui.mList.columnCount()
        rowCount = self.ui.mList.rowCount()
        # if this is first layer, we need to add name column and creation No
        # self.ui.mList.setRowCount(rowcount + 1)  # adding one new row

        self.ui.mList.blockSignals(True)
        if colCount == 0:  # if no columns we create standard structure
            self.ui.mList.setColumnCount(1)
            colCount = 1
            self.ui.mList.setHorizontalHeaderLabels(["Depth"])

        self.ui.mList.setSortingEnabled(False)

        # take Layer name form user
        layerName, ok = QtGui.QInputDialog.getText(self, 'Name Dialog',
                                                   'Layer depth:')
        layerName = str(layerName)

        # if layername is empty, stop function here
        if not layerName.isdigit():
            return

        self.ui.mList.insertRow(rowCount)

        for i in xrange(colCount):
            if rowCount != 0:
                # adding field with creation order
                self.ui.mList.horizontalHeaderItem(i).text()
                # adding field with name
                if str(self.ui.mList.horizontalHeaderItem(i).text()) == 'Depth':
                    cell = MyTableWidgetItem(layerName, int(layerName))
                    self.ui.mList.setItemSelected(cell, True)
                    self.ui.mList.setItem(rowCount, i, cell)
                # adding field with taxa for counting
                else:
                    if self.horizontalHeaderList[i] in self.sett.specDict.keys():
                        cell = MyTableWidgetItem('0', 0)
                    else:
                        cell = MyTableWidgetItem(' ', 0)
                    self.ui.mList.setItem(rowCount, i, cell)

            # if first layer, add only depth and end loop
            elif i == 0:
                # if first layer there is no sorting set.
                cell = MyTableWidgetItem(layerName, int(layerName))
                self.ui.mList.setItem(rowCount, 0, cell)
                break

        self.ui.mList.setSortingEnabled(True)
        self.ui.mList.blockSignals(False)
        self.ui.taxaHist.appendPlainText(self.sett.main_sett['histSep'].join([
            "New Layer",
            layerName,
            "(" + str(rowCount) + ")",
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            ))
        self.updateHorizontalHeadersList()

    def deleteLayer(self):
        answer = QtGui.MessageBox.question(
                self, "Delete Layer",
                u'Are You sure?',
                QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if answer == QtGui.QMessageBox.Yes:
            self.ui.mList.removeRow(self.ui.mList.currentRow())

    def importTaxa(self):  # p
        # load taxas from dictionary - definition of taxons
        self.ui.taxaList.blockSignals(True)

        # clear taxaList
        self.ui.taxaList.clear()

        # import taxa list with metadata
        if self.sett.taxaFileOK:
            # insert taxa item into taxaList - QTableWidget
            self.ui.taxaList.setColumnCount(len(self.sett.specDict.values()[0]))
            self.ui.taxaList.setRowCount(len(self.sett.scDict.keys()) - 1)
            self.ui.taxaList.setHorizontalHeaderLabels(
                                                self.sett.taxaHeaders[::-1])
            self.ui.taxaList.setAlternatingRowColors(True)
            self.ui.taxaList.verticalHeader().setVisible(False)
            self.ui.taxaList.verticalHeader().setDefaultSectionSize(13)

            # insert taxaList into QTableWidget
            for i, key in enumerate(sorted(self.sett.specDict.keys())):
                row = self.sett.specDict[key]
                row.reverse()
                for j, val in enumerate(row):
                    cell = QtGui.QTableWidgetItem(str(val))
                    if j > 0:
                        cell.setTextAlignment(
                            QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
                    else:
                        cell.setTextAlignment(
                            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                    cell.setFlags(QtCore.Qt.ItemIsSelectable |
                                  QtCore.Qt.ItemIsEnabled)

                    self.ui.taxaList.setItem(i, j, cell)

            self.ui.taxaList.resizeColumnsToContents()
            self.ui.taxaList.setColumnWidth(0, 99)
        else:
            msgBox = QtGui.QMessageBox()
            msgBox.setText(u"Taxa file has wrong format")
            msgBox.exec_()

        self.ui.taxaList.blockSignals(False)

    def addCustomCol(self, colName=''):  # p
        """Adding new column to mList for metada other than taxa
        """
        self.ui.mList.blockSignals(True)
        self.ui.mList.setSortingEnabled(False)

        colCount = self.ui.mList.columnCount()
        rowCount = self.ui.mList.rowCount()

        if colName == '':
            columnName, ok = QtGui.QInputDialog.getText(self, 'Name Dialog',
                                                        'Column Name: ')
            columnName = str(columnName)
        elif colName != '':
            columnName = colName
        else:
            return

        self.ui.mList.insertColumn(colCount)
        colItem = QtGui.QTableWidgetItem(columnName)
        self.ui.mList.setHorizontalHeaderItem(colCount, colItem)
        self.ui.mList.horizontalHeaderItem(colCount).setTextAlignment(
                                                            QtCore.Qt.AlignLeft)

        for i in xrange(rowCount):
            cell = QtGui.QTableWidgetItem(" ")
            self.ui.mList.setItem(i, colCount, cell)

        self.horizontalHeaderList.append(columnName)
        self.ui.mList.setSortingEnabled(True)
        self.ui.mList.blockSignals(False)

    def deleteColumn(self):
        answer = QtGui.MessageBox.question(
                self, "Delete Column",
                u'Are You sure?',
                QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if answer == QtGui.QMessageBox.Yes:
            self.ui.mList.removeColumn(self.ui.mList.currentColumn())

    def textInput(self, text):
        text = str(text)
        self.ui.inLine.blockSignals(True)

        # triggers
        space_index = -1
        multiplier = 1
        multiplier_index = -1
        FullTaxa = False
        codeCheck = False
        species = False
        textTrigg = False

        # itereatige by characters
        i = 0
        while i < len(text):
            if text[i].isdigit() and not textTrigg:
                multiplier = int(text[0:i+1])
                multiplier_index = i + 1
            elif text[i] == ' ' and not FullTaxa:
                textTrigg = True
                space_index = i
            elif text[i] == text[i].upper():
                textTrigg = True
                FullTaxa = True
            i += 1

        b = 0
        if multiplier_index > -1:
            b = multiplier_index

        if len(text[b:]) > 2 and not FullTaxa:
            codeCheck = text[b:]
        else:
            species = text[b:]

        if space_index > -1:
            if len(text[space_index+1:]) == 2:
                codeCheck = text[space_index+1:]

        # if taxa is valid check in dictionaries and process
        taxa = False
        try:
            if codeCheck:
                taxa = self.sett.scDict[codeCheck]
            if species in self.sett.specDict.keys():
                taxa = species
        except:
            pass

        if FullTaxa:
            self.delta = datetime.datetime.now() - self.lastTime
            self.delta = self.delta.total_seconds()
            if self.delta < 0.061 and taxa == self.lastSpec:
                self.ui.inLine.clear()
                self.ui.inLine.blockSignals(False)
                return
            else:
                self.lastTime = datetime.datetime.now()
                self.lastSpec = taxa

        if taxa and self.ui.mList.currentRow() > -1:
            row = self.ui.mList.currentRow()
            if taxa not in self.horizontalHeaderList:
                self.addCustomCol(colName=taxa)

            col = self.horizontalHeaderList.index(taxa)
            try:
                val = self.ui.mList.item(row, col).sortKey
            except:
                val = 0
            val += 1 * multiplier
            it_new = MyTableWidgetItem(str(int(val)), val)
            # it_new.setSelected(True)
            self.ui.mList.blockSignals(True)
            self.ui.mList.setItem(row, col, it_new)
            self.ui.mList.blockSignals(False)
            # self.ui.mList.setItemSelected(row, col)
            # it = self.ui.mList.item(row, col)
            # self.ui.mList.setItemSelected(it, True)
            self.ui.inLine.clear()
            self.updateTotals()
            self.ui.taxaHist.appendPlainText(
                self.sett.main_sett['histSep'].join(
                    [
                     '+' + str(multiplier),
                     str(taxa),
                     self.currentLayerName(),
                     datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]))

        if self.ui.mList.currentRow() == -1:
            window = QtGui.QMessageBox()
            window.setText(
                'Add new Layer or select existing one to add counts')
            window.exec_()
            self.ui.inLine.clear()

        self.ui.inLine.blockSignals(False)

    def keyPressEvent(self, e):
        key = e.key()
        if str(key) in self.sett.FunctionKeysDict.keys():
            val = self.sett.keySC[self.sett.FunctionKeysDict[str(key)]]
            if len(self.sett.keySC[self.sett.FunctionKeysDict[str(key)]]) == 2:
                val = ' ' + val

            self.textInput(
                self.ui.inLine.text() +
                val
                )

    def togglePercentValue(self):
        if not self.showPercents:
            self.showPercents = True
            self.ui.inLine.setEnabled(False)
        else:
            self.showPercents = False
            self.ui.inLine.setEnabled(True)

        rowCount = self.ui.mList.rowCount()
        colCount = self.ui.mList.columnCount()

        self.ui.mList.blockSignals(True)
        for row in range(rowCount):
            # first loop for sum all taxacounts in row
            rowSum = 0
            if self.showPercents:
                rowSum = self.calculateApNapTotal(row)[-1]

            # second loop for calculating proper percent
            for col in range(colCount):
                item = self.ui.mList.item(row, col)
                if self.showPercents and self.horizontalHeaderList[col] in \
                        self.sett.specDict.keys():
                    percent = round(100*float(item.sortKey) / rowSum, 2)
                    newItem = MyTableWidgetItem(str(percent), item.sortKey)
                    # change it to use colorband
                    if percent == 0:
                        newItem.setBackgroundColor(QtGui.QColor('white'))
                        newItem.setTextColor(QtGui.QColor(5, 5, 5, 25))
                    else:
                        # TODO: przepisac rysowanie kolorow do 1 proc i potem od
                        # 60% w gore tez jeden kolor, a pomiedzy klasy
                        newItem.setBackgroundColor(QtGui.QColor(
                            int(255*percent/100),
                            int(255*(100-percent)/100),
                            0,
                            155))
                    self.ui.mList.setItem(row, col, newItem)

                elif self.showPercents and self.horizontalHeaderList[col] \
                        not in self.sett.specDict.keys():
                    pass
                elif not self.showPercents and self.horizontalHeaderList[col] in \
                        self.sett.specDict.keys():
                    newItem = MyTableWidgetItem(
                        str(int(item.sortKey)), item.sortKey)
                    # change it to use colorband
                    newItem.setBackgroundColor(QtGui.QColor('white'))
                    self.ui.mList.setItem(row, col, newItem)

        self.ui.mList.blockSignals(False)

    def copyCountsToMemory(self):
        self.CountTable = recursivedefaultdict()  # clear dict

        colCount = self.ui.mList.columnCount()
        rowCount = self.ui.mList.rowCount()

        for row in range(rowCount):
            for col in range(colCount):
                self.CountTable[row][col] = \
                    int(self.ui.mList.item(row, col).text())

    def updateHistory(self):
        row = self.ui.mList.currentRow()
        col = self.ui.mList.currentColumn()
        self.ui.mList.blockSignals(True)

        text = str(self.ui.mList.item(row, col).text())
        # substitiute sortKey for further sorting
        if self.horizontalHeaderList[col] in self.sett.specDict.keys() + ['Depth']:
            item = MyTableWidgetItem(text, int(text))
            self.ui.mList.setItem(row, col, item)

        self.ui.taxaHist.appendPlainText(self.sett.main_sett['histSep'].join(
            [
                text,
                str(self.horizontalHeaderList[col]),
                str(self.ui.mList.item(row,
                                       self.horizontalHeaderList.index('Depth')
                                       ).text()),
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]))
        self.ui.mList.blockSignals(False)
        self.updateTotals()

    def calculateApNapTotal(self, row=False):

        if not row:
            row = self.ui.mList.currentRow()
        colCount = self.ui.mList.columnCount()
        countsTotal = 0
        countsAP = 0
        countsNAP = 0

        for col in range(colCount):
            if self.horizontalHeaderList[col] in self.sett.specDict.keys():
                # total sum without notSum value in settings file
                if self.sett.specDict[self.horizontalHeaderList[col]][-2] not in\
                        self.sett.main_sett['notTotalSum'].split(';'):
                    countsTotal += int(self.ui.mList.item(row, col).text())
                # AP + NAP , field sum in settings file
                if self.sett.specDict[self.horizontalHeaderList[col]][-2] in \
                        self.sett.main_sett['sumNAP'].split(';'):
                    countsNAP += int(self.ui.mList.item(row, col).text())
                # AP, field sumAP in settings file
                if self.sett.specDict[self.horizontalHeaderList[col]][-2] in \
                        self.sett.main_sett['sumAP'].split(';'):
                    countsAP += int(self.ui.mList.item(row, col).text())

        return [countsAP, countsNAP, countsTotal]

    def updateTotals(self):
        rowSel, colSel = self.getSelectedRowCol()

        uiTotals = [
            self.ui.uiAPValue,
            self.ui.uiNAPValue,
            self.ui.uiTotalValue
            ]

        if len(rowSel) == 1 and not self.showPercents:
            totals = self.calculateApNapTotal(row=rowSel[0])
            for i in range(3):
                uiTotals[i].setText(str(totals[i]))
        else:
            totals = ['---', '---', '---']

        for i in range(3):
            uiTotals[i].setText(str(totals[i]))

    def doubleClickedTaxa(self, item):
        row = item.row()
        species = str(self.ui.taxaList.item(row, 0).text())
        self.textInput(species)

    def getSelectedRowCol(self):
        rowCount = self.ui.mList.rowCount()
        colCount = self.ui.mList.columnCount()
        rowSel = set([])
        colSel = set([])

        for row in range(rowCount):
            for col in range(colCount):
                if self.ui.mList.item(row, col).isSelected():
                    rowSel.add(row)
                    colSel.add(col)

        return list(rowSel), list(colSel)

    def currentLayerName(self):
        nameIndex = self.horizontalHeaderList.index('Depth')
        row = self.ui.mList.currentRow()
        return str(self.ui.mList.item(row, nameIndex).text())

    def setAutocompleter(self):
        # set autocompleter for species in inLine
        self.completer = QtGui.QCompleter()
        self.ui.inLine.setCompleter(self.completer)
        self.model = QtGui.QStringListModel()
        self.completer.setModel(self.model)
        self.model.setStringList(self.sett.specDict.keys())

    def changeColumnWidth(self):
        sizes = [30, 50, 999]
        self.colWidthIndex += 1
        if self.colWidthIndex > 2:
            self.colWidthIndex = 0

        notChangableCol = [
            self.horizontalHeaderList.index('Depth'),
            ]

        for i in range(self.ui.mList.columnCount()):
            if i not in notChangableCol:
                if self.colWidthIndex < 2:
                    self.ui.mList.setColumnWidth(i, sizes[self.colWidthIndex])
                else:
                    self.ui.mList.resizeColumnToContents(i)

    def setHorizontalHeadersAlignment(self):
        colCount = self.ui.mList.columnCount()
        for i in range(colCount):
            self.ui.mList.horizontalHeaderItem(i).setTextAlignment(
                                                            QtCore.Qt.AlignLeft)

    def updateHorizontalHeadersList(self):
        self.horizontalHeaderList = []
        for i in range(self.ui.mList.columnCount()):
            self.horizontalHeaderList.append(
                str(self.ui.mList.horizontalHeaderItem(i).text()))

    def saveTaxaList(self):
        ''' Method save definitions of taxa file to taxafile.txt
        '''

        out = '\t'.join(self.sett.taxaHeaders) + '\r\n'
        for key in sorted(self.sett.specDict.keys()):
            out += '\t'.join(self.sett.specDict[key]) + '\r\n'

        open(self.sett.taxaDefFile, 'w').write(out.encode('cp1250'))

    def saveCounts(self):
        rows = self.ui.mList.rowCount()
        cols = self.ui.mList.columnCount()

        out = '\t'.join(self.horizontalHeaderList) + '\r\n'
        for i in range(rows):
            out_line = []
            for j in range(cols):
                out_line.append(str(self.ui.mList.item(i, j).text()))
            out += '\t'.join(out_line) + '\r\n'

        open(self.prjFile, 'w').write(out.encode('cp1250'))

    def saveHistory(self):
        open(self.sett.taxaHistFile, 'w').write(
            str(self.ui.taxaHist.toPlainText()).encode('cp1250'))


class MyTableWidgetItem(QtGui.QTableWidgetItem):
    def __init__(self, text, sortKey):
        QtGui.QTableWidgetItem.__init__(self, text,
                                        QtGui.QTableWidgetItem.UserType)
        self.sortKey = float(sortKey)
        self.showproc = 0  # 0 - showing row count; 1 - showing %
    # Qt uses a simple < check for sorting items, override this to use the
    # sortKey

    def __lt__(self, other):
        return self.sortKey < other.sortKey


class recursivedefaultdict(defaultdict):
    def __init__(self):
        self.default_factory = type(self)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = Form()
    form.show()
    app.exec_()
    app.deleteLater()
    sys.exit(0)
