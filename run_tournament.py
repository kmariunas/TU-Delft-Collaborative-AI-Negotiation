import json
import os

from utils.runners import run_tournament

# create results directory if it does not exist
if not os.path.exists("results"):
    os.mkdir("results")

# Settings to run a tournament:
#   We need to specify the classpath all agents that will participate in the tournament
#   We need to specify duos of preference profiles that will be played by the agents
#   We need to specify a deadline of amount of rounds we can negotiate before we end without agreement
n_games = 0
total_nash = 0
total_welfare = 0

best_game_nash = [0, None]
worst_game_nash = [1000, None]

best_game_welfare = [0, None]
worst_game_welfare = [1000, None]

best_game_util = [0, None]
worst_game_util = [1000, None]

agents = [
    ["agents.boulware_agent.boulware_agent.BoulwareAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
    ["agents.conceder_agent.conceder_agent.ConcederAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
    ["agents.hardliner_agent.hardliner_agent.HardlinerAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
    ["agents.linear_agent.linear_agent.LinearAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
    ["agents.random_agent.random_agent.RandomAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
]

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

        ],
        "deadline_rounds": 200,
    }

    # run a session and obtain results in dictionaries
    tournament, results_summaries = run_tournament(tournament_settings)

    for idx, game in enumerate(results_summaries):
        n_games += 1

        total_nash += game["nash_product"]
        total_welfare += game["social_welfare"]

        print(n_games, game["nash_product"], game["social_welfare"], total_welfare, total_nash)

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
    print("+++++++++++++++++")
print("----------------------")
print("NUM OF GAMES: ", n_games)

print("--WELFARE--")
print("TOTAL: ", total_welfare)
print("AVG: ", total_welfare/n_games)
print("BEST: ", best_game_welfare)
print("WORST: ", worst_game_welfare)

print("--NASH PRODUCT--")
print("TOTAL: ", total_nash)
print("AVG: ", total_nash/n_games)
print("BEST: ", best_game_nash)
print("WORST: ", worst_game_nash)
print("----------------------")


# save the tournament settings for reference
with open("results/tournament.json", "w") as f:
    f.write(json.dumps(tournament, indent=2))
# save the result summaries
with open("results/results_summaries.json", "w") as f:
    f.write(json.dumps(results_summaries, indent=2))








# import json
# import os
#
# from utils.runners import run_tournament
#
# # create results directory if it does not exist
# if not os.path.exists("results"):
#     os.mkdir("results")
#
# # Settings to run a tournament:
# #   We need to specify the classpath all agents that will participate in the tournament
# #   We need to specify duos of preference profiles that will be played by the agents
# #   We need to specify a deadline of amount of rounds we can negotiate before we end without agreement
#
# agents = [
#     ["agents.boulware_agent.boulware_agent.BoulwareAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
#     ["agents.conceder_agent.conceder_agent.ConcederAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
#     ["agents.hardliner_agent.hardliner_agent.HardlinerAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
#     ["agents.linear_agent.linear_agent.LinearAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
#     ["agents.random_agent.random_agent.RandomAgent", "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye"],
# ]
#
# tournament_settings = {
#     "agents": [
#         "agents.boulware_agent.boulware_agent.BoulwareAgent",
#         "agents.conceder_agent.conceder_agent.ConcederAgent",
#         "agents.hardliner_agent.hardliner_agent.HardlinerAgent",
#         "agents.linear_agent.linear_agent.LinearAgent",
#         "agents.random_agent.random_agent.RandomAgent",
#         "agents.stupid_agent.stupid_agent.StupidAgent",
#         "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye",
#     ],
#     "profile_sets": [
#         ["domains/domain00/profileA.json", "domains/domain00/profileB.json"],
#         ["domains/domain01/profileA.json", "domains/domain01/profileB.json"],
#     ],
#     "deadline_rounds": 200,
# }
#
# # run a session and obtain results in dictionaries
# tournament, results_summaries = run_tournament(tournament_settings)
#
#
# print(results_summaries)
#
# n_games = len(results_summaries)
# total_nash = 0
# total_welfare = 0
#
# best_game_nash = [0, None]
# worst_game_nash = [1000, None]
#
# best_game_welfare = [0, None]
# worst_game_welfare = [1000, None]
#
# best_game_util = [0, None]
# worst_game_util = [1000, None]
#
# for idx, game in enumerate(results_summaries):
#     total_nash += game["nash_product"]
#     total_welfare += game["social_welfare"]
#
#     if game["nash_product"] > best_game_nash[0]:
#         best_game_nash[0] = game["nash_product"]
#         best_game_nash[1] = game
#
#     if game["nash_product"] < worst_game_nash[0]:
#         worst_game_nash[0] = game["nash_product"]
#         worst_game_nash[1] = game
#
#     if game["social_welfare"] > best_game_welfare[0]:
#         best_game_welfare[0] = game["nash_product"]
#         best_game_welfare[1] = game
#
#     if game["social_welfare"] < worst_game_welfare[0]:
#         worst_game_welfare[0] = game["nash_product"]
#         worst_game_welfare[1] = game
# print("----------------------")
# print("NUM OF GAMES: ", n_games)
#
# print("--WELFARE--")
# print("TOTAL: ", total_welfare, "AVG: ", total_welfare/n_games)
# print("BEST: ", best_game_welfare)
# print("WORST: ", worst_game_welfare)
#
# print("--NASH PRODUCT--")
# print("TOTAL: ", total_nash)
# print("AVG: ", total_nash/n_games)
# print("BEST: ", best_game_nash)
# print("WORST: ", worst_game_nash)
# print("----------------------")
#
#
# # save the tournament settings for reference
# with open("results/tournament.json", "w") as f:
#     f.write(json.dumps(tournament, indent=2))
# # save the result summaries
# with open("results/results_summaries.json", "w") as f:
#     f.write(json.dumps(results_summaries, indent=2))
