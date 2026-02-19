# FPL API Endpoints

All API endpoints from Fantasy Premier League website

## Public

| Endpoint                                                                                | Description                                                                                           |
| :-------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------- |
| `https://fantasy.premierleague.com/api/bootstrap-static/`                               | Main URL for all player IDs, team IDs, team strength, gameweek deadlines                              |
| `https://fantasy.premierleague.com/api/fixtures/`                                       | Fixture of all the games                                                                              |
| `https://fantasy.premierleague.com/api/fixtures/?event=GW`                              | Fixture of game for specific GW                                                                       |
| `https://fantasy.premierleague.com/api/event/GW/live/`                                  | Live results of given GW, it should be numeric                                                        |
| `https://fantasy.premierleague.com/api/entry/TID/`                                      | General info about team TID, such as name, manager, kit colors, leagues joined                        |
| `https://fantasy.premierleague.com/api/entry/TID/history/`                              | This season and previous season performance of given team TID                                         |
| `https://fantasy.premierleague.com/api/entry/TID/transfers/`                            | All transfers of given team TID                                                                       |
| `https://fantasy.premierleague.com/api/entry/TID/event/GW/picks/`                       | Squad picks of team TID for week GW. Both TID and GW should be numeric                                |
| `https://fantasy.premierleague.com/api/leagues-classic/LID/standings/`                  | Information about league with id LID, such as name and standings                                      |
| `https://fantasy.premierleague.com/api/leagues-classic/LID/standings/?page_standings=P` | Page P for leagues LID with more than 50 teams                                                        |
| `https://fantasy.premierleague.com/api/element-summary/EID/`                            | Details of player EID, such as fixtures with FDR, current season details, and previous season summary |
| `https://fantasy.premierleague.com/api/regions/`                                        | FPL Region List                                                                                       |
| `https://fantasy.premierleague.com/api/stats/best-classic-private-leagues/`             | List of best leagues                                                                                  |

> [!INFO]
> Capital words (GW, TID, EID, LID) should be replaced before the query. All of these values should be numeric.

## Private

| Endpoint                                                            | Description                                                                                   |
| :------------------------------------------------------------------ | :-------------------------------------------------------------------------------------------- |
| `https://fantasy.premierleague.com/api/my-team/TID/`                | Details about your own team: your squad picks, current sell prices, chip status and transfers |
| `https://fantasy.premierleague.com/api/entry/TID/transfers-latest/` | List of transfers you have performed in current period                                        |
| `https://fantasy.premierleague.com/api/me/`                         | Information about your profile (Name, Team ID, etc...)                                        |

> [!INFO]
> TID value should be your own team ID.

## Reference

<https://cheatography.com/sertalpbilal/cheat-sheets/fpl-api-endpoints/>
