# Lab 9 — From model to data product

## Step 2 — Shared feature contract

Training and the API import the same `make_features` function, so they use the same transformations and the same feature-column names and order. If the API had a separate copy, even a small difference such as a rainfall unit conversion or different category spelling could make inference inputs inconsistent with training.

## Step 3–4 — Training and model metadata

Training completed on 801 rows and saved `models/model.joblib` and `models/model_metadata.json`. The recorded training R-squared is 1.0, but that score is not evidence of useful predictive power here: the source Parquet has a constant price of 500 for every row.

To answer “which data was this model trained on?”, use `training_data_path` and `training_data_sha256` (the hash identifies the exact file contents). To identify the serving model, use `model_version` and `model_type` in the metadata and the `/health` response.

The provided feature contract lists markets such as `Owino` and `Mbale Central`, but the actual training file contains lowercase `bwais`, `kansanga`, `mukono`, and `nakasero`. I kept the feature lists as given in the assignment; consequently, those training rows have zeroes for all the listed market indicator columns. This data/contract mismatch should be resolved before treating this model as a useful price predictor.

## Step 5–7 — API validation and health

`/health` reports `status`, `model_version`, `model_type`, and whether the serving feature code matches the code used at training. `/predict` validates the request, applies the shared feature function, and returns a rounded price and model version.

Live responses from the Uvicorn run:

| Request | Status | Message |
|---|---:|---|
| `rainfall_mm = -5` | 422 | `rainfall_mm`: input should be greater than or equal to 0 |
| `market = "Narnia"` | 422 | `market`: input must be one of the six listed markets |
| `date = "not-a-date"` | 422 | `date`: input should be a valid date or datetime |

A 422 clearly identifies a client input problem. A 500 would incorrectly suggest a server failure, while silently predicting from invalid input could produce a misleading result.

## Step 8 — Training/serving skew experiment

I changed the inference rainfall feature to divide by 1000, restarted Uvicorn without retraining, and sent the same valid request. The service did not crash. `/health` reported `status: degraded` and `feature_code_matches: false`, while the prediction remained **500.0**.

The unchanged prediction is explained by this dataset's constant 500 price: the trained regression predicts 500 regardless of its input features. With a non-constant target, a feature transformation change could change predictions without crashing. The `feature_code_sha256` metadata field lets the service detect that the feature implementation no longer matches the training version. I then restored the original feature code.

## Step 9 — Contract client

`src/api/test_client.py` calls `/health`, a valid `/predict`, and an invalid `/predict`. The invalid request demonstrates the API's 422 validation response.

## Step 10–11 — Container and reproducibility

`requirements.txt` pins the environment versions, and the root `Dockerfile` and `.dockerignore` are in place. Docker Desktop's CLI is installed, but its Linux engine was unavailable during this run, so I used the assignment's Uvicorn fallback rather than building or running the container.

The valid request returned `{"predicted_price": 500.0, "model_version": "20261101-141205"}` before restart and returned the identical output after stopping and restarting Uvicorn. The model file and metadata were unchanged between calls.

The scikit-learn version should match between training and serving because serialized estimators may depend on library internals and are not guaranteed to load or behave consistently across versions. The image excludes `data/` because inference only needs the saved model and metadata, not the training dataset; this also keeps the image smaller and avoids bundling unnecessary source data.

## Step 12 — Reflection

1. Preprocessing at inference happens in the `/predict` route, when it builds a one-row DataFrame and calls `make_features` before prediction.
2. A shared feature function prevents the ordinary case of training and serving implementing preprocessing differently. Step 8 showed that changing that shared code after training can still create skew; the feature-code hash detected the mismatch.
3. `/health` should show the service is responding and identify the loaded model. This implementation also reports whether the loaded feature implementation matches the training metadata.
4. A model version should be accompanied by its model type, feature names/order, training-data path and content hash, training-row count, training score, and feature-code hash. Together these help identify, reproduce, and diagnose a model.
5. Batch inference is a better fit for scheduled market summaries, large sets of prices that can be processed together, and use cases that do not need an immediate per-request response. It avoids keeping an API service running when periodic results are sufficient.
