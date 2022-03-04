import json
import os
from collections import defaultdict
from typing import List

from utils.plot_rmse import plot_rmse
from utils.plot_trace import plot_trace
from utils.plot_utilities import plot_utils
from utils.runners import run_session

# create results directory if it does not exist
if not os.path.exists("results"):
    os.mkdir("results")

# issueA, issueB, etc
actual_weights = {
      "issueA": 0.05298,
      "issueB": 0.14706,
      "issueC": 0.47093,
      "issueD": 0.20636,
      "issueE": 0.12267
    }

settings_opponent_name = "agents.boulware_agent.boulware_agent.BoulwareAgent"
opponent_name = "agents_boulware_agent_boulware_agent_BoulwareAgent_1"

# Settings to run a negotiation session:
#   We need to specify the classpath of 2 agents to start a negotiation.
#   We need to specify the preference profiles for both agents. The first profile will be assigned to the first agent.
#   We need to specify a deadline of amount of rounds we can negotiate before we end without agreement
settings = {
    "agents": [
        settings_opponent_name,
        "agents.Group34_NegotiationAssignment_Agent.Group34_NegotiationAssignment_Agent.Ye",
    ],
    # TODO: change actual utilities when you change domain
    "profiles": ["domains/domain00/profileA.json", "domains/domain00/profileB.json"],
    "deadline_rounds": 200,
}

# run a session and obtain results in dictionaries
results_trace, results_summary = run_session(settings)



#####
basepath = os.path.dirname(__file__)

utilities_file_name = os.path.abspath(os.path.join(basepath, "results/received-bids-utilities.json"))

weights_file_name = os.path.abspath(os.path.join(basepath, "results/opponent-weights.json"))

# read data
# predicted_utilities = None
# weights: List[Dict[str, float]] = None

# read utilities
predicted_utilities: List[float] = json.loads(json.load(open(utilities_file_name)))

# read weights
weights = json.loads(json.load(open(weights_file_name)))


# change format of predicted weights
predicted_weights = []

####
for i in range(0, len(weights)):
    predicted_weights.append([])
    for k in actual_weights.keys():
        predicted_weights[i].append(weights[i].get(k))


plot_rmse(predicted_weights, actual_weights, "results/plot-weights.html")
plot_utils(results_trace,
           "agents_Group34_NegotiationAssignment_Agent_Group34_NegotiationAssignment_Agent_Ye_2",
           opponent_name, "results/utils.html")

# actual_utilities = []
# for offer in results_trace.get("actions"):
#     if offer.get("actor") is opponent_name:
#         actual_utilities.append(offer.get("utilities").get(opponent_name))

utilities = defaultdict(lambda: defaultdict(lambda: {"x": [], "y": [], "bids": []}))
accept = {"x": [], "y": [], "bids": []}

for index, action in enumerate(results_trace["actions"], 1):
    if "Offer" in action:
        offer = action["Offer"]
        actor = offer["actor"]
        for agent, util in offer["utilities"].items():
            utilities[agent][actor]["x"].append(index)
            utilities[agent][actor]["y"].append(util)
            utilities[agent][actor]["bids"].append(offer["bid"]["issuevalues"])

plot_rmse(predicted_utilities, utilities[opponent_name][opponent_name]["y"], "results/utilities.html")
######

# plot trace to html file
plot_trace(results_trace, "results/trace_plot.html")

# write results to file
with open("results/results_trace.json", "w") as f:
    f.write(json.dumps(results_trace, indent=2))
with open("results/results_summary.json", "w") as f:
    f.write(json.dumps(results_summary, indent=2))
