import json
import urllib.request
import bs4
from datetime import date, timedelta
from LineupDataGenerator import GetDataForGame
import sys


# consider regressing against diversion from BPM, and also diversion from 0/replacement level which is like -2.7

#data = GetDataForGame("201611120MIA")
#sys.exit()

#f = open("201611070GSW.txt", 'r')
#data2 = json.load(f)
#f.close()

'''
f = open("badgames.txt", 'r')
badgames = f.readlines()
for game in badgames:
    game = game.replace("\n", '')
    print(game)
    GetDataForGame(game)
    print("\n")
sys.exit()
'''

# iterate through timespan (use play index to get specific timespan priors?)
# iterate through all games in a day
# consider days with no games

startDate = date(2016, 10, 25)
endDate = date(2016, 12, 24)

baseDateUrl = "http://www.basketball-reference.com/boxscores/index.cgi?month={}&day={}&year={}"

date = startDate
while date < endDate:
    dateUrl = baseDateUrl.format(date.month, date.day, date.year)
    print(dateUrl)
    request = urllib.request.Request(dateUrl)
    result = urllib.request.urlopen(request)
    resulttext = result.read()
    soup = bs4.BeautifulSoup(resulttext, "html5lib") # make this and above a shared function
    links = soup.find_all(class_="right gamelink")
    games = [link.a['href'][11:-5] for link in links]
    for game in games:
        try:
            GetDataForGame(game)
            print("Wrote data for " + game)
        except:
            print("Failed to write data for " + game)
    
    date += timedelta(1)
