import os

import numpy as np
import plotly.graph_objects as go


def rmse(predicted_values, actual_values):
    return np.sqrt(np.sum(np.square(np.array(predicted_values) - np.array(actual_values))))

def plot_rmse(predicted_values, actual_values, file_path):
    fig = go.Figure()

    rounds = [].extend(range(1, len(predicted_values)))

    if isinstance(actual_values, dict): # we are working with weights -- actual_values len is issue_n and actual values len is number of rounds
        round_rmse = []

        actual_value_list = list(actual_values.values())

        for weights in predicted_values:
            round_rmse.append(rmse(weights, actual_value_list))

        text = []

        for idx, weights in enumerate(predicted_values):
            print(weights)
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
                x=rounds,
                hovertext = text,
                hoverinfo = "text",
            )
        )
    else:

        text = []

        # round_rmse = rmse(predicted_values, actual_values)

        for idx, (predicted_util, actual_util) in enumerate(zip(predicted_values, actual_values)):
            # print(round_rmse, idx)
            text.append(
                "<br>".join(
                    # [f"<b>RMSE: {round_rmse[idx]:.3f}</b><br>"]+
                    [f"Predicted Utility: {predicted_util}", f"Actual Util: {actual_util}"]
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
            )
        )

    basepath = os.path.dirname(__file__)

    filename = os.path.abspath(os.path.join(basepath, "..",  file_path))

    fig.write_html(filename)

plot_rmse([[3, 2], [5, 2]], {"aaa": 2, "bbb": 3}, "results/util_plot.html", )