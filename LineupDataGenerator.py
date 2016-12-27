import urllib.request
import bs4
from operator import add
import json
import sys

'''
TODO:
ensure that fouls and techs are processed properly
don't forget to include home court advantage
If somebody gets fouled, the people subbing in get penalized for the free throws. Solution: if "free throw 1 of 2" followed by "enters the game for" then switch enters and FT 2 lines entirely. also 2 of 3. also multiple enters
this is also bad because free throw 2 is being counted as a possession

foul -> timeout -> subs -> freethrow make the subs happen after freethrow

check for "violation" not counting as switchs

check thanksgiving- no games played
'''

# Return basketball reference's unique identifier for a player
def Id(tag):
    return tag['href'][11:-5]

# time is minutes elapsed out of 12 in quarter
def GarbageTimeMultiplier(quarter, time, differential):
    garbageTimePenalty = 0.5

    if abs(differential) >= 20:
        return garbageTimePenalty

    # 10+ with 1 min left, 11+ with 2 min, etc. to 21 with 12 min left
    if quarter == 4 and abs(differential) - 12 + time >= 9:
        return garbageTimePenalty

    return 1

def FreethrowSubPreprocess(pbpList):
    
    index = ftIndex = 3
    for playEntry in pbpList[4:]:
        play = list(playEntry)
        index += 1

        if len(play) < 8:
            continue

        playText = play[3].text + play[7].text

        if "free throw 1 of 2" in playText or "free throw 2 of 3" in playText:
            ftIndex = index

        if ("free throw 2 of 2" in playText or "free throw 3 of 3" in playText):
            row = pbpList.pop(index)
            pbpList.insert(ftIndex + 1, row)


def GetStarters(pbpList, quarter, game):
    homePlayers = set()
    awayPlayers = set()
    subs = set()

    # Add team names as players to be modeled?
    # teamsEntry = list(pbpList[1].children)
    # homeTeam = teamsEntry[3].text
    # awayTeam = teamsEntry[11].text
    # homePlayers.add(homeTeam)
    # awayPlayers.add(awayTeam)

    curQuarter = 1

    for playEntry in pbpList[4:]:
        play = list(playEntry)
        if len(play) >= 4:
            if "Start of" in play[3].text:
                curQuarter += 1
                continue

        if len(play) < 8:
            continue

        if curQuarter != quarter:
            continue

        homePlay = play[7]
        awayPlay = play[3]
        
        if homePlay:
            AddPlayers(homePlay, homePlayers, awayPlayers, subs)
        if awayPlay:
            AddPlayers(awayPlay, awayPlayers, homePlayers, subs)

        if len(homePlayers) == 5 and len(awayPlayers) == 5:
            break;
        
    if len(homePlayers) != 5 or len(awayPlayers) != 5:
        if game == "201611010MIA":
            homePlayers.add("waitedi01")
            awayPlayers.add("koufoko01")
        elif game == "201611220NYK":
            awayPlayers.remove("kuzmimi01")
        elif game == "201611120MIA":
            pass
        elif game == "201611230PHI":
            awayPlayers.add("cartevi01")
        elif game == "201611280WAS":
            awayPlayers.add("templga01")
        elif game == "201611300OKC":
            homePlayers.add("roberan03")
            awayPlayers.add("porteot01")
        elif game == "201612010GSW":
            homePlayers.add("greendr01")
            awayPlayers.add("arizatr01")
        elif game == "201612110PHO":
            awayPlayers.add("gallola01")
        else:
            print("Wrong number of players in starting lineup for a quarter!")

              
    return homePlayers, awayPlayers

def AddPlayers(play, playerSet, otherPlayerSet, subs): 
    if "enters the game for" in play.text:
        players = play.find_all('a')
        subs.add(Id(players[0]))
        if Id(players[1]) not in subs:
            playerSet.add(Id(players[1]))
        return
            
    # Everybody mentioned in these plays is on the relevant team
    singleTeamPlays = ["makes 2-pt shot", "makes 3-pt shot", "rebound by", "free throw"]
    for phrase in singleTeamPlays:
        if phrase in play.text:
            players = play.find_all('a')
            for player in players:
                if Id(player) not in subs:
                    playerSet.add(Id(player))

    # First person mentioned in these plays is on the relevant team
    firstMentionedPlays = ["Turnover by", "misses 3-pt shot", "misses 2-pt shot"]
    for phrase in firstMentionedPlays:
        if phrase in play.text:
            player = play.find('a')
            if player:
                if Id(player) not in subs:
                    playerSet.add(Id(player))
                    
    if "Shooting foul by" in play.text:
        players = play.find_all('a')
        if Id(players[0]) not in subs:
            otherPlayerSet.add(Id(players[0]))
        if Id(players[1]) not in subs:
            playerSet.add(Id(players[1]))
    
def Time(play):
    timeStr = play[1].text
    minutes, seconds = timeStr.split(':')
    return float(minutes) + float(seconds) / 60.

def HomePointsScored(play):
    text = play[6].text
    if text[0] == '+':
        return int(text[1:])
    return 0

def AwayPointsScored(play):
    text = play[4].text
    if text[0] == '+':
        return int(text[1:])
    return 0

def WriteStint(data, homePlayers, awayPlayers, homePos, homePoints, awayPos, awayPoints):
    if homePos == 0 and awayPos == 0:
        return

    if len(homePlayers) != 5 or len(awayPlayers) != 5:
        # delete this if they fix the play by play
        if awayPlayers == {'tuckepj01', 'lenal01', 'knighbr03', 'bledser01'} and homePlayers == {'thompkl01', 'iguodan01', 'greendr01', 'curryst01', 'mcgeeja01'}:
            awayPlayers.add("bendedr01")
        else:
            print("Wrong number of players!")
            print(homePlayers, awayPlayers)
            return
    
    newData = [homePos, homePoints, awayPos, awayPoints]
    
    key = str((tuple(sorted(homePlayers)), tuple(sorted(awayPlayers))))
    if key in data:
        #print(data[key], newData)
        data[key] = list(map(add, data[key], newData))
        #print(data[key], newData)
    else:
        data[key] = newData

def GetDataForGame(game):
    url = 'http://www.basketball-reference.com/boxscores/pbp/{}.html'.format(game)
    request = urllib.request.Request(url)
    result = urllib.request.urlopen(request)
    resulttext = result.read()
    #f = open('pbpsource.txt', 'r')
    #resulttext = f.read()
    soup = bs4.BeautifulSoup(resulttext, "html5lib")
    pbpTable = soup.find('table', id="pbp")
    pbpList = list(pbpTable.tbody)[::2]
    FreethrowSubPreprocess(pbpList)

    data = dict()

    quarter = 1
    homePos = awayPos = homePoints = awayPoints = differential = 0

    prevPossession = "neither"

    homePlayers, awayPlayers = GetStarters(pbpList, quarter, game)

    for entry in pbpList[4:]:
        
        play = list(entry)

        # Filtering non-plays, tracking quarters
        if (len(play) < 7):
            if len(play) >= 4:
                if "Start of" in play[3].text:
                    quarter += 1
                    WriteStint(data, homePlayers, awayPlayers, homePos, homePoints, awayPos, awayPoints)
                    homePos = awayPos = homePoints = awayPoints = 0
                    prevPossession = "neither"
                    homePlayers, awayPlayers = GetStarters(pbpList, quarter, game)
                    if len(homePlayers) != 5:
                        print(play[3].text, homePlayers)
                    if len(awayPlayers) != 5:
                        print(play[3].text, awayPlayers)
            continue
        if not isinstance(play[6], bs4.element.Tag):
            continue

        # Home substitutions
        if "enters the game" in play[7].text:
            WriteStint(data, homePlayers, awayPlayers, homePos, homePoints, awayPos, awayPoints)
            homePos = awayPos = homePoints = awayPoints = 0
            prevPossession = "neither"

            players = play[7].find_all('a')
            homePlayers.add(Id(players[0]))
            homePlayers.remove(Id(players[1]))

            #print(play[3].text + play[7].text)

            continue

        # Away substitutions
        if "enters the game" in play[3].text:
            WriteStint(data, homePlayers, awayPlayers, homePos, homePoints, awayPos, awayPoints)
            homePos = awayPos = homePoints = awayPoints = 0
            prevPossession = "none"

            players = play[3].find_all('a')
            awayPlayers.add(Id(players[0]))
            awayPlayers.remove(Id(players[1]))

            #print(play[3].text + play[7].text)

            continue

        playText = play[3].text + play[7].text

        if "timeout" in playText:
            continue

        time = Time(play)

        # Iterate home score
        points = HomePointsScored(play)
        differential += points
        homePoints += points * GarbageTimeMultiplier(quarter, time, differential)

        # Iterate away score
        points = AwayPointsScored(play)
        differential -= points
        awayPoints += points * GarbageTimeMultiplier(quarter, time, differential)

        # Tracking possession
        homePossession = len(play[7].text) > len(play[3].text)

        nonPossessions = ["technical free throw", "tech foul", "Loose ball foul", "Personal foul"]

        for item in nonPossessions:
            if item in playText:
                homePossession = prevPossession
                break

        if prevPossession != homePossession:
            if homePossession:
                homePos += 1
            else:
                awayPos += 1

        #print(homePos, homePoints, awayPos, awayPoints, playText, awayPlayers)

        prevPossession = homePossession

    # Write final stint (no substitution at end of game)
    WriteStint(data, homePlayers, awayPlayers, homePos, homePoints, awayPos, awayPoints)

    # Write data to file
    with open('Games/{}.txt'.format(game), 'w') as f:
        json.dump(data, f)

    return data

#data = GetDataForGame("201611120IND")
#sys.exit()
