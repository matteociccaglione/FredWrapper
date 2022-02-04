# This file contains the core classes of the package
import enum
from model import *
import requests
import json
import sqlite3
from typing import List, Any
from datetime import datetime as dt

_database_configuration = {"tables": ["series", "observables", "categories"],
                           "rows": {
                               "series": [("series_id", "TEXT PRIMARY KEY"), ("title", "TEXT"),
                                          ("last_updated", "TEXT"), ("observation_start", "TEXT"),
                                          ("observation_end", "TEXT"),
                                          ("category_id",
                                           "TEXT REFERENCES categories(category_id) ON DELETE CASCADE ON UPDATE CASCADE")],
                               "observables": [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"), ("date", "TEXT"),
                                               ("value", "REAL"), ("series_id",
                                                                   "TEXT REFERENCES series(series_id) ON DELETE CASCADE ON UPDATE CASCADE")],
                               "categories": [("category_id", "INTEGER PRIMARY KEY"), ("name", "TEXT"),
                                              ("parent_id", "INTEGER")]
                           }}


class BadRequestException(Exception):
    def __init__(self, status_code):
        super().__init__("Request has failed with HTTP code: " + str(status_code))


class NotSupportedModelType(Exception):
    def __init__(self, model_type):
        super().__init__("ModelType not supported. Type used: " + str(model_type))


class CategoryNotFound(Exception):
    def __init__(self, category_id):
        super().__init__("Category with id " + str(category_id) + " not found")


class BadDatabaseQuery(Exception):
    def __init__(self, query):
        super().__init__("Invalid query: " + query)


class NotSupportedOperation(Exception):
    def __init__(self):
        super().__init__("Operation not supported")


class DatabaseWritingError(Exception):
    def __init__(self, query, error):
        super().__init__("Query :" + query + " has failed with error:" + str(error))


class SeriesNotFound(Exception):
    def __init__(self, series_id):
        super().__init__("Series with id: " + str(series_id) + " not found")


class ModelType(enum.Enum):
    Category = 1
    Series = 2
    Observable = 3


class DataManager:
    # query in local database or to FRED
    def _get(self, query):
        pass

    def get_category(self, category_id) -> Category:
        pass

    def get_series(self, category) -> []:
        pass

    def get_observables(self, series) -> []:
        pass


class Fred(DataManager):
    def __init__(self, key):
        self.key = key
        self.final_url = "&api_key=" + key + "&file_type=json"

    '''
    This method makes a query to FRED services;
    if the request does not fail, the method returns a json object
    @:param query string Initial part of the url of a FRED's API
    @:return Response json object, result of the query
    
    @:exception BadRequestException the method throws an exception if the request fails
    '''

    def _get(self, query):
        url = query + self.final_url
        request = requests.get(url)
        status_code = request.status_code
        if status_code != 200:
            raise BadRequestException(status_code)
        return request.content

    '''
    This method parses a json object into one of the following classes:
        Category,
        Series,
        Observable.
    If the model_type is not one of the 3 previously listed, the method raises an exception.
    
    @:param json_object String The json object to be parsed
    @:param model_type ModelType One of the enumerated type of the ModelType enum
    @:return List A list of the requested object

    @:exception NotSupportedModelType the method throws an exception 
    if the model_type is not one of the 3 previously listed
    '''

    def _parse(self, json_object, model_type, elem_id=0) -> List[Any]:
        dictionary = json.loads(json_object)
        if model_type == ModelType.Category:
            categories = dictionary["categories"]
            returned_categories = []
            for cat in categories:
                returned_categories.append(Category(int(cat["id"]), cat["name"], int(cat["parent_id"])))
            result = returned_categories
        elif model_type == ModelType.Series:
            list_of_series = dictionary["seriess"]
            series = []
            for ser in list_of_series:
                series.append(Series(ser["id"], ser["title"], ser["last_updated"], ser["observation_start"],
                                     ser["observation_end"], elem_id))
            result = series

        elif model_type == ModelType.Observable:
            observations = dictionary["observations"]
            observables = []
            for obs in observations:
                observables.append(Observable(obs["date"], obs["value"], elem_id))
            result = observables
        else:
            raise NotSupportedModelType(model_type)

        return result

    def get_category(self, category_id) -> Category:
        url_start = "https://api.stlouisfed.org/fred/category?category_id="
        json_object = self._get(url_start + str(category_id))
        categories = self._parse(json_object, ModelType.Category)
        if len(categories) == 0:
            raise CategoryNotFound(category_id)
        return categories[0]

    def get_single_series(self, series_id) -> Series:
        url_start = "https://api.stlouisfed.org/fred/series?series_id="
        json_object = self._get(url_start + str(series_id))
        series = self._parse(json_object, ModelType.Series)
        if len(series) == 0:
            raise SeriesNotFound(series_id)
        return series[0]

    def get_series(self, category) -> []:
        url_start = "https://api.stlouisfed.org/fred/category/series?category_id="
        json_object = self._get(url_start + str(category))
        return self._parse(json_object, ModelType.Series, category)

    def get_observables(self, series) -> []:
        url_start = "https://api.stlouisfed.org/fred/series/observations?series_id="
        json_object = self._get(url_start + str(series))
        return self._parse(json_object, ModelType.Observable, series)

    def get_category_children(self, category_id) -> []:
        url_start = "https://api.stlouisfed.org/fred/category/children?category_id="
        json_object = self._get(url_start + str(category_id))
        categories = self._parse(json_object, ModelType.Category)
        return categories


class Database(DataManager):
    def __init__(self, db_name: str):
        if (db_name.endswith(".db")):
            self.db_name = db_name
        else:
            self.db_name = db_name + ".db"
        self.con = sqlite3.connect(self.db_name)
        cur = self.con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type ='table';")
        tables = cur.fetchall()
        list_of_tables = []
        for tab in tables:
            list_of_tables.append(tab[0])
        for table in _database_configuration["tables"]:
            if not (table in list_of_tables):
                rows = _database_configuration["rows"][table]
                attributes = ""
                for row in rows:
                    if len(attributes) != 0:
                        attributes += ","
                    attributes += row[0] + " " + row[1]
                statement = "CREATE TABLE " + table + "(" + attributes + ");"
                cur.execute(statement)
        self.con.commit()

    def destroy(self):
        self.con.close()

    def _get(self, query):
        if not (query.startswith("SELECT")):
            raise BadDatabaseQuery(query)
        cur = self.con.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        return rows

    def _parse(self, model_type, rows) -> []:
        if len(rows) == 0:
            return []
        if model_type == ModelType.Series:
            returned_series = []
            for row in rows:
                series = Series(row[0], row[1], row[2], row[3], row[4], row[5])
                returned_series.append(series)
            return returned_series

        if model_type == ModelType.Observable:
            observables = []
            for row in rows:
                observable = Observable(row[1], row[2], row[3])
                observables.append(observable)
            return observables

        if model_type == ModelType.Category:
            categories = []
            for row in rows:
                category = Category(row[0], row[1], row[2])
                categories.append(category)
            return categories

        raise NotSupportedModelType(model_type)

    def get_category(self, category_id) -> Category:
        statement = "SELECT * FROM categories WHERE category_id =" + str(category_id) + ";"
        rows = self._get(statement)
        categories = self._parse(ModelType.Category, rows)
        if len(categories) > 0:
            return categories[0]
        else:
            raise CategoryNotFound(category_id)

    def get_categories_by_parent_id(self, parent_id) -> []:
        statement = "SELECT * FROM categories WHERE parent_id=" + str(parent_id) + ";"
        rows = self._get(statement)
        return self._parse(ModelType.Category, rows)

    def get_series(self, category) -> []:
        statement = "SELECT * FROM series WHERE category_id = " + str(category) + ";"
        rows = self._get(statement)
        return self._parse(ModelType.Series, rows)

    def get_observables(self, series) -> []:
        statement = "SELECT * FROM observables WHERE series_id ='" + str(series) + "';"
        rows = self._get(statement)
        return self._parse(ModelType.Observable, rows)

    def _push(self, query):
        if query.startswith("SELECT"):
            raise BadDatabaseQuery(query)
        cur = self.con.cursor()
        try:
            cur.execute(query)
            self.con.commit()
        except sqlite3.Error as e:
            raise DatabaseWritingError(query, e.args[0])

    def insert_category(self, category: Category):
        statement = "INSERT INTO categories VALUES ('" + str(category.category_id) + "','" + str(
            category.name) + "'," + str(category.parent_id) + ");"
        self._push(statement)

    def insert_series(self, series: Series):
        statement = "INSERT INTO series VALUES ('" + str(series.series_id) + "','" + str(
            series.title) + "'" + ",'" + str(series.last_updated) + "'," + "'" + str(
            series.observation_start) + "'," + "'" + str(series.observation_end) + "'," + str(series.category_id) + ");"
        self._push(statement)

    def insert_observables(self, observable: Observable):
        attributes = _database_configuration["rows"]["observables"]
        columns = attributes[1][0] + "," + attributes[2][0] + "," + attributes[3][0]
        statement = "INSERT INTO observables (" + columns + ") VALUES ('" + str(observable.date) + "'," + str(
            observable.value) + ",'" + str(observable.series_id) + "');"
        self._push(statement)

    def delete_series(self, series: Series):
        statement = "DELETE  FROM series WHERE series_id='" + series.series_id + "';"
        self._push(statement)

    def is_new_series(self, series: Series):
        try:
            prev_series = self._get_single_series(series.series_id)
            last_date = dt.strptime(prev_series.last_updated.split(" ")[0], "%Y-%m-%d")
            actual_date = dt.strptime(series.last_updated.split(" ")[0], "%Y-%m-%d")
            return actual_date > last_date or len(self.get_observables(series.series_id)) == 0
        except SeriesNotFound as e:
            return True

    def is_empty_series(self, series: Series) -> bool:
        return len(self.get_observables(series.series_id)) == 0

    def update_series(self, series: Series, observables: []):
        if self.is_new_series(series):
            self.delete_series(series)
        self.insert_series(series)
        for obs in observables:
            self.insert_observables(obs)

    def _get_single_series(self, series_id: str) -> Series:
        statement = "SELECT * FROM series WHERE series_id ='" + str(series_id) + "';"
        rows = self._get(statement)
        series = self._parse(ModelType.Series, rows)
        if len(series) != 0:
            return series[0]
        else:
            raise SeriesNotFound(series_id)

    def __del__(self):
        self.destroy()
