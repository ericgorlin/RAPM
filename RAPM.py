import json
import random
from ast import literal_eval

# http://www.sloansportsconference.com/wp-content/uploads/2015/09/joeSillSloanSportsPaperWithLogo.pdf

def GetOffPrior(name):
    return 0

def GetDefPrior(name):
    return 0

def OffVal(name, offValues):
    try:
        return offValues[name]
    except:
        offValues[name] = GetOffPrior(name)
        return offValues[name]
    
def DefVal(name, defValues):
    try:
        return defValues[name]
    except:
        defValues[name] = GetDefPrior(name)
        return defValues[name]

# Return points per possession scored by both teams
def GetPrediction(homePlayers, awayPlayers, offValues, defValues, homeCourtAdvantageOff, homeCourtAdvantageDef):
    
    homePoints = sum([OffVal(player, offValues) for player in homePlayers]) - sum([DefVal(player, defValues) for player in awayPlayers])
    homePoints += homeCourtAdvantageOff
    awayPoints = sum([OffVal(player, offValues) for player in awayPlayers]) - sum([DefVal(player, defValues) for player in homePlayers])
    awayPoints -= homeCourtAdvantageDef

    return (homePoints, awayPoints)

with open("lineupDataFrom2016-10-25to2016-12-24.txt") as f:
    lineupData = json.load(f)

offValues = dict()
defValues = dict()

# How many more points offense scores at home
homeCourtAdvantageOff = 0
# How many fewer points scored by the away team (positive number which is subtracted)
homeCourtAdvantageDef = 0

# Step size of gradient descent
stepSize = 0.01
# Regularization term
lambdaVal = 0.01


epoch = 1

while epoch < 20:
    totalError = 0
    for key in lineupData:
        homePos, homePoints, awayPos, awayPoints = lineupData[key]
        players = literal_eval(key)
        homePlayers = players[0]
        awayPlayers = players[1]

        homePrediction, awayPrediction = GetPrediction(homePlayers, awayPlayers, offValues, defValues, homeCourtAdvantageOff, homeCourtAdvantageDef)

        homePointsError = homePrediction * homePos - homePoints
        awayPointsError = awayPrediction * awayPos - awayPoints

        totalError += homePointsError**2 + awayPointsError**2

        #print("Home court advantage", awayPointsError, homeCourtAdvantageDef)
        homeCourtAdvantageOff -= stepSize * homePos * (homePointsError + lambdaVal * homeCourtAdvantageOff)
        homeCourtAdvantageDef += stepSize * awayPos * (awayPointsError - lambdaVal * homeCourtAdvantageDef)
        #print("Home court advantage after", homeCourtAdvantageDef)
        for player in homePlayers:
            print("off value", homePointsError, offValues[player])
            offValues[player] -= stepSize * homePos * (homePointsError + lambdaVal * offValues[player])
            print("subsequently:", offValues[player])
            #print("def value", awayPointsError, defValues[player])
            defValues[player] += stepSize * homePos * (awayPointsError - lambdaVal * defValues[player])
            #print("subsequently on defense:", defValues[player])
        for player in awayPlayers:
            offValues[player] -= stepSize * awayPos * (awayPointsError + lambdaVal * offValues[player]) 
            defValues[player] += stepSize * awayPos * (homePointsError - lambdaVal * defValues[player])

    print("Finished with epoch {}, total error {}".format(totalError, epoch))
    epoch += 1
        








