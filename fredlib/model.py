import enum


class Frequency(enum.Enum):
    Daily = "d"
    Weekly = "w"
    Biweekly = "bw"
    Monthly = "m"
    Quarterly = "q"
    Semiannual = "sa"
    Annual = "a"

    def to_number_of_days(self):
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


class Category:
    def __init__(self, category_id, name, parent_id):
        self.category_id = category_id
        self.name = name
        self.parent_id = parent_id

    def __str__(self):
        return "Name: " + self.name + " ID: " + str(self.category_id) + " Parent id:" + str(self.parent_id)


class Series:
    def __init__(self, series_id, title, last_updated, observation_start, observation_end, frequency_short: str, category_id=0):
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


class Observable:
    def __init__(self, date, value, series_id=0):
        self.date = date
        self.value = float(value)
        self.series_id = series_id

    def __str__(self):
        return "Date: " + str(self.date) + " Value: " + str(self.value) + " Series ID: " + str(self.series_id)
