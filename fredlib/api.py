# This file contains exported APIs of the package
from _core import *
import time


def get_children_categories_recursive(parent_category: int, api_key) -> []:
    children = Fred(api_key).get_category_children(parent_category)
    if len(children) == 0:
        return []
    else:
        category_children = []
        for ch in children:
            category_children += get_children_categories_recursive(ch.category_id, api_key) + [ch]
        return category_children


def get_children_categories_iterative(parent_category: int, api_key: str) -> []:
    fred = Fred(api_key)
    iterative_list = [Category(parent_category, "", 0)]
    result_list = []
    while len(iterative_list) != 0:
        iterative_list += fred.get_category_children(iterative_list[0].category_id)
        time.sleep(0.1)
        result_list.append(iterative_list.pop(0))
    result_list.pop(0)
    return result_list


def get_series(category_id: int, api_key: str, db_name="fred.db") -> []:
    database = Database(db_name)
    fred = Fred(api_key)
    series = database.get_series(category_id)
    if len(series) == 0:
        series = fred.get_series(category_id)
        for ser in series:
            database.insert_series(ser)
    return series


def update_series(series_id: int, api_key: str, db_name="fred.db") -> []:
    fred = Fred(api_key)
    database = Database(db_name)
    series = fred.get_single_series(series_id)
    if database.is_new_series(series):
        obs = fred.get_observables(series.series_id)
        database.update_series(series, obs)
