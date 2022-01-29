# This file contains the core classes of the package
import enum

import requests
import json


class BadRequestException(Exception):
    def __init__(self, status_code):
        super().__init__("Request has failed with HTTP code: " + status_code)


class NotSupportedModelType(Exception):
    def __init__(self, model_type):
        super().__init__("ModelType not supported. Type used: " + model_type)

class CategoryNotFound(Exception):
    def __init__(self, category_id):
        super().__init__("Category with id " + category_id + " not found")


class ModelType(enum.Enum):
    Category = 1
    Series = 2
    Observable = 3


class DataManager:
    # query in local database or to FRED
    def get(self, query):
        pass

    def get_category(self, category_id):
        pass

    def get_series(self, category):
        pass

    def get_observables(self, series):
        pass


class Category:
    def __init__(self, category_id, name, parent_id):
        self.category_id = category_id
        self.name = name
        self.parent_id = parent_id


class Series:
    def __init__(self, series_id, title, last_updated, category_id=0):
        self.series_id = series_id
        self.title = title
        self.last_updated = last_updated
        self.category_id = category_id


class Observable:
    def __init__(self, date, value, series_id=0):
        self.date = date
        self.value = value
        self.series_id = series_id


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
    def _parse(self, json_object, model_type):
        dictionary = json.loads(json_object)
        match model_type:
            case ModelType.Category:
                categories = dictionary["categories"]
                returned_categories = []
                for cat in categories:
                    returned_categories.append(Category(cat["id"], cat["name"], cat["parent_id"]))
                return returned_categories

            case ModelType.Series:
                list_of_series = dictionary["seriess"]
                series = []
                for ser in list_of_series:
                    series.append(Series(ser["id"], ser["title"], ser["last_update"]))
                return series

            case ModelType.Observable:
                observations = dictionary["observations"]
                observables = []
                for obs in observations:
                    observables.append(Observable(obs["date"], obs["value"]))
                return observables

            case _:
                raise NotSupportedModelType(model_type)

    def get_category(self, category_id):
        url_start = "https://api.stlouisfed.org/fred/category?category_id="
        json_object = self._get(url_start + category_id)
        categories = self._parse(json_object, ModelType.Category)
        if len(categories) == 0:
            raise CategoryNotFound(category_id)
        return categories[0]

    def get_series(self, category):
        url_start = "https://api.stlouisfed.org/fred/category/series?category_id="
        json_object = self._get(url_start + category)
        return self._parse(json_object, ModelType.Series)

    def get_observables(self, series):
        url_start = "https://api.stlouisfed.org/fred/series/observations?series_id="
        json_object = self._get(url_start + series)
        return self._parse(json_object, ModelType.Observable)

    def get_category_children(self, category_id):
        url_start = "https://api.stlouisfed.org/fred/category/children?category_id="
        json_object = self._get(url_start + category_id)
        categories = self._parse(json_object, ModelType.Category)
        return categories
