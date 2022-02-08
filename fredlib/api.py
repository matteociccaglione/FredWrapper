"""

This module contains the APIs for interacting with Fred.
The APIs store the downloaded data in a database and use local data if already downloaded.
To use an API it is necessary to have an API key which can be obtained by following these instructions: https://fred.stlouisfed.org/docs/api/api_key.html

"""
from _core import *
import time
from tree import *
from typing import List
import numpy as np




class InvalidOperation(Exception):
    """
    This exception is thrown when an error occurs while running our API if the requested operation cannot be performed.

    :param mex: A string reporting the reason for the error
    :type mex: str
    """

    def __init__(self, mex):
        super().__init__(mex)


def get_children_categories_recursive(parent_category: int, api_key) -> List[Category]:
    """
    This function allows to obtain a list of all the sub-categories given an input category using a recursive approach.
    The function returns a Category list and if you want to rebuild a tree structure use the "from_list_to_tree" function.

    This function will always download the data from internet and doesn't save it on a database.

    :param parent_category: Category id of the parent category
    :type parent_category: int
    :param api_key: A valid Fred API Key
    :type api_key: str
    :raises BadRequestException: This exception is thrown when an error occurs during http communication
    :return: A list of all the sub-categories of parent_category
    :rtype: List[Category]
    """
    children = Fred(api_key).get_category_children(parent_category)
    if len(children) == 0:
        return []
    else:
        category_children = []
        for ch in children:
            category_children += get_children_categories_recursive(ch.category_id, api_key) + [ch]
        return category_children


def get_children_categories_iterative(parent_category_id: int, api_key: str, db_name="fred.db") -> List[Category]:
    """
    This function allows to obtain a list of all the sub-categories given an input category using an iterative approach.
    The function returns a Category list and if you want to rebuild a tree structure use the "from_list_to_tree" function.

    If the data does not already exist in a database this may take a long time.
    The function uses local data whenever possible and stores data downloaded via the internet in a database.

    :param parent_category: Category id of the parent category
    :type parent_category: int
    :param api_key: A valid Fred API Key
    :type api_key: str
    :param db_name: The name of the database you want to use, defaults to fred.db
    :type db_name: str
    :raises BadRequestException: This exception is thrown when an error occurs during http communication
    :return: A list of all the sub-categories of parent_category
    :rtype: List[Category]
    """
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
    """
    This function allows you to obtain all the series associated with a certain category as input.
    This function uses local data whenever possible and stores data downloaded over the internet in a database.

    :param category_id: id of the category from which you want to get the series
    :type category_id: int
    :param api_key: A valid Fred API Key
    :type api_key: str
    :param db_name: The name of the database you want to use, defaults to fred.db
    :type db_name: str
    :raises BadRequestException: This exception is thrown when an error occurs during http communication
    :return: A list of all the series associated with the given category id
    :rtype: List[Series]
    """
    database = Database(db_name)
    fred = Fred(api_key)
    series = database.get_series(category_id)
    if len(series) == 0:
        series = fred.get_series(category_id)
        for ser in series:
            database.insert_series(ser)
    return series


def update_series(series_id: str, api_key: str, db_name="fred.db") -> bool:
    """
    This function allows you to update a series given its id.
    Use this function to make sure you always have up-to-date data before carrying out your statistical analysis on a series!

    :param series_id: The id of the series you want to update
    :type series_id: str
    :param api_key: A valid Fred API Key
    :type api_key: str
    :param db_name: The name of the database you want to use, defaults to fred.db
    :type db_name: str
    :raises BadRequestException: This exception is thrown when an error occurs during http communication
    :return: The function returns a boolean which is true if the series has been updated, false otherwise. Note that if the local data is already updated the function will return false
    :rtype: bool
    """
    fred = Fred(api_key)
    database = Database(db_name)
    series = fred.get_single_series(series_id)
    if database.is_new_series(series):
        obs = fred.get_observables(series.series_id)
        database.update_series(series, obs)
        return True
    return False


def get_observables(series_id: str, api_key: str, db_name="fred.db") -> List[Observable]:
    """
    This function allows you to get all the observables given the id of a series.
    The function uses local data if possible and writes all data downloaded via the internet to a database.

    :param series_id: Id of the series from which you want to get the data
    :type series_id: str
    :param api_key: A valid Fred API Key
    :type api_key: str
    :param db_name: The name of the database you want to use, defaults to fred.db
    :type db_name: str
    :raises BadRequestException: This exception is thrown when an error occurs during http communication
    :return: A list of all the observables linked with the given series id
    :rtype: List[Observable]
    """
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
    """
    This function allows you to update all the series linked to a given category.

    :param category_id: id of the category from which you want to update the series
    :type category_id: int
    :param api_key: A valid Fred API Key
    :type api_key: str
    :param db_name: The name of the database you want to use, defaults to fred.db
    :type db_name: str
    :raises BadRequestException: This exception is thrown when an error occurs during http communication
    :return: The function returns a boolean which is true if all the series has been updated, false otherwise. Note that if one of the local data is already updated the function will return false
    :rtype: bool
    """
    fred = Fred(api_key)
    series = fred.get_series(category_id)
    result = True
    for ser in series:
        result = result and update_series(ser.series_id, api_key, db_name)
    return result


def from_list_to_tree(list_of_categories) -> CategoryTree:
    """
    This function allows you to convert a list of categories into a CategoryTree in order to manage access to categories with a tree structure.
    Use this function to construct CategoryTree type objects.

    :param list_of_categories: A list of categories that you want to convert into a tree
    :type list_of_categories: List[Category]
    :return: An instance of CategoryTree populated with the data in the list
    :rtype: CategoryTree
    """
    return CategoryTree(list_of_categories)


def moving_average(series: Series, n: int, api_key, db_name="fred.db") -> List[Observable]:
    """
    This function compute the moving average from a given series.
    The function uses local data if possible and saves all data downloaded via the internet to a database.
    The function returns a list of observables modified with the moving average application.

    :param series: The series on which you want to calculate the moving average
    :type series: Series
    :param n: An integer representing the period of the moving average
    :type n: int
    :param api_key: A valid Fred API Key
    :type api_key: str
    :param db_name: The name of the database you want to use, defaults to fred.db
    :type db_name: str
    :raises BadRequestException: This exception is thrown when an error occurs during http communication
    :return: A list of observables modified with the moving average
    :rtype: List[Observable]
    """
    values = get_observables(series.series_id, api_key, db_name)
    for i in range(0, len(values) - n + 1):
        mean = 0
        for j in range(0, n):
            mean += values[i + j].value
        values[i].value = mean / n
    return values[:len(values) - n + 1]


def prime_differences(series: Series, api_key, db_name="fred.db") -> List[Observable]:
    """
    This function returns the prime differences series given an input series.
    The function uses local data if possible and saves all data downloaded via the internet to a database.
    The function returns a list of observables modified with the prime differences application.

    :param series: The series on which you want to calculate the prime differences
    :type series: Series
    :param api_key: A valid Fred API Key
    :type api_key: str
    :param db_name: The name of the database you want to use, defaults to fred.db
    :type db_name: str
    :raises BadRequestException: This exception is thrown when an error occurs during http communication
    :return: A list of observables modified with the prime differences
    :rtype: List[Observable]

    """
    values = get_observables(series.series_id, api_key, db_name)
    for i in range(1, len(values)):
        values[i - 1].value = values[i].value - values[i - 1].value
    return values[:len(values) - 1]


def prime_differences_percent(series: Series, api_key, db_name="fred.db") -> List[Observable]:
    """
    This function returns the prime percentage differences series given an input series.
    The function uses local data if possible and saves all data downloaded via the internet to a database.
    The function returns a list of observables modified with the prime percentage differences application.

    :param series: The series on which you want to calculate the prime percentage differences
    :type series: Series
    :param api_key: A valid Fred API Key
    :type api_key: str
    :param db_name: The name of the database you want to use, defaults to fred.db
    :type db_name: str
    :raises BadRequestException: This exception is thrown when an error occurs during http communication
    :return: A list of observables modified with the prime percentage differences
    :rtype: List[Observable]

    """
    values = get_observables(series.series_id, api_key, db_name)
    for i in range(1, len(values)):
        prime_diff = values[i].value - values[i - 1].value
        if values[i - 1].value != 0:
            values[i - 1].value = prime_diff / values[i - 1].value
        else:
            values[i - 1].value = float("NaN")

    return values[:len(values) - 1]


def compute_covariance(series1: Series, series2: Series, api_key, db_name="fred.db") -> np.ndarray:
    """
    This function compute the covariance between two series.
    The function uses local data if possible and saves all data downloaded via the internet to a database.
    The function return a numpy ndarray representing the variance covariance matrix.

    :param series1: The first series that you want to use for computation
    :type series1: Series
    :param series2: The second series that you want to use for computation
    :type series2: Series
    :param api_key: A valid Fred API Key
    :type api_key: str
    :param db_name: The name of the database you want to use, defaults to fred.db
    :type db_name: str
    :raises BadRequestException: This exception is thrown when an error occurs during http communication
    :raises InvalidOperation: This exception is thrown if the two series has not the same number of observables
    :return: A numpy ndarray representing the variance covariance matrix
    :rtype: np.ndarray
    """
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


def linear_regression(series: Series, api_key, db_name="fred.db") -> (float, float):
    """
    This function allows to calculate the coefficients of a regression line given an input series.
    The function uses local data if possible and saves all data downloaded via the internet to a database.
    The function returns two elements which are the coefficients b0 and b1 of the following expression for the regression line:
        y = b0 + b1 * x.

    :param series: The series whose regression line you want to calculate
    :type series: Series
    :param api_key: A valid Fred API Key
    :type api_key: str
    :param db_name: The name of the database you want to use, defaults to fred.db
    :type db_name: str
    :raises BadRequestException: This exception is thrown when an error occurs during http communication
    :return: Two values b0 and b1 of the following expression for the regression line: y = b0 + b1*x
    :rtype: (float,float)
    """
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
