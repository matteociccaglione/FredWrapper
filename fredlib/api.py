# This file contains exported APIs of the package
from _core import *
import time
from tree import *


def get_children_categories_recursive(parent_category: int, api_key) -> []:
    children = Fred(api_key).get_category_children(parent_category)
    if len(children) == 0:
        return []
    else:
        category_children = []
        for ch in children:
            category_children += get_children_categories_recursive(ch.category_id, api_key) + [ch]
        return category_children


def get_children_categories_iterative(parent_category_id: int, api_key: str, db_name="fred.db") -> []:
    database = Database(db_name)
    # controlla se c'è nel db
    try:
        category = database.get_category(parent_category_id)
        print("IN DB")
        iterative_list = [category]
        result_list = []
        while len(iterative_list) != 0:
            iterative_list += database.get_categories_by_parent_id(iterative_list[0].category_id)
            result_list.append(iterative_list.pop(0))
        # result_list.pop(0)

    except CategoryNotFound:
        # deve prendere le categorie da fred
        print("NOT IN DB")
        fred = Fred(api_key)
        category = fred.get_category(parent_category_id)
        iterative_list = [category]
        result_list = []
        while len(iterative_list) != 0:
            iterative_list += fred.get_category_children(iterative_list[0].category_id)
            time.sleep(0.35)
            result_list.append(iterative_list.pop(0))

        for cat in result_list:
            try:
                database.insert_category(cat)
            except DatabaseWritingError:
                continue
        # result_list.pop(0)

    return result_list


def old_get_children_categories(parent_category: int, api_key: str) -> []:
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


def update_series(series_id: str, api_key: str, db_name="fred.db") -> bool:
    fred = Fred(api_key)
    database = Database(db_name)
    series = fred.get_single_series(series_id)
    if database.is_new_series(series):
        obs = fred.get_observables(series.series_id)
        database.update_series(series, obs)
        return True
    return False


def insert_observables(series_id: str, api_key: str, db_name="fred.db") -> []:
    fred = Fred(api_key)
    database = Database(db_name)
    try:
        database._get_single_series(series_id)
        result = database.get_observables(series_id)
    except SeriesNotFound:
        observables = fred.get_observables(series_id)
        database.insert_observables(observables)
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
