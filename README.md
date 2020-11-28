# Voting-Predictions

Application to calculate the final result of a votation based on partial results.

This uses (or at least tries to use) the method described in [Sub-Matrix Factorization for Real-Time Vote Prediction](https://infoscience.epfl.ch/record/278872) by Immer, Alexander; Kristof, Victor; Grossglauser, Matthias; Thiran, Patrick.

Results are fetched from [Opendata.Swiss](https://opendata.swiss/en/dataset/echtzeitdaten-am-abstimmungstag-zu-eidgenoessischen-abstimmungsvorlagen/resource/25b805a2-98a8-418f-b367-0c98cd382fee), provided by the [Federal Statistical Office FSO](https://opendata.swiss/en/organization/bundesamt-fur-statistik-bfs).

## Structure

The Python code in `predict.py` fetches the results and predicts the outcome of the missing municipalities. These results are written into the `www/` directory, where they can be served through nginx. The `index.html` in there includes tables to load the newest predictions.

The `predict.py` is controlled through environment varibles `VOTATION_URL` and `VOTATION_INDEX`, they refer to the url of the json file and the index of the votation of interest in this json file.

Running it locally could look like this:
```bash
export VOTATION_URL=https://app-prod-static-voteinfo.s3.eu-central-1.amazonaws.com/v1/ogd/sd-t-17-02-20201129-eidgAbstimmung.json
export VOTATION_INDEX=0
python predict.py
```

And in another terminal:
```bash
python -m "http.server" -d www
```
And then navigate to http://localhost:8000
