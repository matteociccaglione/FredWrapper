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


def plot_series(series: Series, api_key, db_name="fred.db"):
    if str(series.observation_start) == "1776-07-04" and series.observation_end == "9999-12-31":
        raise NotPlottableSeries(series)
    observables = get_observables(series.series_id, api_key, db_name)
    if len(observables) <= 1:
        raise NotPlottableSeries(series)
    _sort_observables(observables)
    dates = []
    values = []
    min_values = math.inf
    max_values = -math.inf
    for obs in observables:
        dates.append((dt.strptime(obs.date, "%Y-%m-%d") - dt(1970, 1, 1)).days)
        values.append(obs.value)
        if obs.value < min_values:
            min_values = obs.value
        if obs.value > max_values:
            max_values = obs.value

    fig = plt.figure(figsize=(10, 8), dpi=300)
    plt.title(series.title + " from " + series.observation_start + " to " + series.observation_end)
    plt.xlabel("dates", color='blue', size="large")
    plt.ylabel("values", color='blue', size="large")
    plt.yticks(np.arange(min_values, max_values, (max_values - min_values) / 10))
    date_list = np.arange(dt.strptime(observables[0].date, "%Y-%m-%d"),
                          dt.strptime(observables[len(observables) - 1].date, "%Y-%m-%d"), timedelta(days=360)).astype(
        datetime)
    ticks_x = []
    for date in date_list:
        ticks_x.append(str(date).split(" ")[0])
    list_of_epochday = []
    for date in date_list:
        list_of_epochday.append((date - dt(1970, 1, 1)).days)
    for i in range(0, len(list_of_epochday)):
        print("Day: " + str(list_of_epochday[i]) + " date: " + ticks_x[i])
    plt.xticks(list_of_epochday, ticks_x, rotation=45, size="small")
    plt.plot(dates, values)
