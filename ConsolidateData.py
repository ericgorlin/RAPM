import json
import os, sys
import datetime
from operator import add

def AddData(fileName, combinedData):
    print(fileName)
    f = open("Games/" + fileName, 'r')
    data = json.load(f)
    for key in data:
        if key in combinedData:
            #print(key, data[key])
            print("combined", key, data[key], combinedData[key])
            combinedData[key] = list(map(add, combinedData[key], data[key]))
            print("combined", key, data[key], combinedData[key])
            print("")
            
        else:
            combinedData[key] = data[key]

startDate = datetime.date(2016, 10, 25)
endDate = datetime.date(2016, 12, 24)

combinedData = dict()

for fileName in os.listdir("C:/Users/ergorlin/Documents/RAPM/Games/"):
    fileDate = datetime.datetime.strptime(fileName[:8], "%Y%m%d").date()
    if fileDate >= startDate and fileDate < endDate:
        AddData(fileName, combinedData)

outputFileName = "lineupDataFrom{}to{}.txt".format(startDate, endDate)

with open(outputFileName, 'w') as f:
    json.dump(combinedData, f)
