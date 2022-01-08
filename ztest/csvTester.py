import csv

FILE_NAME = 'configTableTest.csv'

with open(FILE_NAME, 'a', newline='') as fcsv:
    csvWriter = csv.writer(fcsv)
    csvWriter.writerow(['newtic', 'net', 'YES'])