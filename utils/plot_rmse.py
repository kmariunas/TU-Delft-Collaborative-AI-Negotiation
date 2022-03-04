import os

import numpy as np
import plotly.graph_objects as go


def rmse(predicted_values, actual_values):
    return np.sqrt(np.sum(np.square(np.array(predicted_values) - np.array(actual_values))))

def plot_rmse(predicted_values, actual_values, file_path):
    fig = go.Figure()

    rounds = []
    rounds.extend(range(1, len(predicted_values)))

    yname = ""
    yrange = 1.05

    if isinstance(actual_values, dict): # we are working with weights -- actual_values len is issue_n and actual values len is number of rounds
        round_rmse = []

        actual_value_list = list(actual_values.values())

        for weights in predicted_values:
            round_rmse.append(rmse(weights, actual_value_list))

        text = []

        for idx, weights in enumerate(predicted_values):
            text.append(
                "<br>".join(
                    [f"<b>RMSE: {round_rmse[idx]:.3f}</b><br>"]
                    + [f"Predicted {issue}: {weights[i]} | {issue}: {value}" for i, (issue, value) in enumerate(actual_values.items())]
                )
            )

        fig.add_trace(
            go.Scatter(
                mode="lines+markers",
                name="Weight RMSE",
                y=round_rmse,
                x=np.array(rounds) * 2,
                hovertext = text,
                hoverinfo = "text",
            )
        )
    else:

        text = []

        # round_rmse = rmse(predicted_values, actual_values)
        if len(predicted_values) != len(actual_values):
            print(actual_values)
            print(predicted_values)
            raise Exception("list values are not equal")

        for idx, predicted_util in enumerate(predicted_values):
            text.append(
                "<br>".join(
                    [f"<b>Utility:</b><br>"]+
                    [f"Predicted Utility: {predicted_util}", f"Actual Util: {actual_values[idx - 1]}"]
                )
            )

        fig.add_trace(
            go.Scatter(
                mode="lines+markers",
                name="Predicted Utility",
                x=rounds,
                y=predicted_values,
                hovertext=text,
                hoverinfo="text",
                marker={"color": "red"}
            )
        )

        fig.add_trace(
            go.Scatter(
                mode="lines+markers",
                name="Actual Utility",
                x=rounds,
                y=actual_values,
                hovertext=text,
                hoverinfo="text",
                marker={"color": "blue"}
            )
        )

    fig.update_layout(
        # width=1000,
        height=800,
        legend={
            "yanchor": "bottom",
            "y": 1,
            "xanchor": "left",
            "x": 0,
        },
    )

    fig.update_xaxes(title_text="round") #, range=[0, len(predicted_values) + 1], ticks="outside")
    fig.update_yaxes(title_text=yname, range=[0, yrange], ticks="outside")

    basepath = os.path.dirname(__file__)

    filename = os.path.abspath(os.path.join(basepath, "..",  file_path))

    fig.write_html(filename)