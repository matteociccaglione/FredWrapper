from typing import List
from matplotlib import pyplot as plt
from model import *
from datetime import datetime as dt, datetime, timedelta
from api import *
import numpy as np
import math


class NotPlottableSeries(Exception):
    def __init__(self, series):
        super().__init__("Series: " + str(series) + "is not plottable")


class SeriesGraph:
    def __init__(self, series: Series, date_list, min_y_value, max_y_value, axis_x_values, axis_y_values):
        self.date_list = date_list
        self.min_y_value = min_y_value
        self.max_y_value = max_y_value
        self.series = [series]
        self.axis_x_values = [axis_x_values]
        self.axis_y_values = [axis_y_values]
        self.linear_regression = None

    def plot(self, fig_size=(14, 8), dpi=150, xlabel="Dates", ylabel="Values", title=""):
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
            plt.plot(x, y, label="Linear regression", color = "black")
        plt.legend(loc="best")

    def merge(self, other_graph):
        other_y_min = other_graph.min_y_value
        other_y_max = other_graph.max_y_value
        self.min_y_value = min(self.min_y_value, other_y_min)
        self.max_y_value = max(self.max_y_value, other_y_max)

        other_date_list = other_graph.date_list
        if (other_date_list[0] < self.date_list[0]) and (
                other_date_list[len(other_date_list) - 1] > self.date_list[len(self.date_list) - 1]):
            self.date_list = other_date_list

        self.series.extend(other_graph.series)
        self.axis_x_values.extend(other_graph.axis_x_values)
        self.axis_y_values.extend(other_graph.axis_y_values)

    def merge_multiple_graph(self, *args):
        for arg in args:
            self.merge(arg)

    def add_linear_regression(self, b0, b1):
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


def build_series_graph(series: Series, api_key, db_name="fred.db", observables: List[Observable] = []) -> SeriesGraph:
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

    '''date_list = np.arange(dt.strptime(observables[0].date, "%Y-%m-%d"),
                          dt.strptime(observables[len(observables) - 1].date, "%Y-%m-%d"), timedelta(days=360)).astype(
        datetime)
    '''
    return SeriesGraph(series, date_list, min_values, max_values, dates, values)
