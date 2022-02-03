# This file is for testing purposes only
from _core import *
from api import *
api_key = "e4c748a06f5ed75a6277731745e18fcf"


def fred_test():

    global fred
    fred = Fred(api_key)
    print("Testing for fred api")
    print("Test categories")
    cat = fred.get_category(1)
    print(cat)
    print("Test series")
    series = fred.get_series(cat.category_id)
    for ser in series:
        print(ser)
    print("Test observables")
    for ser in series:
        observables = fred.get_observables(ser.series_id)
        for obs in observables:
            print(obs)

def test_database():

    fred = Fred(api_key)
    print("Fred object created")
    """
    series = fred.get_series(1)
    print("Series taken")
    """
    database = Database("test")
    print("Database created")
    """
    for ser in series:
        try:
            database.update_series(ser)
            observables = fred.get_observables(ser.series_id)
            for obs in observables:
                database.insert_observables(obs)
        except DatabaseWritingError as e:
            print(e.args[0])
            """
    series = database.get_series(1)
    for ser in series:
        print(ser)
        observables = database.get_observables(ser.series_id)
        for obs in observables:
            print(obs)
    database.destroy()


def test_api_children():
    all_category = get_children_categories_iterative(10,api_key)
    for cat in all_category:
        print(cat)
    cat_from_db = get_children_categories_iterative(10,api_key)
    for cat in cat_from_db:
        print(cat)
    print(len(all_category) == len(cat_from_db))

test_api_children()
