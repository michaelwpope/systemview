#!/usr/bin/env python

"""
DESCRIPTION
    Suggested additions to SystemView

VERSION
    0.2 - update getTradeList() to handle different trade list file structures
    0.1 - initial release

AUTHOR
    SystemView: John Bollinger <BBands@BollingerBands.com>
    Suggested additions: Michael Pope <michael.pope@telstra.com>
"""


# import external libraries
from systemview import View                         # base systemview class
import sys                                          # system functions
import datetime                                     # date functions
import numpy as np                                  # numpy
import matplotlib.pyplot as plt                     # pyplot
from matplotlib.ticker import MultipleLocator       # format graph axes

# import our system variables from parameters.py
import addParameters as param


# version number
__author__ = "Michael Pope"
__version__ = "0.2"


def string_to_iso_date(date):
    """Convert date string to datetime object."""
    date = date.split(param.dateSeparator)
    if param.dateFormat == "DMY":
        return datetime.date(int(date[2]), int(date[1]), int(date[0]))
    if param.dateFormat == "MDY":
        return datetime.date(int(date[2]), int(date[0]), int(date[1]))
    if param.dateFormat == "YMD":
        return datetime.date(int(date[0]), int(date[1]), int(date[2]))


class addedView(View):
    """Display trading statistics as charts instead of tables."""
    def __init__(self):
        View.__init__(self)

    def getTradeListData(self, fileName):
        """Load the trade list data from a csv file."""
        # open the file
        source = open(fileName, 'r')
        # dump the first line
        source.readline()
        # put the data in our list
        for line in source:
            line.strip() # get rid of the new line
            data = line.split(',')
            # 0 = Symbol, 1 = Trade, 2 = Date, 3 = Price, 4 = Ex. date, 5 = Ex. Price,
            # 6 = % chg, 7 = Profit, 8 = % Profit, 9 = Shares, 10 = Position value,
            # 11 = Cum. Profit, 12 = # bars, 13 = Profit/bar, 14 = MAE, 15 = MFE
            entryDate = string_to_iso_date(data[param.entryDateCol])
            exitDate = string_to_iso_date(data[param.exitDateCol])
            daysInTrade = int(float(data[param.daysInTradeCol]))-1
            try:
                trade = float(data[param.profitCol])
            except:
                trade = float(data[param.exitPriceCol])/float(data[param.entryPriceCol])-1
            self.trades.append([entryDate, trade, daysInTrade, exitDate])
            if trade > 0.0:
                self.wins.append(trade)
            else:
                self.losses.append(trade)

        # add trades into main data list
        # 0 = date, 1 = open, 2 = high, 3 = low, 4 = close, 5 = volume,
        # 6 = indicator 1, 7 = indicator 2, 8 = signal and 9 = equity curve
        # 10 = TimeInDD
        tradeIndex = 0
        for i in xrange(0, len(self.myData)):
            if tradeIndex < len(self.trades) and self.myData[i][0] == self.trades[tradeIndex][0]: # entry date
                self.myData[i][8] = 1
                entry = self.myData[i][4] # entry price
                drawdown = sys.maxint # a large number
                for j in xrange(i, len(self.myData)):
                    if self.myData[j][4] < entry: # drawdown
                        drawdown = self.myData[j][4]
                    if self.myData[j][0] == self.trades[tradeIndex][3]: # exit date
                        self.myData[j][8] = -1
                        if drawdown < entry:
                            self.drawdowns.append([self.myData[i][0], drawdown/entry-1])
                        else:
                            self.drawdowns.append([self.myData[i][0], 0.0])
                        tradeIndex += 1
                        break

    def displayYearlyProfit(self):
        """Display histogram of profit by year."""
        x=[]
        y=[]
        startEquity = self.myData[0][9]
        for i in xrange(0, len(self.myData)-1):
            if self.myData[i][0].year != self.myData[i+1][0].year:
                x.append(self.myData[i][0].year)
                y.append(self.myData[i][9]/startEquity-1)
                startEquity = self.myData[i][9]
        x.append(self.myData[-1][0].year)
        y.append(self.myData[-1][9]/startEquity-1)
        fig, ax = plt.subplots()
        fig.suptitle("John Bollinger's Trade Visualization")
        ax.set_ylabel("yearly profit")
        ax.bar(x, y, color=['green' if p>0 else 'red' for p in y])
        ax.set_ylim(top=max(0,np.max(y)*1.1))
        ax.set_ylim(bottom=min(0,np.min(y)*1.1))
        ax.grid(True)
        ax.set_xlim([x[0]-1, x[-1]+2]) # leave extra space
        ax.xaxis.set_major_locator(MultipleLocator(5))
        fig.autofmt_xdate()
        plt.show()


if __name__ == '__main__':
    # create an instance of our class
    a = addedView()
    # fetch data
    # expecting comma separated data
    # 2016-01-01, open, high, low, close, volume
    a.getData(param.file1)
    # debug print first and last record
    if param.verbose:
        print("First record {0}, {1:0.2f}".format(a.myData[0][0].isoformat(), a.myData[0][4]))
        print("Last record  {0}, {1:0.2f}".format(a.myData[-1][0].isoformat(), a.myData[-1][4]))
    # import Trade List from csv file generated by AmiBroker
    a.getTradeListData(param.file2)
    # calculate returns
    a.calcReturns()
    # calculate equity curve
    a.calcEquityCurve()
    # calculate time to recover peak asset value
    a.calcTimeInDrawdown()
    # calcuate Maximum Adverse Excursion
    a.calcMAE(param.maLength)
    # calculate efficiency
    a.calcEfficiency(param.maLength)
    # calculate in-trade volatility
    a.calcVolatility(param.maLength)
    # calculate summary data
    a.calcSummaryData()
    # print some summary data
    a.printResults()
    # debug print first and last trade
    if param.verbose:
        print("First trade {0}, {1:.2f}%".format(a.trades[0][0].isoformat(), a.trades[0][1] * 100))
        print("Last trade  {0}, {1:.2f}%".format(a.trades[-1][0].isoformat(), a.trades[-1][1] * 100))
    # show a plot of price with trade markers
    if param.displayPriceGraph:
        a.displayPriceGraph()
    if param.displayPriceTradesGraph:
        a.displayPriceTradesGraph(param.distance)
    # show a plot of all trades
    if param.displayTradeGraph:
        a.displayTradeGraph()
    # show a plot of trades versus time
    if param.displayTradesVersusTime:
        a.displayTradesVersusTime()
    # show a plot of the equity curve
    if param.displayEquityCurve:
        a.displayEquityCurve()
    # show a log plot of the equity curve
    if param.displayEquityCurveLog:
        a.displayEquityCurveLog()
    # show a graph of the distribution of returns
    if param.displayDistribution:
        a.displayDistribution()
    # show a graph of drawdowns
    if param.displayDrawdownGraph:
        a.displayDrawdownGraph()
    # show a graph of time in drawdown
    if param.displayTimeInDrawDown:
        a.displayTimeInDrawDown()
    # show an MAE graph
    if param.displayMAE:
        a.displayMAE()
    # show an Efficiency graph
    if param.displayEfficiency:
        a.displayEfficiency()
    # show a graph of in-trade volatility
    if param.displayInTradeVol:
        a.displayInTradeVol()
    # show a graph of profit by calendar year
    if param.displayYearlyProfit:
        a.displayYearlyProfit()

