import requests
from bs4 import BeautifulSoup
import re


def get_parsed_page(url):
    # This fixes a blocked by cloudflare error i've encountered
    headers = {
        "referer": "https://www.hltv.org/stats",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    return BeautifulSoup(requests.get(url, headers=headers).text, 'lxml')


def get_matches():
    matches = get_parsed_page("http://www.hltv.org/matches/")
    matches_list = {}

    matchdays = matches.find_all("div", {"class": "upcomingMatchesSection"})

    for match in matchdays:
        matchDetails = match.find_all("div", {"class": "upcomingMatch"})
        date = match.find(
            {'span': {'class': 'matchDayHeadline'}}).text.split()[-1]
        for getMatch in matchDetails:
            matchObj = {}

            matchlink = getMatch.find('a', href=True)['href']
            match_id = re.findall('matches\/([0-9]+)\/', matchlink)[0]

            matchObj['date'] = date
            matchObj['link'] = 'https://hltv.org' + matchlink
            matchObj['matchLink'] = matchlink
            matchObj['id'] = match_id
            matchObj['time'] = getMatch.find(
                "div", {"class": "matchTime"}).text.strip()
            matchObj['length'] = getMatch.find(
                "div", {"class": "matchMeta"}).text

            if getMatch.find("div", {"class": "matchEvent"}):
                matchObj['event'] = getMatch.find(
                    "div", {"class": "matchEvent"}).text.strip()
            else:
                matchObj['event'] = getMatch.find(
                    "div", {"class": "matchInfoEmpty"}).text.strip()

            if (getMatch.find_all("div", {"class": "matchTeams"})):
                matchObj['team1'] = getMatch.find_all(
                    "div", {"class": "matchTeam"})[0].text.strip()
                matchObj['team2'] = getMatch.find_all(
                    "div", {"class": "matchTeam"})[1].text.strip()
            else:
                break

            tr = get_parsed_page(matchObj['link']).find_all(
                "tr", {"class": "provider"})
            matchObj['team1_odds'] = 0
            matchObj['team2_odds'] = 0
            for t in tr:
                a = t.find_all('a')
                if len(a) == 4:
                    matchObj['team1_odds'] = float(a[1].text)
                    matchObj['team2_odds'] = float(a[3].text)
                    break

            matches_list[str(match_id)] = matchObj

    return matches_list


def get_results(link: str):
    page = get_parsed_page(link)

    match_info = {
        "team1": page.find("div", {"class": "team1-gradient"}).find("div", {"class": "teamName"}).text,
        "team2": page.find("div", {"class": "team2-gradient"}).find("div", {"class": "teamName"}).text
    }

    if page.find("div", {"class": "countdown"}).text == 'Match over':
        match_info['ended'] = True

        t1 = page.find("div", {"class": "team1-gradient"})
        t2 = page.find("div", {"class": "team2-gradient"})
        t1_won = t1.find("div", {"class": "won"})
        t1_lost = t1.find("div", {"class": "lost"})
        t2_won = t2.find("div", {"class": "won"})
        t2_lost = t2.find("div", {"class": "lost"})

        match_info['team1_score'] = int(t1_lost.text) if t1_won == None else int(t1_won.text)
        match_info['team2_score'] = int(t2_lost.text) if t2_won == None else int(t2_won.text)
    else:
        match_info['ended'] = False
        match_info['team1_score'] = 0
        match_info['team2_score'] = 0

    return match_info
