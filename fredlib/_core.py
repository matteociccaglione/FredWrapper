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
                                          ("observation_end", "TEXT"), ("frequency_short", "TEXT"),
                                          ("category_id",
                                           "TEXT REFERENCES categories(category_id) ON DELETE CASCADE ON UPDATE CASCADE")],
                               "observables": [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"), ("date", "TEXT"),
                                               ("value", "REAL"), ("series_id",
                                                                   "TEXT REFERENCES series(series_id) ON DELETE CASCADE ON UPDATE CASCADE")],
                               "categories": [("category_id", "INTEGER PRIMARY KEY"), ("name", "TEXT"),
                                              ("parent_id", "INTEGER")]
                           }}

class BadRequestException(Exception):

    """
    ..autoexception::BadRequestException

    This exception is raised when an HTTP request fails.

    :param status_code: An integer representing the HTTP error code
    :type status_code: int
    """

    def __init__(self, status_code):
        super().__init__("Request has failed with HTTP code: " + str(status_code))


class NotSupportedModelType(Exception):
    """
    ..autoexception::NotSupportedModelType

    This exception is raised when an invalid ModelType object is passed to a method or function.

    :param model_type: One of the element contained in the enum ModelType
    :type model_type: ModelType
    """
    def __init__(self, model_type):
        super().__init__("ModelType not supported. Type used: " + str(model_type))


class CategoryNotFound(Exception):
    """
    ..autoexception::CategoryNotFound

    This exception is raised when the retrieval of a category from a database or through the use of FRED's API gives an empty result.

    :param category_id: The ID of the category in FRED
    :type category_id: int
    """
    def __init__(self, category_id):
        super().__init__("Category with id " + str(category_id) + " not found")


class BadDatabaseQuery(Exception):
    """
    ..autoexception::BadDatabaseQuery

    This exception is raised when a malformed or invalid database query is executed.

    :param query: The string representing the SQL query
    :type query: str
    """
    def __init__(self, query):
        super().__init__("Invalid query: " + str(query))


class NotSupportedOperation(Exception):
    """
    ..autoexception::NotSupportedOperation

    This exception is raised when trying to perform an unsupported operation.
    """

    def __init__(self):
        super().__init__("Operation not supported")


class DatabaseWritingError(Exception):
    """
    ..autoexception::DatabaseWritingError

    This exception is raised when a database internal error occurs, following a write operation in the database.

    :param query: The string representing the SQL operation that caused the raising of the exception
    :type query: str
    :param error: The error code returned by the database
    :type error: Any
    """
    def __init__(self, query, error):
        super().__init__("Query :" + str(query) + " has failed with error:" + str(error))


class SeriesNotFound(Exception):
    """
    ..autoexception::SeriesNotFound

    This exception is raised when the retrieval of a series from a database or through the use of FRED's API gives an empty result.

    :param series_id: The unique identifier of the series in FRED
    :type series_id: str
    """
    def __init__(self, series_id):
        super().__init__("Series with id: " + str(series_id) + " not found")


class ModelType(enum.Enum):
    """
    This is an enumeration of the model's classes used in fredlib, representing the various data stored by FRED.
    They are: Category, Series, Observable
    """
    Category = 1
    Series = 2
    Observable = 3


class DataManager:
    """
    ..autoclass::DataManager

    This is an interface defining the fundamental methods of a DataManager object.
    """
    def _get(self, query):
        """
        Private method representing a general retrieval operation.

        :param query: The query to be performed
        :type query: str
        :return: The result of the query.
        :type: Any
        """
        pass

    def get_category(self, category_id) -> Category:
        """
        Method used to retrieve a Category, given its category id.

        :param category_id: The unique identifier of the category in FRED.
        :type category_id: int
        :return: The desired Category object.
        :rtype: Category
        """
        pass

    def get_series(self, category) -> []:
        """
        Method used to retrieve a list of Series, given the category id of the category they belong to.

        :param category: The unique identifier of the category in FRED.
        :type category: int
        :return: The list of the desired Series objects.
        :rtype: List[Series]
        """
        pass

    def get_observables(self, series) -> []:
        """
        Method used to retrieve a list of Observables, given the series id of the time series they belong to.

        :param series: The unique identifier of the series in FRED.
        :type series: str
        :return: The list of the desired Observable objects.
        :rtype: List[Observable]
        """
        pass



class Fred(DataManager):

    """
    ..autoclass::Fred

    This class is used to interact with FRED's services.
    It makes HTTP requests in order to retrieve the desired data in json format.
    It also parses json responses, building the appropriate :class:`ModelType` object representing the data.
    """

    def __init__(self, key):
        """

        :param key: The FRED's API key to use in request operation
        :type key: str
        """
        self.key = key
        self.final_url = "&api_key=" + key + "&file_type=json"

    def _get(self, query):
        '''
        This private method makes a query to FRED's services;
        if the request does not fail, the method returns a json object

        :param query: The initial URL part of the query to FRED's services, without specifying the API key
        :type query: str
        :raises BadRequestException: The method throws an exception if the request fails
        :return: The json object resulting from the query
        :rtype: Any
        '''
        url = query + self.final_url
        request = requests.get(url)
        status_code = request.status_code
        if status_code != 200:
            raise BadRequestException(status_code)
        return request.content

    def _parse(self, json_object, model_type, elem_id=0) -> List[Any]:
        '''
        This method parses a json object into a list of objects whose type is one of those in :class:`ModelType`.
        When parsing observables, only those that have no NaN value are kept.

        :param json_object: The JSON document to be parsed
        :type json_object: str
        :param model_type: The type of expected resulting object
        :type model_type: ModelType
        :param elem_id: It represents the category [resp. series] identifier to which a Series [resp. Observable] belongs
        :type elem_id: int
        :raises NotSupportedModelType: The exception is raised when the model_type parameter is not one of the enum :class:`ModelType`.
        :return: A list of the requested objects.
        :rtype: List[Any]
        '''
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
                                     ser["observation_end"], ser["frequency_short"].lower(), elem_id))
            result = series

        elif model_type == ModelType.Observable:
            observations = dictionary["observations"]
            observables = []
            for obs in observations:
                # Discard observables with NaN value
                if obs["value"] == ".":
                    continue
                observables.append(Observable(obs["date"], obs["value"], elem_id))
            result = observables
        else:
            raise NotSupportedModelType(model_type)

        return result

    def get_category(self, category_id) -> Category:
        """
        This method retrieves a single category from FRED archive, given its category identifier.

        :param category_id: The category unique identifier of the category to be retrieved from FERD
        :type category_id: int
        :raises CategoryNotFound: Raised when a category with such a category identifier does not exist in FRED archive
        :return: The retrieved category object
        :rtype: Category
        """
        url_start = "https://api.stlouisfed.org/fred/category?category_id="
        json_object = self._get(url_start + str(category_id))
        categories = self._parse(json_object, ModelType.Category)
        if len(categories) == 0:
            raise CategoryNotFound(category_id)
        return categories[0]

    def get_single_series(self, series_id) -> Series:
        """
        This method retrieves a single series from FRED archive, given its series identifier.

        :param series_id: The series unique identifier of the series to be retrieved from FERD
        :type series_id: str
        :raises SeriesNotFound: Raised when a series with such a series identifier does not exist in FRED archive
        :return: The retrieved series object
        :rtype: Series
        """
        url_start = "https://api.stlouisfed.org/fred/series?series_id="
        json_object = self._get(url_start + str(series_id))
        series = self._parse(json_object, ModelType.Series)
        if len(series) == 0:
            raise SeriesNotFound(series_id)
        return series[0]

    def get_series(self, category) -> []:
        """
        This method retrieves all the series under a given category from FRED archive, given the category identifier.

        :param category: The category unique identifier of the category of which retrieve the series
        :type category: int
        :return: A list containing the retrieved series. If no series exists under the specified category, the resulting list is empty.
        :rtype: List[Series]
        """
        url_start = "https://api.stlouisfed.org/fred/category/series?category_id="
        json_object = self._get(url_start + str(category))
        return self._parse(json_object, ModelType.Series, category)

    def get_observables(self, series) -> []:
        """
        This method retrieves all the observables, except those with a NaN value, of a time series from FRED archive, given the series identifier.

        :param series: The series unique identifier of the series of which retrieve the observables
        :type series: str
        :return: A list containing the retrieved observables. If no observable exists for the specified series, the resulting list is empty.
        :rtype: List[Observable]
        """
        url_start = "https://api.stlouisfed.org/fred/series/observations?series_id="
        json_object = self._get(url_start + str(series))
        return self._parse(json_object, ModelType.Observable, series)

    def get_category_children(self, category_id) -> []:
        """
        This method retrieves the children categories of a category in the FRED's category tree hierarchy, given the identifier of the parent category.

        :param category_id: The category identifier of the parent category
        :type category_id: int
        :return: A list containing the retrieved categories. If the parent category has no children, the resulting list is empty.
        :rtype: List[Category]
        """
        url_start = "https://api.stlouisfed.org/fred/category/children?category_id="
        json_object = self._get(url_start + str(category_id))
        categories = self._parse(json_object, ModelType.Category)
        return categories



class Database(DataManager):
    """
    ..autoclass::Database

    This class is used to interact with an SQLite database.
    Its main purpose is to write data downloaded from FRED into a local database.
    It also allows to fetch the saved data from the database, parsing them into appropriate objects.
    """

    def __init__(self, db_name: str):
        """

        :param db_name: Name of the database to interact with. If it does not exist, then it will be created.
        :type db_name: str
        """
        if db_name.endswith(".db"):
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
        """
        This method closes the connection with the database.
        """
        self.con.close()

    def _get(self, query):
        """
        This private method makes a query (SQL SELECT) to the database.
        If the query does not fail, the method returns the fetched rows.

        :param query: The SQL query to be performed
        :type query: str
        :raises BadDatabaseQuery: The exception is raised when the query is malformed or is not an SQL SELECT
        :return: A list of SQL records
        :rtype: List[Any]
        """
        if not (query.startswith("SELECT")):
            raise BadDatabaseQuery(query)
        cur = self.con.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        return rows

    def _parse(self, model_type, rows) -> []:
        '''
        This method parses a list of SQL record into a list of objects whose type is one of those in :class:`ModelType`.

        :param model_type: The type of expected resulting object
        :type model_type: ModelType
        :param rows: The list of SQL records to be parsed
        :type rows: List[Any]
        :raises NotSupportedModelType: The exception is raised when the model_type parameter is not one of the enum :class:`ModelType`.
        :return: A list of the requested objects.
        :rtype: List[Any]
        '''
        if len(rows) == 0:
            return []
        if model_type == ModelType.Series:
            returned_series = []
            for row in rows:
                series = Series(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
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
        """
        This method fetches a single category from the database, given its category identifier.

        :param category_id: The category identifier of the category to be fetched.
        :type category_id: int
        :raises CategoryNotFound: Raised when the database query gives an empty result
        :return: A :class:`Category` object representing the fetched category
        :rtype: Category
        """
        statement = "SELECT * FROM categories WHERE category_id =" + str(category_id) + ";"
        rows = self._get(statement)
        categories = self._parse(ModelType.Category, rows)
        if len(categories) > 0:
            return categories[0]
        else:
            raise CategoryNotFound(category_id)

    def get_categories_by_parent_id(self, parent_id) -> []:
        """
        This method fetches from the database all the children categories of a parent category, given the parent category identifier.

        :param parent_id: The category identifier of the parent category
        :type parent_id: int
        :return: A list of :class:`Category` object.
        :rtype: List[Category]
        """
        statement = "SELECT * FROM categories WHERE parent_id=" + str(parent_id) + ";"
        rows = self._get(statement)
        return self._parse(ModelType.Category, rows)

    def get_series(self, category) -> []:
        """
        This method fetches from the database all the series owned by a category , given the category identifier.

        :param category: The category identifier of the category
        :type category: int
        :return: A list of :class:`Series` object.
        :rtype: List[Series]
        """
        statement = "SELECT * FROM series WHERE category_id = " + str(category) + ";"
        rows = self._get(statement)
        return self._parse(ModelType.Series, rows)

    def get_observables(self, series) -> []:
        """
        This method fetches from the database all the observables of a time series , given the series identifier.

        :param series: The series identifier of the series
        :type series: str
        :return: A list of :class:`Series` object.
        :rtype: List[Series]
        """
        statement = "SELECT * FROM observables WHERE series_id ='" + str(series) + "';"
        rows = self._get(statement)
        return self._parse(ModelType.Observable, rows)

    def _push(self, query):
        """
        This method performs a generic write operation into the database.

        :param query: The SQL operation to be performed
        :type query: str
        :raises BadDatabaseQuery: Raised when the specified operation is not a write operation, but it's a read operation.
        :raises DatabaseWritingError: Raised when the writing operation generates an error into the database
        """
        if query.startswith("SELECT"):
            raise BadDatabaseQuery(query)
        cur = self.con.cursor()
        try:
            cur.execute(query)
            self.con.commit()
        except sqlite3.Error as e:
            raise DatabaseWritingError(query, e.args[0])

    def insert_category(self, category: Category):
        """
        This method saves a single :class:`Category` object into the database

        :param category: The :class:`Category` object to be saved
        :type category: Category
        """
        statement = "INSERT INTO categories VALUES ('" + str(category.category_id) + "','" + str(
            category.name) + "'," + str(category.parent_id) + ");"
        self._push(statement)

    def insert_series(self, series: Series):
        """
        This method saves a single :class:`Series` object into the database

        :param series: The :class:`Series` object to be saved
        :type series: Series
        """
        statement = "INSERT INTO series VALUES ('" + str(series.series_id) + "','" + str(
            series.title) + "'" + ",'" + str(series.last_updated) + "'," + "'" + str(
            series.observation_start) + "'," + "'" + str(series.observation_end) + "'," + "'" + str(
            series.frequency_short.value) + "'," + str(series.category_id) + ");"
        self._push(statement)

    def insert_observables(self, observable: Observable):
        """
        This method saves a single :class:`Observable` object into the database

        :param observable: The :class:`Observable` object to be saved
        :type observable: Observable
        """
        attributes = _database_configuration["rows"]["observables"]
        columns = attributes[1][0] + "," + attributes[2][0] + "," + attributes[3][0]
        statement = "INSERT INTO observables (" + columns + ") VALUES ('" + str(observable.date) + "'," + str(
            observable.value) + ",'" + str(observable.series_id) + "');"
        self._push(statement)

    def delete_series(self, series: Series):
        """
        This method deletes a single :class:`Series` object from the database

        :param series: The :class:`Series` object to be deleted
        :type series: Series
        """
        statement = "DELETE  FROM series WHERE series_id='" + series.series_id + "';"
        self._push(statement)

    def is_new_series(self, series: Series) -> bool:
        """
        This method checks if a given :class:`Series` has the last_updated value more recent than its saved copy in the database.
        If the series has not yet been saved in the database or if no observables associated with the series are saved
        in the database, then the series is deemed not up-to-date.

        :param series: The series to be checked
        :type series: Series
        :return: True if the series is not up-to-date; False otherwise.
        :rtype: bool
        """
        try:
            prev_series = self._get_single_series(series.series_id)
            last_date = dt.strptime(prev_series.last_updated.split(" ")[0], "%Y-%m-%d")
            actual_date = dt.strptime(series.last_updated.split(" ")[0], "%Y-%m-%d")
            return actual_date > last_date or len(self.get_observables(series.series_id)) == 0
        except SeriesNotFound:
            return True

    def is_empty_series(self, series: Series) -> bool:
        """
        This method check if no observables are saved in the database for a specific :class:`Series`.

        :param series: The series to check the observables for.
        :type series: Series
        :return: True if the series has not associated observables; False, otherwise.
        :rtype: bool
        """
        return len(self.get_observables(series.series_id)) == 0

    def update_series(self, series: Series, observables: []):
        """
        This method overrides a series and its observables into the database if the series is not up-to-date.

        :param series: The series to be updated
        :type series: Series
        :param observables: The list of :class:`Observables` object to associate with the series
        :type observables: List[Observable]
        """
        if self.is_new_series(series):
            self.delete_series(series)
        self.insert_series(series)
        for obs in observables:
            self.insert_observables(obs)

    def _get_single_series(self, series_id: str) -> Series:
        """
        This method fetches a single :class:`Series` object from the database.

        :param series_id: The series identifier of the series to be fetched.
        :type series_id: str
        :raises SeriesNotFound: Raised when the series is not in the database
        :return: The retrieved :class:`Series` object
        :rtype: Series
        """
        statement = "SELECT * FROM series WHERE series_id ='" + str(series_id) + "';"
        rows = self._get(statement)
        series = self._parse(ModelType.Series, rows)
        if len(series) != 0:
            return series[0]
        else:
            raise SeriesNotFound(series_id)

    def __del__(self):
        self.destroy()
