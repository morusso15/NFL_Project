import requests
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from datetime import date

def get_player_id(full_name):
    all_athletes = "https://sports.core.api.espn.com/v3/sports/football/nfl/athletes?limit=20000&active=true"
    all_athletes = requests.get(all_athletes).json()
    for athlete in all_athletes.get('items', {}):
        if athlete.get('fullName').lower() == full_name:
            player_id = athlete.get('id')
            return player_id
    return -1

def find_nfl_week():

    today = str(date.today())

    with open("nfl_dates.txt", "r") as file:
        for line in file:
            week, dates = line.split(":")
            start, end = [d.strip() for d in dates.split("to")]
            if start <= today <= end:
                return week.split(' ')[1]
    
    return 18

def get_team_id(player_id):
    all_ids = {
    1: 'Atlanta Falcons',
    2: 'Buffalo Bills',
    3: 'Chicago Bears',
    4: 'Cincinnati Bengals',
    5: 'Cleveland Browns',
    6: 'Dallas Cowboys',
    7: 'Denver Broncos',
    8: 'Detroit Lions',
    9: 'Green Bay Packers',
    10: 'Tennessee Titans',
    11: 'Indianapolis Colts',
    12: 'Kansas City Chiefs',
    13: 'Las Vegas Raiders',
    14: 'Los Angeles Rams',
    15: 'Miami Dolphins',
    16: 'Minnesota Vikings',
    17: 'New England Patriots',
    18: 'New Orleans Saints',
    19: 'New York Giants',
    20: 'New York Jets',
    21: 'Philadelphia Eagles',
    22: 'Arizona Cardinals',
    23: 'Pittsburgh Steelers',
    24: 'Los Angeles Chargers',
    25: 'San Francisco 49ers',
    26: 'Seattle Seahawks',
    27: 'Tampa Bay Buccaneers',
    28: 'Washington Commanders',
    29: 'Carolina Panthers',
    30: 'Jacksonville Jaguars',
    33: 'Baltimore Ravens',
    34: 'Houston Texans'
    }
    for i in range(1, 35):
        if i == 32 or i == 33:
            continue
        team_id = i
        team_roster = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2024/teams/{team_id}/athletes?limit=200"
        team_roster = requests.get(team_roster).json()
        for athlete in team_roster.get('items', {}):
            athlete_id = athlete['$ref'].split('/')[11].split('?')[0]
            if player_id == athlete_id:
                return [team_id, all_ids[team_id]]

def get_game_id(team_name, week):
    week_page = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2024&seasontype=2&week={week}"
    week_page = requests.get(week_page).json()
    events = week_page.get('events', [])
    for event in events:
        if team_name in event["name"]:
            game_id = event["id"]
            return game_id
    return -1

def get_yards(team_id, player_id, event_id, pass_rush_rec, yards_or_tds):

    stats_url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{event_id}/competitions/{event_id}/competitors/{team_id}/roster/{player_id}/statistics/0"
    stats_response = requests.get(stats_url, timeout=5)
    stats = stats_response.json()
    if stats == {'error': {'message': 'no instance found', 'code': 404}}:
        return -1
    
    categories = stats.get('splits', {}).get('categories', [])
    for category in categories:
        if category.get('name') == pass_rush_rec:
            for stat in category.get('stats', []):
                if stat.get('name') == yards_or_tds:
                    yards = stat.get('displayValue')
                    return yards
                
def main():
    current_week = int(find_nfl_week())
    current_week_backup = current_week
    while True:
        full_name = input("Player Full Name: ").lower()
        player_id = get_player_id(full_name)
        if player_id != -1:
            name_split = full_name.split(" ")
            break
        else:
            print("Please Enter a Valid Player Name")
    while True:
        acceptable_ints = [1, 2, 3]
        pass_rush_rec = int(input("Select Category: 1 = Passing, 2 = Rushing, 3 = Rec: "))
        if pass_rush_rec not in acceptable_ints:
            print("Please Enter a Valid Number")
        else:
            break
    while True:
        acceptable_ints = [1, 2]
        yards_or_tds = int(input("Select Type: 1 = Yards, 2 = Touchdowns: "))
        if yards_or_tds not in acceptable_ints:
            print("Please Enter a Valid Number")
        else:
            break
    team_name = get_team_id(player_id)[1]
    team_id = get_team_id(player_id)[0]
    stats_parsed = []

    if pass_rush_rec == 1:
        pass_rush_rec = "passing"
    elif pass_rush_rec == 2:
        pass_rush_rec = "rushing"
    elif pass_rush_rec == 3:
        pass_rush_rec = "receiving"

    if yards_or_tds == 1:
        yards_or_tds = f"{pass_rush_rec}Yards"
        ylabel = "Yards"
    else:
        ylabel = "Touchdowns"
        yards_or_tds = f"{pass_rush_rec}Touchdowns"

    games_retrieved = 0
    while True:
        acceptable_ints = [i for i in range(1, current_week_backup + 1)]
        desired_games = int(input("How many games back (ex. 5, 10): "))
        if desired_games not in acceptable_ints:
            print("Please Enter a Valid Number")
        else:
            break

    skip_weeks = []
    game_weeks = []

    while games_retrieved < desired_games:
        
        game_id = get_game_id(team_name, current_week)
        damn_stats = get_yards(team_id, player_id, game_id, pass_rush_rec, yards_or_tds)
        if game_id == -1 or damn_stats == -1:
            skip_weeks.append(current_week)
        else:
            game_weeks.append(current_week)
            stats_parsed.append(int(damn_stats))
            games_retrieved += 1

        current_week -= 1  
        if current_week < 1:
            break
    

    plt.bar(game_weeks, stats_parsed, width=0.5, edgecolor='black')
    plt.xlabel("Week", fontdict={'fontsize': 12, 'weight': 'bold'})
    plt.ylabel(ylabel, fontdict={'fontsize': 12, 'weight': 'bold'})
    if min(stats_parsed) < 40:
        plt.ylim(bottom=0)
    else:
        plt.ylim(bottom=min(stats_parsed)-(min(stats_parsed)/2))
    try:
        threshold = float(input("Threshold / Stat Line (Click Enter for None): "))
        if threshold > max(stats_parsed):
            plt.ylim(top=threshold+(threshold/2))
        else:
            plt.ylim(top=max(stats_parsed)+(max(stats_parsed)/2))
        overs = 0
        for game in stats_parsed:
            if game > threshold:
                overs += 1
        name_split = full_name.split(" ")
        name_split[0][0].upper()
        first_name = f"{name_split[0].upper()[0]}{name_split[0].lower()[1:]}"
        last_name = f"{name_split[1].upper()[0]}{name_split[1].lower()[1:]}"
        print(f"In {first_name} {last_name}'s L{len(stats_parsed)} games, he has gone over/met that line {overs}/{len(stats_parsed)} times")
        plt.axhline(y=threshold, color='black', linestyle='-', linewidth=1)
    except ValueError:
        None
    ax = plt.gca()
    if yards_or_tds == "passingYards" or yards_or_tds == "receivingYards":
        ax.yaxis.set_major_locator(MultipleLocator(25))
        ax.yaxis.set_minor_locator(MultipleLocator(5))
    else:
        ax.yaxis.set_major_locator(MultipleLocator(1))
        ax.yaxis.set_minor_locator(MultipleLocator(0.25))
    filtered_weeks = [week for week in range(min(game_weeks), max(game_weeks) + 1) if week not in skip_weeks]
    plt.xticks(filtered_weeks)
    plt.gca().invert_xaxis()
    plt.show()

if "__main__" == __name__:
    main()