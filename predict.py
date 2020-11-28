"""
This module fetches voting data, tries to make a projection and writes it to the filesystem
"""
import json
import os
import time
from datetime import datetime

import numpy as np
import pandas as pd
import requests

OLD_RESULT_PATH = "abstimmungen.csv"

HALBKANTONE = [
    "Obwalden",
    "Nidwalden",
    "Basel-Stadt",
    "Basel-Landschaft",
    "Appenzell Ausserrhoden",
    "Appenzell Innerrhoden",
]


def get_staende(kantone):
    """
    Return the amount stände that or over 50%
    """
    total = 0
    for kanton, data in kantone.iterrows():
        if data["JaInProzent"] > 50:
            if kanton in HALBKANTONE:
                total += 0.5
            else:
                total += 1
    return total


def calculate_projection(old_data):
    """
    Calculates the projection used to calculate the prediction
    """
    u, s, v = np.linalg.svd(old_data, full_matrices=False)
    s = np.diag(s)
    return np.dot(u, s)


def prediction(projection, values, indexes):
    """
    Predicts the result for the missing communities
    """
    observed_projection = projection[indexes]
    tmp = np.linalg.inv(
        (
            np.dot(observed_projection.T, observed_projection)
            + 0.01 * np.identity(projection.shape[1])
        )
    )
    tmp2 = np.dot(tmp, observed_projection.T)
    w = np.dot(tmp2, values[indexes])

    return np.dot(projection[~indexes], w)


def result_tuple(result):
    """
    Returns the tuple with the relevant info
    """
    return (
        result["jaStimmenInProzent"] or 0.0,
        result["stimmbeteiligungInProzent"] or 0.0,
        result["anzahlStimmberechtigte"] or 0,
        result["gebietAusgezaehlt"],
    )


def initial_dataframe(url, vote_index):
    """
    Fetches an initial dataset, and returns a dataframe
    """
    kantone = requests.get(url).json()["schweiz"]["vorlagen"][vote_index]["kantone"]
    gemeinden = []

    for kanton in kantone:
        kanton_name = kanton["geoLevelname"]
        for gemeinde in kanton["gemeinden"]:
            r = gemeinde["resultat"]
            gemeinden.append((kanton_name, gemeinde["geoLevelname"], *result_tuple(r)))

    data_frame = pd.DataFrame(
        gemeinden,
        columns=[
            "Kanton",
            "Gemeinde",
            "JaInProzent",
            "StimmbetProzent",
            "Stimmberechtigte",
            "Ausgezaehlt",
        ],
    ).set_index("Gemeinde")

    return data_frame


def predict_results(data_frame, proj_yes, proj_part):
    data_frame.loc[df["Ausgezaehlt"] == False, "JaInProzent"] = prediction(
        proj_yes, data_frame["JaInProzent"], data_frame["Ausgezaehlt"]
    )
    data_frame.loc[data_frame["Ausgezaehlt"] == False, "StimmbetProzent"] = prediction(
        proj_part, data_frame["StimmbetProzent"], data_frame["Ausgezaehlt"]
    )

    data_frame["JaTotal"] = (
        (data_frame["JaInProzent"] / 100)
        * (data_frame["StimmbetProzent"] / 100)
        * data_frame["Stimmberechtigte"]
    )
    data_frame["NeinTotal"] = (
        (1 - data_frame["JaInProzent"] / 100)
        * (data_frame["StimmbetProzent"] / 100)
        * data_frame["Stimmberechtigte"]
    )


def calculate_kantone(df):
    kanton_results = df.groupby("Kanton")[["JaTotal", "NeinTotal"]].sum()
    kanton_results["JaInProzent"] = (
        kanton_results["JaTotal"]
        / (kanton_results["JaTotal"] + kanton_results["NeinTotal"])
        * 100
    )

    return kanton_results


def update_results(df, url):
    new_results = requests.get(url).json()
    kantone = new_results["schweiz"]["vorlagen"][0]["kantone"]

    for kanton in kantone:
        for gemeinde in kanton["gemeinden"]:
            name = gemeinde["geoLevelname"]
            r = gemeinde["resultat"]
            if r["gebietAusgezaehlt"]:
                df.at[
                    name,
                    [
                        "JaInProzent",
                        "StimmbetProzent",
                        "Stimmberechtigte",
                        "Ausgezaehlt",
                    ],
                ] = result_tuple(r)


if __name__ == "__main__":
    print(f"Loading old results from {OLD_RESULT_PATH}")

    results = pd.read_csv(OLD_RESULT_PATH, na_values=["..."]).rename(
        columns={"Kanton (-) / Bezirk (>>) / Gemeinde (......)": "Gemeinde"}
    )
    results["Gemeinde"] = (
        results["Gemeinde"]
        .str.replace(r"\.\.\.\.\.\.", "")
        .replace(
            "Brione (Verzasca)",
            "Verzasca",
        )
        .replace("La Punt-Chamues-ch", "La Punt Chamues-ch")
    )

    yes_pivot = results.pivot(
        index="Gemeinde", columns="Datum und Vorlage", values="Ja in %"
    ).reset_index()
    yes_pivot.columns.name = None
    yes_pivot.set_index("Gemeinde", inplace=True)

    part_pivot = results.pivot(
        index="Gemeinde", columns="Datum und Vorlage", values="Beteiligung in %"
    ).reset_index()
    part_pivot.columns.name = None
    part_pivot.set_index("Gemeinde", inplace=True)

    people = results.pivot(
        index="Gemeinde", columns="Datum und Vorlage", values="Stimmberechtigte"
    ).reset_index()
    people.columns.name = None
    people.set_index("Gemeinde", inplace=True)

    print("Preparing result table")

    url = os.environ["VOTATION_URL"]
    vote_index = int(os.environ["VOTATION_INDEX"])

    os.makedirs(f"www/gemeinden/{vote_index}/", exist_ok=True)
    os.makedirs(f"www/kantone/{vote_index}/", exist_ok=True)
    os.makedirs(f"www/schweiz/{vote_index}/", exist_ok=True)

    df = initial_dataframe(url, vote_index)

    indexes = df.drop(
        [
            "Kanton",
            "JaInProzent",
            "StimmbetProzent",
            "Stimmberechtigte",
            "Ausgezaehlt",
        ],
        axis=1,
    )

    yes_table = indexes.join(yes_pivot)
    part_table = indexes.join(part_pivot)
    people_table = indexes.join(people)

    df["Stimmberechtigte"] = people_table[
        "2020-09-27 Volksinitiative «Für eine massvolle Zuwanderung (Begrenzungsinitiative)»"
    ]

    print("Calculating matrices")

    yes_matrix = yes_table.fillna(yes_table.mean()).to_numpy()
    part_matrix = part_table.fillna(yes_table.mean()).to_numpy()

    proj_yes = calculate_projection(yes_matrix)
    proj_part = calculate_projection(part_matrix)

    print("Starting fetch loop")

    while True:
        update_results(df, url)
        predict_results(df, proj_yes, proj_part)
        kantone = calculate_kantone(df)

        df.reset_index().to_json(
            f"www/gemeinden/{vote_index}/latest.json", orient="records"
        )
        kantone.reset_index().to_json(
            f"www/kantone/{vote_index}/latest.json", orient="records"
        )

        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        kantone_ja = get_staende(kantone)

        ja_total = kantone["JaTotal"].sum()
        ja_prozent = 0

        if (kantone["JaTotal"] + kantone["NeinTotal"]).sum() > 0:
            ja_prozent = (
                ja_total / (kantone["JaTotal"] + kantone["NeinTotal"]).sum()
            ) * 100

        schweiz = {
            "kantone": kantone_ja,
            "ja_total": ja_total,
            "ja_prozent": ja_prozent,
        }

        json.dump([schweiz], open(f"www/schweiz/{vote_index}/latest.json", "w"))

        df.reset_index().to_json(
            f"www/gemeinden/{vote_index}/{timestamp}.json", orient="records"
        )

        time.sleep(20)
