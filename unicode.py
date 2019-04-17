"""TODO."""

from csv import DictReader, DictWriter
from unicodedata import normalize


NORMALIZATION_FORMS = ('NFC', 'NFKC', 'NFD', 'NFKD')


def getAllFormsFromCSVField(inputPath='input.csv', outputPath='output.csv',
                            fieldname='value'):
    """TODO."""
    fieldnames = [fieldname] + [form for form in NORMALIZATION_FORMS]
    with open(outputPath, 'w') as outputFile:
        writer = DictWriter(outputFile, fieldnames=fieldnames)
        writer.writeheader()
        with open(inputPath, 'r') as inputFile:
            for row in DictReader(inputFile):
                writer.writerow({
                    fieldname: row[fieldname]
                } + {
                    form: normalize(form, row[fieldname])
                    for form in NORMALIZATION_FORMS
                })
