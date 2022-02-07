# This file contains exported APIs of the package
from _core import *
import time
from tree import *
from typing import List
import numpy as np


class InvalidOperation(Exception):
    def __init__(self, mex):
        super().__init__(mex)


def get_children_categories_recursive(parent_category: int, api_key) -> List[Category]:
    children = Fred(api_key).get_category_children(parent_category)
    if len(children) == 0:
        return []
    else:
        category_children = []
        for ch in children:
            category_children += get_children_categories_recursive(ch.category_id, api_key) + [ch]
        return category_children


def get_children_categories_iterative(parent_category_id: int, api_key: str, db_name="fred.db") -> List[Category]:
    database = Database(db_name)
    # controlla se c'è nel db
    try:
        category = database.get_category(parent_category_id)
        iterative_list = [category]
        result_list = []
        while len(iterative_list) != 0:
            iterative_list += database.get_categories_by_parent_id(iterative_list[0].category_id)
            first_element = iterative_list.pop(0)
            result_list.append(first_element)
            if first_element.category_id == 0:
                for item in iterative_list:
                    if item.category_id == 0:
                        iterative_list.remove(item)
                        break
        # result_list.pop(0)

    except CategoryNotFound:
        # deve prendere le categorie da fred
        fred = Fred(api_key)
        category = fred.get_category(parent_category_id)
        iterative_list = [category]
        result_list = []
        time_sleep = 0.35
        if parent_category_id == 0:
            time_sleep = 0.8
        while len(iterative_list) != 0:
            iterative_list += fred.get_category_children(iterative_list[0].category_id)
            time.sleep(time_sleep)
            result_list.append(iterative_list.pop(0))

        for cat in result_list:
            try:
                database.insert_category(cat)
            except DatabaseWritingError:
                continue
        # result_list.pop(0)

    return result_list


def get_series(category_id: int, api_key: str, db_name="fred.db") -> List[Series]:
    database = Database(db_name)
    fred = Fred(api_key)
    series = database.get_series(category_id)
    if len(series) == 0:
        series = fred.get_series(category_id)
        for ser in series:
            database.insert_series(ser)
    return series


def update_series(series_id: str, api_key: str, db_name="fred.db") -> bool:
    fred = Fred(api_key)
    database = Database(db_name)
    series = fred.get_single_series(series_id)
    if database.is_new_series(series):
        obs = fred.get_observables(series.series_id)
        database.update_series(series, obs)
        return True
    return False


def get_observables(series_id: str, api_key: str, db_name="fred.db") -> List[Observable]:
    fred = Fred(api_key)
    database = Database(db_name)
    try:
        series = database._get_single_series(series_id)
        if database.is_empty_series(series):
            observables = fred.get_observables(series_id)
            for obs in observables:
                database.insert_observables(obs)
            result = observables
        else:
            result = database.get_observables(series_id)
    except SeriesNotFound:
        observables = fred.get_observables(series_id)
        for obs in observables:
            database.insert_observables(obs)
        result = observables
    return result


def update_category(category_id: int, api_key: str, db_name="fred.db") -> bool:
    fred = Fred(api_key)
    series = fred.get_series(category_id)
    result = True
    for ser in series:
        result = result and update_series(ser.series_id, api_key, db_name)
    return result


def from_list_to_tree(list_of_categories) -> CategoryTree:
    return CategoryTree(list_of_categories)


def moving_average(series: Series, n: int, api_key, db_name="fred.db") -> List[Observable]:
    values = get_observables(series.series_id, api_key, db_name)
    for i in range(0, len(values) - n + 1):
        mean = 0
        for j in range(0, n):
            mean += values[i + j].value
        values[i].value = mean / n
    return values[:len(values) - n + 1]


def prime_differences(series: Series, api_key, db_name="fred.db") -> List[Observable]:
    values = get_observables(series.series_id, api_key, db_name)
    for i in range(1, len(values)):
        values[i - 1].value = values[i].value - values[i - 1].value
    return values[:len(values) - 1]


def prime_differences_percent(series: Series, api_key, db_name="fred.db") -> List[Observable]:
    values = get_observables(series.series_id, api_key, db_name)
    for i in range(1, len(values)):
        prime_diff = values[i].value - values[i - 1].value
        if values[i - 1].value != 0:
            values[i - 1].value = prime_diff / values[i - 1].value
        else:
            values[i - 1].value = float("NaN")

    return values[:len(values) - 1]


def compute_covariance(series1: Series, series2: Series, api_key, db_name="fred.db"):
    observables1 = get_observables(series1.series_id, api_key, db_name)
    observables2 = get_observables(series2.series_id, api_key, db_name)
    if len(observables2) == len(observables1):
        values = []
        for i in range(0, len(observables1)):
            values.append(observables1[i].value)
        values1 = np.array(values)
        values = []
        for i in range(0, len(observables2)):
            values.append(observables2[i].value)
        values2 = np.array(values)
        covariance = np.cov(values1, values2)
        return covariance
    else:
        raise InvalidOperation("Covariance not computable")


def linear_regression(series: Series, api_key, db_name="fred.db"):
    observables = get_observables(series.series_id, api_key, db_name)
    values_x = []
    values_y = []
    for obs in observables:
        days = (dt.strptime(obs.date, "%Y-%m-%d") - dt(1970, 1, 1)).days
        values_x.append(days)
        values_y.append(obs.value)
    cov = np.cov(np.array(values_x), np.array(values_y))[0][1]
    var = np.var(np.array(values_x))
    b1 = cov / var
    b0 = np.mean(np.array(values_y)) - (b1 * np.mean(np.array(values_x)))
    return b0, b1
