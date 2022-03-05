import json
import os

from sklearn.model_selection import ParameterSampler
from scipy.stats.distributions import uniform
import numpy as np

rng = np.random.RandomState(0)
param_grid = {
    'e': uniform(0, 0.5),
    'to_factor': uniform(0, 1),
    'window_size': [2, 5, 10, 20, 40],
    'max_concession': uniform(0, 0.5),
    'fn': [1, 2, 3, 4, 5],
    'alpha': uniform(0.9, 1.2),
    'beta': uniform(0, 0.2),
    'time': uniform(0.8, 0.98),
    'a_const': uniform(0.8, 0.95),
    'ac': [1, 2],
    'fit': [1, 2]
}

n_iter = 10

param_list = list(ParameterSampler(param_grid, n_iter=n_iter,
                                   random_state=rng))
rounded_list = [0, [dict((k, round(v, 6)) for (k, v) in d.items())
                    for d in param_list]]



with open("results/parameters.json", "w") as f:
    f.write(json.dumps(rounded_list, indent=2))

with open("results/parameters_read.json", "w") as f:
    f.write(json.dumps(rounded_list, indent=2))

print(rounded_list)


from utils.runners import run_tournament

# create results directory if it does not exist
if not os.path.exists("results"):
    os.mkdir("results")

# Settings to run a tournament:
#   We need to specify the classpath all agents that will participate in the tournament
#   We need to specify duos of preference profiles that will be played by the agents
#   We need to specify a deadline of amount of rounds we can negotiate before we end without agreement




agents = [
    ["agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
    ["agents.boulware_agent.boulware_agent.BoulwareAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
    ["agents.agent_bribery.agent_bribery.AgentBribery", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
    ["agents.conceder_agent.conceder_agent.ConcederAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
    ["agents.hardliner_agent.hardliner_agent.HardlinerAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
    ["agents.linear_agent.linear_agent.LinearAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
    ["agents.random_agent.random_agent.RandomAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
]

random_search_summaries = []

for i in range(0, n_iter):
    n_games = 0
    total_nash = 0
    total_welfare = 0
    ye_utility = 0
    opp_utility = 0

    best_game_nash = [0, None]
    worst_game_nash = [1000, None]

    best_game_welfare = [0, None]
    worst_game_welfare = [1000, None]

    best_game_util = [0, None]
    worst_game_util = [1000, None]

    for agent_duo in agents:
        tournament_settings = {
            "agents": agent_duo,
            "profile_sets": [
                ["domains/domain00/profileA.json", "domains/domain00/profileB.json"],
                ["domains/domain01/profileA.json", "domains/domain01/profileB.json"],
                ["domains/domain02/profileA.json", "domains/domain02/profileB.json"],
                ["domains/domain03/profileA.json", "domains/domain03/profileB.json"],
                ["domains/domain04/profileA.json", "domains/domain04/profileB.json"],
                ["domains/domain05/profileA.json", "domains/domain05/profileB.json"],
                ["domains/domain06/profileA.json", "domains/domain06/profileB.json"],
                ["domains/domain07/profileA.json", "domains/domain07/profileB.json"]

            ],
            "deadline_rounds": 200,
        }

        # run a session and obtain results in dictionaries
        tournament, results_summaries = run_tournament(tournament_settings)

        we_start = False

        for idx, game in enumerate(results_summaries):

            n_games += 1

            index_of_ye = 2 if we_start else 4
            index_of_opp = 4 if we_start else 2

            """
            ToDo: do average utility, best worst games, store averages of everything in a json file (i started making it below)
            """

            print("------ game util: ", game[list(game)[index_of_ye]], index_of_ye, game)

            total_nash += game["nash_product"]
            total_welfare += game["social_welfare"]
            ye_utility += game[list(game)[index_of_ye]] #list(game.values()).index('Ye')
            opp_utility +=  game[list(game)[index_of_opp]]

            if game["nash_product"] > best_game_nash[0]:
                best_game_nash[0] = game["nash_product"]
                best_game_nash[1] = game

            if game["nash_product"] < worst_game_nash[0]:
                worst_game_nash[0] = game["nash_product"]
                worst_game_nash[1] = game

            if game["social_welfare"] > best_game_welfare[0]:
                best_game_welfare[0] = game["social_welfare"]
                best_game_welfare[1] = game

            if game["social_welfare"] < worst_game_welfare[0]:
                worst_game_welfare[0] = game["social_welfare"]
                worst_game_welfare[1] = game

            if game[list(game)[index_of_ye]] > best_game_util[0]:
                best_game_util[0] = game[list(game)[index_of_ye]]
                best_game_util[1] = game

            if game[list(game)[index_of_ye]] < worst_game_util[0]:
                worst_game_util[0] = game[list(game)[index_of_ye]]
                worst_game_util[1] = game

            we_start = not we_start

    results = {
        "parameters": rounded_list[1][i],

        "welfare": {
            "total": total_welfare,
            "avg": total_welfare / n_games,
            "best_game": best_game_welfare,
            "worst_game": worst_game_welfare
        },
        "nash": {
            "total": total_nash,
            "avg": total_nash / n_games,
            "best_game": best_game_nash,
            "worst_game": worst_game_nash
        },
        "utility": {
            "total": ye_utility,
            "avg": ye_utility / n_games,
            "best_game": best_game_util,
            "worst_game": worst_game_util
        }
    }

    random_search_summaries.append(results)

    print(results)

    # print("+++++++++++++++++")
    # print("----------------------")
    # print("NUM OF GAMES: ", n_games)
    #
    # print("--WELFARE--")
    # print("TOTAL: ", total_welfare)
    # print("AVG: ", total_welfare/n_games)
    # print("BEST: ", best_game_welfare)
    # print("WORST: ", worst_game_welfare)
    #
    # print("--NASH PRODUCT--")
    # print("TOTAL: ", total_nash)
    # print("AVG: ", total_nash/n_games)
    # print("BEST: ", best_game_nash)
    # print("WORST: ", worst_game_nash)
    # print("----------------------")

# save the tournament settings for reference
with open("results/tournament.json", "w") as f:
    f.write(json.dumps(tournament, indent=2))
# save the result summaries
with open("results/results_summaries.json", "w") as f:
    f.write(json.dumps(results_summaries, indent=2))

with open("results/random_search_summaries.json", "w") as f:
    f.write(json.dumps(random_search_summaries, indent=2))