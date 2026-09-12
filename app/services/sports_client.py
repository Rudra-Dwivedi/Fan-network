"""
Sports data client — example uses TheSportsDB's free tier (no key required
for basic endpoints, key '3' is the public test key).
Docs: https://www.thesportsdb.com/free_sports_api
Swap this for API-Football or another provider if you want live scores/odds.
"""

import json
import requests

BASE_URL = "https://www.thesportsdb.com/api/v1/json/3"


def fetch_teams_by_league(league_name):
    """Fetch teams in a league (e.g. 'English Premier League', 'Indian Premier League').
    Returns a list of dicts ready to insert into `items` (type='team')."""
    resp = requests.get(
        f"{BASE_URL}/search_all_teams.php", params={"l": league_name}, timeout=10
    )
    resp.raise_for_status()
    data = resp.json()

    items = []
    for team in data.get("teams") or []:
        items.append(
            {
                "type": "team",
                "external_id": team["idTeam"],
                "title": team["strTeam"],
                "genre_tags": league_name,
                "metadata": json.dumps(
                    {
                        "badge": team.get("strTeamBadge"),
                        "stadium": team.get("strStadium"),
                        "description": team.get("strDescriptionEN"),
                    }
                ),
            }
        )
    return items
