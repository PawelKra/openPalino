#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtCore


class sett():
    def __init__(self, settFile='ustawienia.txt'):
        self.settFile = settFile
        self.main_sett = {}  # dictionary with main settings
        self.keySC = {}  # dict with key shorcuts (Function keys)
        self.specDict = {}  # dictionary with species to table from taxa file
        self.scDict = {}  # dictionary with SC to species
        self.colWidth = 2  # 0-5 letters;1-10 letters;2-all letters
        self.RC = 'R'  # R-Layers in row; C-Layer in columns
        self.perc = 0  # 0 - show row numbers in table; 1 - percent by layer
        self.prjName = ''  # Project name
        self.taxaFileOK = True  # is taxa file Valid?
        self.taxaDefFile = ''  # name of taxa list
        self.taxaHistFile = ''  # path to history file in project

        # decode function keys for further usager
        self.FunctionKeysDict = {
            str(QtCore.Qt.Key_F1): 'F1',
            str(QtCore.Qt.Key_F2): 'F2',
            str(QtCore.Qt.Key_F3): 'F3',
            str(QtCore.Qt.Key_F4): 'F4',
            str(QtCore.Qt.Key_F5): 'F5',
            str(QtCore.Qt.Key_F6): 'F6',
            str(QtCore.Qt.Key_F7): 'F7',
            str(QtCore.Qt.Key_F8): 'F8',
            str(QtCore.Qt.Key_F9): 'F9',
            str(QtCore.Qt.Key_F10): 'F10',
            str(QtCore.Qt.Key_F12): 'F12',
        }
        # Sorting counting table by:
        # 0-Alfabetic; 1-Creation; 2-Manual; 3-Numeric; 4-Stratigraphic
        self.sortType = 1

        self.readMainSettingsFile()
        self.readTaxaFile(self.main_sett['taxaFile'])

    def readMainSettingsFile(self):
        section = ''
        for line_raw in open(self.settFile, 'r'):
            line = line_raw.rstrip('\n')
            ok = 0

            if len(line) == 0:
                line = ' '

            if line[0] == '[':
                section = line
            elif line.find('=') > -1:
                splitLine = line.split("=")
                ok = 1

            # main section
            if section == '[main]' and ok == 1:
                self.main_sett[splitLine[0]] = splitLine[1]

            # --- KEY SHORTCUTS SECTION ---
            if section == '[keyshortcuts]' and ok == 1:
                sL = splitLine[1]
                # if len(splitLine[1]) == 2:
                    # sL = ' ' + splitLine[1]
                self.keySC[splitLine[0]] = sL

    def readTaxaFile(self, taxaFile):
        self.scDict = {}
        self.specDict = {}
        for line in open(taxaFile, 'r'):
            line = line.decode('cp1250')
            splitLine = line.rstrip('\r\n').split('\t')
            if splitLine[-1] in ['Species', 'species']:
                self.taxaHeaders = splitLine
            else:
                self.scDict[splitLine[-2]] = splitLine[-1]
                self.specDict[splitLine[-1]] = splitLine
                if len(splitLine) != 4:
                    self.taxaFileOK = False
