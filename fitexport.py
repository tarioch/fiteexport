import yaml
import requests
from datetime import date, timedelta
import os.path
import sys
from time import sleep

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

accessToken = config['token']
headers = {
    'Authorization': 'Bearer ' + accessToken,
    'Accept-Locale': 'de_DE'
}


def fr(resource, retry=True):
    r = requests.get(resource, headers=headers)
    if 'Retry-After' in r.headers:
        sleepDuration = int(r.headers['Retry-after']) + 10
        if retry:
            print(f"Reached Limit, sleeping for {sleepDuration} seconds")
            sleep(sleepDuration)
            return fr(resource, retry=False)
        else:
            print(f"Reached Limit after sleeping, stopping")
            sys.exit()
    if 'Retry-After' in r.headers:
        sys.exit()

    return r


days = config['days']

with open('data/state.txt', 'r') as f:
    startDay = f.readline()

startDate = date.fromisoformat(startDay)
curDate = startDate

while curDate >= startDate - timedelta(days=days):
    day = curDate.isoformat()
    print(day)
    year = curDate.year
    month = curDate.strftime('%m')

    r = fr(
        f"https://api.fitbit.com/1/user/-/activities/date/{day}.json")
    data = r.json()

    for activity in data['activities']:
        logId = activity['logId']
        tcxresp = fr(
            f"https://api.fitbit.com/1/user/-/activities/{logId}.tcx?includePartialTCX=true")
        with open(f"data/tcx/{day}-{logId}.tcx", 'wb') as f:
            f.write(tcxresp.content)

    activityFile = f"data/{year}-{month}-activity.csv"
    if not os.path.isfile(activityFile):
        with open(activityFile, 'w') as f:
            f.write("""Aktivitäten
Datum,Verbrannte Kalorien,Schritte,Strecke,Stockwerke,Minuten im Sitzen,Minuten mit leichter Aktivität,Minuten mit relativ hoher Aktivität,Minuten mit sehr hoher Aktivität,Aktivitätskalorien
""")

    with open(activityFile, 'a') as f:
        summary = data['summary']
        totalDist = next(
            x for x in summary['distances'] if x['activity'] == 'total')
        row = [
            '"' + curDate.strftime('%d-%m-%Y') + '"',
            '"' + str(summary['caloriesOut']) + '"',
            '"' + str(summary['steps']) + '"',
            '"' + str(totalDist['distance']) + '"',
            '"' + str(summary['floors']) + '"',
            '"' + str(summary['sedentaryMinutes']) + '"',
            '"' + str(summary['lightlyActiveMinutes']) + '"',
            '"' + str(summary['fairlyActiveMinutes']) + '"',
            '"' + str(summary['veryActiveMinutes']) + '"',
            '"' + str(summary['activityCalories']) + '"',
        ]
        f.write(','.join(row))
        f.write('\n')

    curDate = curDate - timedelta(days=1)
    with open('data/state.txt', 'w') as f:
        state = f.write(curDate.isoformat())

# with open('data/weight.csv', 'a') as f:
#     for year in range(2018, 2016, -1):
#         for month in range(12, 0, -1):
#             yearMonth = f"{year}-{month:02d}"
#             print(yearMonth)
#             r = fr(
#                 f"https://api.fitbit.com/1/user/-/body/log/weight/date/{yearMonth}-01/1m.json")
#             data = r.json()
#             for dr in data['weight']:
#                 row = [
#                     '"' + date.fromisoformat(dr['date']
#                                              ).strftime('%d-%m-%Y') + '"',
#                     '"' + str(dr['weight']) + '"',
#                     '"' + str(dr['bmi']) + '"',
#                     '"20"',
#                 ]
#                 f.write(','.join(row))
#                 f.write('\n')
