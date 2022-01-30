class Category:
    def __init__(self, category_id, name, parent_id):
        self.category_id = category_id
        self.name = name
        self.parent_id = parent_id

    def __str__(self):
        return "Name: " + self.name + " ID: " + str(self.category_id) + " Parent id:" + str(self.parent_id)


class Series:
    def __init__(self, series_id, title, last_updated, category_id=0):
        self.series_id = series_id
        self.title = title
        self.last_updated = last_updated
        self.category_id = category_id

    def __str__(self):
        return "ID-> " + str(self.series_id) + " Title-> " + self.title + " Last update-> " + str(self.last_updated) + " Category ID-> " + str(self.category_id)


class Observable:
    def __init__(self, date, value, series_id=0):
        self.date = date
        self.value = value
        self.series_id = series_id

    def __str__(self):
        return "Date: " + str(self.date) + " Value: " + str(self.value) + " Series ID: " + str(self.series_id)

