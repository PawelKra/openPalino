#!/usr/bin/env python
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt

tab = []
for lineRaw in open('hucianka/hucianka.txt', 'r'):
    tab.append(lineRaw.rstrip('r\n').split('\t'))

tabProc = []
first = True
depth = []
taxa = []
for row in tab:
    if row[0].isdigit():
        depth.append(int(row[0]))
    suma = 0
    if first:
        first = False
        tabProc.append(row)
    else:
        for col in range(len(row)):
            if col > 0:
                suma += int(row[col])
        for col in range(len(row)):
            if col == 0:
                tabProc.append([])
                tabProc[-1].append(row[col])
            else:
                tabProc[-1].append((100*float(row[col]))/suma)
                if col == 7:
                    taxa.append(100*float(row[col])/suma)


def singlePlot(taxa, depth):
    fig = plt.figure()
    ax = fig.add_subplot(111)

    # ax.plot(taxa, depth, '-')
    ax.fill_betweenx(depth, taxa, 0, color='k')
    ax.xaxis.tick_top()

    ax.set_ylim(max(depth) + 3, min(depth) - 3)
    ax.set_xlim(0, 75)

    plt.show()


if __name__ == '__main__':

    singlePlot(taxa, depth)
