""" Blaseball Bet Optimizer

Usage:
    blaseballBetOptimizer.py coins <coins> maxbet <maxbet> [-s <season>] [-d <day>]

Options:
  -h --help     Show this screen.
  -d --day      set day
  -s --season   set season


"""

## Blaseball Bet Odds Optimizer ##
import math
import numpy
import requests
import re

from docopt import docopt

#TODO: add auth (with selenium?) so can get number of coins, max bet automatically

# Manually enter the winning odds for each game, your number of coins, and your current max bet
# gameOdds = [56,63,62,61,55,63,63,53,60,61]

def get_day_season():
    r = requests.get("https://www.blaseball.com/events/streamData").text
    # TODO: scrape from reblased instead? this shit is super big, for just two numbers
    # can't do it with reblased
    season = re.findall("\"season\":(\d+)", r)[0]
    day = re.findall("\"day\":(\d+)", r)[0]
    return int(day)+2, int(season)+1 #note that indexes count from 0 and we want one day in the future
    # this returns the "actual" name of the day/season

def get_odds_dict(js, day, season):
    home_odds = [(game["homeOdds"]*100, game["homeTeamName"]) for game in js]
    away_odds = [(game["awayOdds"]*100, game["awayTeamName"]) for game in js]
    return {i[0]:i[1] for i in home_odds+away_odds}

def get_odds(js, day, season):
    return [(max(game["homeOdds"], game["awayOdds"])*100) for game in js]

def main(coins, currentMaxBet, day=None, season=None):
    if not day and not season:
        day, season = get_day_season()
    print("This is season {}, day {}".format(season, day))
    js = requests.get("https://www.blaseball.com/database/games", params={"day":day-1, "season":season-1}).json()
    oddsDict = get_odds_dict(js, day, season)
    gameOdds = get_odds(js, day, season)
    # coins =   10979
    # currentMaxBet = 640
    EVMode = True

    # Pre-Allocating Arrays
    gameOddsEV = ['0'] * len(gameOdds)
    gameBetsSortedBeg = ['0'] * len(gameOdds)
    gameBets = ['0'] * len(gameOdds)
    totalCoins = coins
    minBet = 0 # Used when EV mode set to False

    # Determine game-set bet order, so high games get max bid
    gameOrder = numpy.argsort(gameOdds)
    gameOrder = gameOrder[::-1]
    # gameSorted = sorted(gameOdds)

    if EVMode == False:
        HighRank = 70
        # Determining bet amounts here
        logCoEf = (1 - minBet)/(math.log1p(HighRank-50))
        print("Log Co-Efficient: " + str(logCoEf))
        for index in range(0,len(gameOdds)):
            gameBets[index] = math.floor( currentMaxBet * ((logCoEf*math.log1p(gameOdds[index] - 50)) + minBet))
            if gameBets[index] > currentMaxBet:
                gameBets[index] = currentMaxBet
        gameBetsSorted = sorted(gameBets, reverse = True)

    if EVMode == True:
        EVmax = (2 - (355*10**-6)*(math.pow((100*(0.77-0.5)), 2.045)))*(0.77) - 1
        EVmin = 0
        EVrange = EVmax - EVmin
        for index in range(0,len(gameOdds)):
            # print(gameOdds[index])
            gameOddsEV[index] = (2 - (355*10**-6)*(math.pow((100*(gameOdds[index]/100 - 0.5)), 2.045)))*(gameOdds[index]/100) - 1
            gameBets[index] = math.floor(currentMaxBet*(gameOddsEV[index]/EVrange))
            if gameBets[index] > currentMaxBet:
                gameBets[index] = currentMaxBet
        gameBetsSorted = sorted(gameBets, reverse = True)

    for index in range(0, len(gameOdds)):
        if totalCoins < gameBetsSorted[index]:
            gameBetsSortedBeg[index] = totalCoins
            gameBetsSorted[index] = totalCoins
        if (totalCoins) <= 0:
            gameBetsSortedBeg[index] = 'Beg'
        totalCoins -= gameBetsSorted[index]
        #print('Total coins is now: ' + str(totalCoins))

    # Output
    print('\nGame\tOdds\tBet')
    print('|||||||||||||||||||')
    for index in range(0,len(gameOdds)):
        if gameBetsSortedBeg[index] == 'Beg':
            gameBetsSorted[index] = gameBetsSortedBeg[index]
            print(f"{gameOrder[index] + 1}" +"\t"+ f"{gameOdds[gameOrder[index]]}" + '\t' + f"{gameBetsSorted[index]}")
        else:
            print('{0: <25} {1}'.format(str(oddsDict[gameOdds[gameOrder[index]]]), str(gameBetsSorted[index])))


if __name__ == "__main__":
    args = docopt(__doc__)
    # print(args)
    main(int(args["<coins>"]), int(args["<maxbet>"]), int(args["<day>"]), int(args["<season>"]))