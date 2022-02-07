import enum

"""
..autoclass::Frequency
This enumeration represents the frequency of sampling on observables
"""
class Frequency(enum.Enum):
    Daily = "d"
    Weekly = "w"
    Biweekly = "bw"
    Monthly = "m"
    Quarterly = "q"
    Semiannual = "sa"
    Annual = "a"

    def to_number_of_days(self):
        """
        This method converts the sampling frequency in the corresponding number of days
        :return: Number of days of the sampling frequency
        :rtype: int
        """
        if self is Frequency.Daily:
            return 1
        elif self is Frequency.Weekly:
            return 7
        elif self is Frequency.Biweekly:
            return 14
        elif self is Frequency.Monthly:
            return 30
        elif self is Frequency.Quarterly:
            return 30*4
        elif self is Frequency.Semiannual:
            return 30*6
        elif self is Frequency.Annual:
            return 365


"""
..autoclass::Category
This class represents a Category as intended by FRED
"""
class Category:
    def __init__(self, category_id, name, parent_id):
        """
        :param category_id: Unique identifier of the category
        :type category_id: int
        :param name: Name of the category
        :type name: str
        :param parent_id: Category identifier of the parent category in FRED's category tree hierarchy
        :type parent_id: int
        """
        self.category_id = category_id
        self.name = name
        self.parent_id = parent_id

    def __str__(self):
        return "Name: " + self.name + " ID: " + str(self.category_id) + " Parent id:" + str(self.parent_id)


"""
..autoclass::Series
This class represents a Series as intended by FRED
"""
class Series:
    def __init__(self, series_id, title, last_updated, observation_start, observation_end, frequency_short: str, category_id=0):
        """
        :param series_id: Unique identifier of the series
        :type series_id: str
        :param title: Title of the series
        :type title: str
        :param last_updated: Last update date of the series
        :type last_updated: str
        :param observation_start: Initial data observation date
        :type observation_start: str
        :param observation_end: Last data observation date
        :type observation_end: str
        :param frequency_short: Sampling frequency of the series
        :type frequency_short: str
        :param category_id: Category identifier of the category to which the series belongs
        :type category_id: int
        """
        self.series_id = series_id
        self.title = title
        self.last_updated = last_updated
        self.category_id = category_id
        self.observation_start = observation_start
        self.observation_end = observation_end
        if frequency_short.startswith("w"):
            self.frequency_short = Frequency.Weekly
        elif frequency_short.startswith("bw"):
            self.frequency_short = Frequency.Biweekly
        elif frequency_short.startswith("d"):
            self.frequency_short = Frequency.Daily
        elif frequency_short.startswith("m"):
            self.frequency_short = Frequency.Monthly
        elif frequency_short.startswith("q"):
            self.frequency_short = Frequency.Quarterly
        elif frequency_short.startswith("sa"):
            self.frequency_short = Frequency.Semiannual
        elif frequency_short.startswith("a"):
            self.frequency_short = Frequency.Annual


    def __str__(self):
        return "ID-> " + str(self.series_id) + " Title-> " + self.title + " Last update-> " + str(
            self.last_updated) + " Observation start -> " + str(self.observation_start) + " Observation end -> " + str(
            self.observation_end) + " Frequency-> " + str(self.frequency_short) + " Category ID-> " + str(self.category_id)


"""
..autoclass::Observable
This class represents an Observable as intended by FRED
"""
class Observable:
    def __init__(self, date, value, series_id=0):
        """
        :param date: The date of the sampling
        :type date: str
        :param value: The sampled value
        :type value: float
        :param series_id: Series identifier of the series to which the observable belongs
        :type series_id: str
        """
        self.date = date
        self.value = float(value)
        self.series_id = series_id

    def __str__(self):
        return "Date: " + str(self.date) + " Value: " + str(self.value) + " Series ID: " + str(self.series_id)
