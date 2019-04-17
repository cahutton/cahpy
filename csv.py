"""TODO."""

from collections import defaultdict
from csv import DictReader


def csv_to_dict(csvPath, keyFieldname, sortKey=None):
    """TODO."""
    dict_ = defaultdict(list)
    with csvPath.open('r') as csvFile:
        for row in DictReader(csvFile):
            dict_[row[keyFieldname]].append({
                key: value for key, value in row.items() if key != keyFieldname
            })

    if sortKey is not None:
        for key in dict_:
            dict_[key].sort(key=sortKey)

    return dict_
