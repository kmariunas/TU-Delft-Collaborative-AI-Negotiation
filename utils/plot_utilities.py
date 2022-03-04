import os
from collections import defaultdict
import plotly.graph_objects as go

def plot_utils(results_trace: dict, my_agent: str, opponent: str, file_path: str):
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
        elif "Accept" in action:
            offer = action["Accept"]
            index -= 1
            for agent, util in offer["utilities"].items():
                accept["x"].append(index)
                accept["y"].append(util)
                accept["bids"].append(offer["bid"]["issuevalues"])


    fig = go.Figure()

    print(accept["y"][0])

    fig.add_trace(
        go.Scatter(
            mode="markers",
            x=[accept["y"][0]],
            y=[accept["y"][1]],
            name="agreement",
            marker={"color": "green", "size": 15},
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            mode="lines+markers",
            x=utilities[opponent][my_agent]["y"],
            y=utilities[my_agent][my_agent]["y"],
            marker={"color": "blue"},
        )
    )

    fig.add_trace(
        go.Scatter(
            mode="lines+markers",
            x=utilities[opponent][opponent]["y"],
            y=utilities[my_agent][opponent]["y"],
            marker={"color": "red"},
        )
    )

    fig.write_html(f"{os.path.splitext(file_path)[0]}.html")