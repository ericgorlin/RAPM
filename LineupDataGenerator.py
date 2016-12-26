import urllib.request
import bs4
from operator import add
import json

'''
TODO:
ensure that fouls and techs are processed properly
don't forget to include home court advantage
If somebody gets fouled, the people subbing in get penalized for the free throws. Solution: if "free throw 1 of 2" followed by "enters the game for" then switch enters and FT 2 lines entirely. also 2 of 3. also multiple enters
this is also bad because free throw 2 is being counted as a possession

foul -> timeout -> subs -> freethrow make the subs happen after freethrow

check for "violation" not counting as switch

check thanksgiving- no games played
'''


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
            homePlayers.add("D. Waiters")
            awayPlayers.add("K. Koufos")
        elif game == "201611120MIA":
            pass
        elif game == "201611230PHI":
            pass
        elif game == "201611280WAS":
            pass
        elif game == "201611300OKC":
            pass
        elif game == "201612010GSW":
            pass
        elif game == "201612110PHO":
            pass
        else:
            print("Wrong number of players in starting lineup for a quarter!")

              
    return homePlayers, awayPlayers

def AddPlayers(play, playerSet, otherPlayerSet, subs): 
    if "enters the game for" in play.text:
        players = play.find_all('a')
        subs.add(players[0].text)
        if players[1].text not in subs:
            playerSet.add(players[1].text)
        return
            
    # Everybody mentioned in these plays is on the relevant team
    singleTeamPlays = ["makes 2-pt shot", "makes 3-pt shot", "rebound by", "free throw"]
    for phrase in singleTeamPlays:
        if phrase in play.text:
            players = play.find_all('a')
            for player in players:
                if player.text not in subs:
                    playerSet.add(player.text)

    # First person mentioned in these plays is on the relevant team
    firstMentionedPlays = ["Turnover by", "misses 3-pt shot", "misses 2-pt shot"]
    for phrase in firstMentionedPlays:
        if phrase in play.text:
            player = play.find('a')
            if player:
                if player.text not in subs:
                    playerSet.add(player.text)
                    
    if "Shooting foul by" in play.text:
        players = play.find_all('a')
        if players[0].text not in subs:
            otherPlayerSet.add(players[0].text)
        if players[1].text not in subs:
            playerSet.add(players[1].text)

    if len(playerSet) > 5:
        # Delete this if they fix the play by play
        if "M. Kuzminskas" in playerSet:
            playerSet.remove("M. Kuzminskas")
            return
        print("Too many players!")
    
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
        if awayPlayers == {'E. Bledsoe', 'B. Knight', 'A. Len', 'P. Tucker'} and homePlayers == {'S. Curry', 'D. Green', 'A. Iguodala', 'K. Thompson', 'J. McGee'}:
            awayPlayers.add("D. Bender")
        else:
            print("Wrong number of players!")
            print(homePlayers, awayPlayers)
            return
    
    newData = [homePos, homePoints, awayPos, awayPoints]

    key = str(( tuple(homePlayers), tuple(awayPlayers) ))
    if key in data:
        #print(key, data[key])
        map(add, data[key], newData)
        #print("adding data")
        #print(key, data[key])

    else:
        data[key] = newData
        #print(key, data[key])
        #print("new data")
    #print("")

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
            homePlayers.add(players[0].text)
            homePlayers.remove(players[1].text)

            #print(play[3].text + play[7].text)

            continue

        # Away substitutions
        if "enters the game" in play[3].text:
            WriteStint(data, homePlayers, awayPlayers, homePos, homePoints, awayPos, awayPoints)
            homePos = awayPos = homePoints = awayPoints = 0
            prevPossession = "none"

            players = play[3].find_all('a')
            awayPlayers.add(players[0].text)
            awayPlayers.remove(players[1].text)

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
    f = open('Games/{}.txt'.format(game), 'w')
    json.dump(data, f)
    f.close()

    return data
