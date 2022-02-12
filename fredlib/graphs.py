"""
This module contains classes and functions for the graphic representation of one or more series and its data.
"""

from typing import List
from matplotlib import pyplot as plt
from model import *
from datetime import datetime as dt, datetime, timedelta
from api import *
import numpy as np
import math


class NotPlottableSeries(Exception):
    """
    ..autoexception::NotPlottableSeries

    This exception is thrown when you try to plot a series that does not have an observable_start and observable_end value or
    that contains at most one observable.
    """
    def __init__(self, series):
        super().__init__("Series: " + str(series) + "is not plottable")



class SeriesGraph:
    """
    This class allows you to graph the progress of a series without getting your hands dirty with the matplotlib API.
    Do not build this class directly but use the build_series_graph function to instantiate an object of type SeriesGraph.
    The class internally makes use of the matplotlib API for graph representation.
    """

    def __init__(self, series: Series, date_list, min_y_value, max_y_value, axis_x_values, axis_y_values):
        """
        Builder of the class.
        Do not instantiate an object of type SeriesGraph using the constructor but use build_series_graph.

        :param series: The series that you want to plot.
        :type series: Series
        :param date_list: A list of datetime objects you want to tick on the x-axis
        :type date_list: List[datetime]
        :param min_y_value: The smallest value among the observables in the series
        :type min_y_value: float
        :param max_y_value: The biggest value among the observables in the series
        :type max_y_value: float
        :param axis_x_values: A list of the x-axis values. Each item on the list must be an epochday list
        :type axis_x_values: List[int]
        :param axis_y_values: A list of the y-axis values. Each item on the list must be a float list
        :type axis_y_values: List[float]
        """
        self.date_list = date_list
        self.min_y_value = min_y_value
        self.max_y_value = max_y_value
        self.series = [series]
        self.axis_x_values = [axis_x_values]
        self.axis_y_values = [axis_y_values]
        self.linear_regression = None

    def plot(self, fig_size=(14, 8), dpi=150, xlabel="Dates", ylabel="Values", title=""):
        """
        This method allows the trend of the series to be represented on a graph.
        Note that the method does not make a call to pyplot.show, so you will need to do it when you want to see the graph.

        :param fig_size: The size of the matplotlib figure, defaults to (14,8)
        :type fig_size: (int,int)
        :param dpi: The dpi of the graph, defaults to 150
        :type dpi: int
        :param xlabel: The label that you want to put on the x-axis, defaults to Dates
        :type xlabel: str
        :param ylabel: The label that you want to put on the y-axis, defaults to Values
        :type ylabel: str
        :param title: The title of the graph. If you use the default value, the title will be the concatenation of series titles, defaults to ""
        :type title: str
        """
        colors = ["blue", "orange", "red", "green", "pink", "grey", "brown", "yellow"]
        plt.figure(figsize=fig_size, dpi=dpi)
        if title == "":
            for ser in self.series:
                title += ser.title + " from " + ser.observation_start + " to " + ser.observation_end + "\n"
        plt.title(title)

        plt.xlabel(xlabel, color='blue', size="large")
        plt.ylabel(ylabel, color='blue', size="large")
        plt.yticks(np.arange(self.min_y_value, self.max_y_value, (self.max_y_value - self.min_y_value) / 10))

        ticks_x = []
        for date in self.date_list:
            ticks_x.append(str(date).split(" ")[0])
        list_of_epochday = []
        for date in self.date_list:
            list_of_epochday.append((date - dt(1970, 1, 1)).days)
        plt.xticks(list_of_epochday, ticks_x, rotation=45, size="small")

        for i in range(len(self.axis_x_values)):
            plt.plot(self.axis_x_values[i], self.axis_y_values[i], color=colors[i], label=self.series[i].title)
        if self.linear_regression is not None:
            x = np.arange(list_of_epochday[0], list_of_epochday[len(list_of_epochday) - 1])
            y = self.linear_regression[1] * x + self.linear_regression[0]
            plt.plot(x, y, label="Linear regression", color="black")
        plt.legend(loc="best")

    def merge(self, other_graph):
        """
        This method allows you to merge the data present in a SeriesGraph instance with the current instance.
        Use this method to configure the SeriesGraph object to plot multiple series on a single graph.
        The method chooses the largest range of values between the two series as values to be inserted on the y axis, while as regards the x axis it uses the dates of the second series if this entirely contains the first (i.e. it starts before and ends after ).
        This method does not plot the graph, to view the graph you must invoke the plot method.

        :param other_graph: The second graph that you want to merge
        :type other_graph: SeriesGraph
        """
        other_y_min = other_graph.min_y_value
        other_y_max = other_graph.max_y_value
        self.min_y_value = min(self.min_y_value, other_y_min)
        self.max_y_value = max(self.max_y_value, other_y_max)

        other_date_list = other_graph.date_list
        if (other_date_list[0] <= self.date_list[0]) and (
                other_date_list[len(other_date_list) - 1] >= self.date_list[len(self.date_list) - 1]):
            self.date_list = other_date_list

        self.series.extend(other_graph.series)
        self.axis_x_values.extend(other_graph.axis_x_values)
        self.axis_y_values.extend(other_graph.axis_y_values)

    def merge_multiple_graph(self, *args):
        """
        This method allows you to merge multiple SeriesGraph instances into one.
        For more information see the merge documentation.

        :param args: A varargs of SeriesGraph objects
        :type args: (SeriesGraph)
        """
        for arg in args:
            self.merge(arg)

    def add_linear_regression(self, b0, b1):
        """
        This method allows you to add a linear regression line to your graph.
        Note that while you can plot multiple plots on one, you can ONLY add a linear regression line.
        Merge operations do not also absorb the linear regression line of the second graph which is therefore lost.

        :param b0: The b0 coefficient of the expression y = b0 + b1*x
        :type b0: float
        :param b1: The b1 coefficient of the expression y = b0 + b1*x
        :type b1: float
        """
        self.linear_regression = (b0, b1)


def _sort_observables(observables):
    for i in range(1, len(observables)):

        key = observables[i]

        # Move elements of arr[0..i-1], that are
        # greater than key, to one position ahead
        # of their current position
        j = i - 1
        while j >= 0 and dt.strptime(key.date, "%Y-%m-%d") < dt.strptime(observables[j].date, "%Y-%m-%d"):
            observables[j + 1] = observables[j]
            j -= 1
        observables[j + 1] = key


def build_series_graph(series: Series, api_key, db_name="fred.db", observables=None) -> SeriesGraph:
    """
    This method allows you to build a SeriesGraph instance.
    By default, this method uses as data associated with a series its observables present in the database or on the internet, but if you want you can pass yourself a list of observables that will be used instead of the "official" ones.
    Use this possibility to build other graphs such as moving average, prime difference graphs etc.

    :param series: The series of which you want to build a graph
    :type series: Series
    :param api_key: A valid Fred API Key
    :type api_key: str
    :param db_name: The name of the database you want to use, defaults to fred.db
    :type db_name: str
    :param observables: A list of observables that you want to use as values of the series, by default it is None and in this case the function use the "ufficial" values, defaults to None
    :type observables: List[Observables]
    :raises BadRequestException: This exception is thrown when an error occurs during http communication
    :raises NotPlottableSeries: This exception is thrown when you try to build a graph for a non plottable series. For more information see the documentation of NotPlottableSeries
    """

    if observables is None:
        observables = []
    if str(series.observation_start) == "1776-07-04" and series.observation_end == "9999-12-31":
        raise NotPlottableSeries(series)
    if len(observables) == 0:
        observables = get_observables(series.series_id, api_key, db_name)
    if len(observables) <= 1:
        raise NotPlottableSeries(series)
    _sort_observables(observables)
    dates = []
    values = []
    datetimes = []
    min_values = math.inf
    max_values = -math.inf
    for obs in observables:
        datetimes.append(dt.strptime(obs.date, "%Y-%m-%d"))
        dates.append((dt.strptime(obs.date, "%Y-%m-%d") - dt(1970, 1, 1)).days)
        values.append(obs.value)
        if obs.value < min_values:
            min_values = obs.value
        if obs.value > max_values:
            max_values = obs.value

    # calculate date_list
    frequency = series.frequency_short.to_number_of_days()

    period_of_days = (dt.strptime(observables[len(observables) - 1].date, "%Y-%m-%d") - dt.strptime(observables[0].date,
                                                                                                    "%Y-%m-%d")).days

    y = period_of_days / frequency
    step = math.ceil(y / 15)
    date_list = []
    for i in range(0, len(datetimes), step):
        date_list.append(datetimes[i])
    return SeriesGraph(series, date_list, min_values, max_values, dates, values)
