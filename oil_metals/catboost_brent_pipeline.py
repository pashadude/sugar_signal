import os
import pandas as pd
import numpy as np
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Paths
DATA_PATH = "ShinkaEvolve/examples/oil_metals/data/price data/Features.xlsx"
OUTPUT_DIR = "ShinkaEvolve/examples/oil_metals"
MODEL_PATH = os.path.join(OUTPUT_DIR, "catboost_brent_model.cbm")
PRED_PATH = os.path.join(OUTPUT_DIR, "catboost_brent_predictions.csv")

# Load all sheets
sheet_names = ['Brent', 'SAUDI_ENERG', 'GOLD_Future', 'Natural Gas Future', 'Sentiment', 'USD']
dfs = {sheet: pd.read_excel(DATA_PATH, sheet_name=sheet) for sheet in sheet_names}
# Set 'Date' as index for each sheet, then reset to keep 'Date' as a column for merging
for sheet, df in dfs.items():
    if 'Date' in df.columns:
        df.set_index('Date', inplace=True)
        df.reset_index(inplace=True)
    dfs[sheet] = df

# Clean column names (remove leading/trailing spaces)
for k, df in dfs.items():
    df.columns = [c.strip() for c in df.columns]

# Merge all sheets on 'Date'
# Find the sheet with the largest date range (most unique dates)
date_counts = {sheet: df['Date'].nunique() for sheet, df in dfs.items() if 'Date' in df.columns}
main_sheet = max(date_counts, key=date_counts.get)
main_dates = pd.DataFrame({'Date': dfs[main_sheet]['Date'].unique()})
main_dates['Date'] = pd.to_datetime(main_dates['Date'])
main_dates = main_dates.sort_values('Date').reset_index(drop=True)

# Start merged with all unique dates from the main sheet
merged = main_dates.copy()

# Merge all sheets on 'Date', aligning to the main date range
for sheet, df in dfs.items():
    if 'Date' not in df.columns:
        continue
    df = df.loc[:, ~df.columns.duplicated()]
    # Remove 'Close' from non-Brent sheets to avoid collision
    cols = [c for c in df.columns if c != 'Close' or sheet == 'Brent']
    # To avoid column name collisions, add sheet prefix to all columns except 'Date'
    cols_prefixed = ['Date'] + [f"{sheet}_{c}" for c in cols if c != 'Date']
    df_prefixed = df[cols].copy()
    df_prefixed.columns = cols_prefixed
    merged = pd.merge(merged, df_prefixed, on='Date', how='left')
# For Brent, rename 'Close' to 'Brent_Close' after merge
if 'Brent_Close' not in merged.columns and 'Brent_Close' in dfs['Brent'].columns:
    pass  # already handled
elif 'Brent_Close' not in merged.columns and 'Brent' in dfs and 'Close' in dfs['Brent'].columns:
    merged = pd.merge(merged, dfs['Brent'][['Date', 'Close']].rename(columns={'Close': 'Brent_Close'}), on='Date', how='left')

# --- Add SMA features for Brent price ---
# Compute SMA_3, SMA_6, SMA_12 for Brent_Close
for win in [3, 6, 12]:
    merged[f'SMA_{win}'] = merged['Brent_Close'].rolling(window=win, min_periods=1).mean()
print("Added SMA features: SMA_3, SMA_6, SMA_12 for Brent_Close")

# Drop rows where Brent_Close is missing (target must be present)
merged = merged.dropna(subset=['Brent_Close'])

# --- Forward fill all columns to handle missing values ---
merged = merged.ffill()
merged = merged.bfill()  # Also backfill to handle leading NaNs from rolling/SMA

print(f"Merged dataset shape after ffill/bfill: {merged.shape} (rows, columns)")
# Feature selection: use all features except 'Brent_Close'
# Convert 'Date' to numeric (ordinal) and use as a feature
merged['Date_numeric'] = pd.to_datetime(merged['Date']).map(pd.Timestamp.toordinal)
# Ensure 'Date_numeric' is only included once
# Add SMA features to feature columns
feature_cols = [c for c in merged.columns if c not in ['Date', 'Brent_Close', 'Date_numeric']]
feature_cols += ['SMA_3', 'SMA_6', 'SMA_12']
feature_cols.append('Date_numeric')

# Handle missing values: fill with median for numeric, mode for categorical
import re

def parse_numeric(val):
    """Convert strings like '334.72K' to float, else np.nan if not convertible."""
    if isinstance(val, str):
        val = val.strip()
        if val == "":
            return np.nan
        # Handle K/M/B suffixes
        match = re.match(r"^([0-9\.\-eE]+)\s*([KMB]?)$", val)
        if match:
            num, suffix = match.groups()
            try:
                num = float(num)
                if suffix == "K":
                    num *= 1e3
                elif suffix == "M":
                    num *= 1e6
                elif suffix == "B":
                    num *= 1e9
                return num
            except Exception:
                return np.nan
        # Try direct conversion
        try:
            return float(val)
        except Exception:
            return np.nan
    return val

for col in feature_cols:
    if merged[col].dtype == 'object':
        # Try to convert to numeric if possible
        merged[col] = merged[col].apply(parse_numeric)
        # If still object, fill with mode; else fill with median
        if merged[col].dtype == 'object':
            merged[col] = merged[col].fillna(merged[col].mode()[0] if not merged[col].mode().empty else "")
        else:
            merged[col] = merged[col].fillna(merged[col].median())
    else:
        merged[col] = merged[col].fillna(merged[col].median())

# Identify categorical features (object dtype)
cat_features = [i for i, c in enumerate(feature_cols) if merged[c].dtype == 'object']

# Prepare X, y
# Remove any duplicate columns from X before fitting
X = merged[feature_cols]
X = X.loc[:, ~X.columns.duplicated()]
y = merged['Brent_Close']

# --- Ensure all arrays used for DataFrame construction are of the same length ---
assert len(X) == len(y), f"Feature and target arrays have mismatched lengths after ffill: {len(X)} vs {len(y)}"

# Optionally scale features (CatBoost handles scaling internally, so skip unless needed)
# from sklearn.preprocessing import StandardScaler
# scaler = StandardScaler()
# X = pd.DataFrame(scaler.fit_transform(X), columns=feature_cols)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Systematic search over feature sets, engineering strategies, and CatBoost hyperparameters
from itertools import product
import random

# Define search space
feature_sets = {
    "original": feature_cols,
    "reduced": None,  # will be set after importance
    "engineered": None  # will be set after engineering
}
engineering_strategies = [
    "none",
    "interaction",
    "log",
    "interaction_log"
]
hyperparams_grid = {
    "depth": [4, 6, 8],
    "learning_rate": [0.01, 0.05, 0.1],
    "iterations": [500, 1000, 1500],
    "l2_leaf_reg": [1, 3, 5]
}

results = []
best_metrics = {"rmse": float("inf"), "mae": float("inf"), "r2": -float("inf")}
best_config = None
best_model = None
best_X_test = None
best_y_test = None
best_y_pred = None

# Feature importance for reduced set
importances = None
importance_df = None
feature_cols_reduced = None
cat_features_reduced = None

# Initial model for importance
model_imp = CatBoostRegressor(
    iterations=500,
    learning_rate=0.05,
    depth=6,
    loss_function='RMSE',
    cat_features=cat_features,
    verbose=0
)
model_imp.fit(X, y)
importances = model_imp.get_feature_importance()
# Ensure importances and feature_cols are the same length
if len(importances) != len(feature_cols):
    print("DEBUG: Length mismatch in feature importance calculation!")
    print(f"len(importances): {len(importances)}, len(feature_cols): {len(feature_cols)}")
    # Truncate to shortest length
    min_len = min(len(importances), len(feature_cols))
    importances = importances[:min_len]
    feature_cols = feature_cols[:min_len]
importance_df = pd.DataFrame({
    'feature': feature_cols,
    'importance': importances
})
max_importance = importance_df['importance'].max()
threshold = 0.01 * max_importance
low_imp_features = importance_df[importance_df['importance'] < threshold]['feature'].tolist()
feature_cols_reduced = [f for f in feature_cols if f not in low_imp_features]
cat_features_reduced = [i for i, c in enumerate(feature_cols_reduced) if merged[c].dtype == 'object']
feature_sets["reduced"] = feature_cols_reduced

# Engineered features
def engineer_features(df, base_cols, strategy):
    df_new = df.copy()
    cols = base_cols.copy()
    top_features = importance_df.sort_values('importance', ascending=False)['feature'].tolist()
    numeric_top = None
    for f in top_features:
        if np.issubdtype(df_new[f].dtype, np.number):
            numeric_top = f
            break
    if strategy in ["interaction", "interaction_log"] and len(top_features) >= 2:
        f1, f2 = top_features[0], top_features[1]
        df_new['interaction_term'] = df_new[f1] * df_new[f2]
        cols.append('interaction_term')
    if strategy in ["log", "interaction_log"] and numeric_top:
        # Suppress RuntimeWarning and handle invalid values for log1p
        vals = df_new[numeric_top].copy()
        vals = vals.replace({-np.inf: np.nan})
        vals = vals.where(vals >= 0)  # set negative values to NaN
        vals = vals.fillna(0)
        with np.errstate(invalid='ignore'):
            df_new['log_' + numeric_top] = np.log1p(vals)
        cols.append('log_' + numeric_top)
    return df_new, cols

# Prepare engineered feature set
X_eng, feature_cols_eng = engineer_features(merged, feature_cols_reduced, "interaction_log")
# Fix: Use X_eng for dtype lookup, not merged
cat_features_eng = [i for i, c in enumerate(feature_cols_eng) if X_eng[c].dtype == 'object']
feature_sets["engineered"] = feature_cols_eng

# Search loop
search_space = list(product(
    feature_sets.keys(),
    engineering_strategies,
    hyperparams_grid["depth"],
    hyperparams_grid["learning_rate"],
    hyperparams_grid["iterations"],
    hyperparams_grid["l2_leaf_reg"]
))

from joblib import Parallel, delayed

def train_catboost_model(fs_key, eng_strat, depth, lr, iters, l2):
    # Feature selection
    if fs_key == "original":
        base_cols = feature_sets["original"]
        cat_feats = [i for i, c in enumerate(base_cols) if merged[c].dtype == 'object']
        X_exp = merged[base_cols]
        X_exp = X_exp.loc[:, ~X_exp.columns.duplicated()]
    elif fs_key == "reduced":
        base_cols = feature_sets["reduced"]
        cat_feats = cat_features_reduced
        X_exp = merged[base_cols]
        X_exp = X_exp.loc[:, ~X_exp.columns.duplicated()]
    else:  # engineered
        base_cols = feature_sets["engineered"]
        cat_feats = cat_features_eng
        X_exp, _ = engineer_features(merged, feature_cols_reduced, eng_strat)
        X_exp = X_exp.loc[:, ~X_exp.columns.duplicated()]

    # Train/test split
    X_train_exp, X_test_exp, y_train_exp, y_test_exp = train_test_split(X_exp, y, test_size=0.2, random_state=42)

    # Model
    model_exp = CatBoostRegressor(
        iterations=iters,
        learning_rate=lr,
        depth=depth,
        l2_leaf_reg=l2,
        loss_function='RMSE',
        cat_features=cat_feats,
        verbose=0
    )
    model_exp.fit(X_train_exp, y_train_exp, eval_set=(X_test_exp, y_test_exp), use_best_model=True)
    y_pred_exp = model_exp.predict(X_test_exp)

    # Metrics
    rmse_exp = np.sqrt(mean_squared_error(y_test_exp, y_pred_exp))
    mae_exp = mean_absolute_error(y_test_exp, y_pred_exp)
    r2_exp = r2_score(y_test_exp, y_pred_exp)

    return {
        "feature_set": fs_key,
        "engineering": eng_strat,
        "depth": depth,
        "learning_rate": lr,
        "iterations": iters,
        "l2_leaf_reg": l2,
        "rmse": rmse_exp,
        "mae": mae_exp,
        "r2": r2_exp,
        "model": model_exp,
        "X_test": X_test_exp,
        "y_test": y_test_exp,
        "y_pred": y_pred_exp
    }

# Only parallelize the CatBoost model training, not feature engineering
parallel_results = Parallel(n_jobs=-1, backend="loky")(
    delayed(train_catboost_model)(fs_key, eng_strat, depth, lr, iters, l2)
    for fs_key, eng_strat, depth, lr, iters, l2 in search_space
)

results = []
best_metrics = {"rmse": float("inf"), "mae": float("inf"), "r2": -float("inf")}
best_config = None
best_model = None
best_X_test = None
best_y_test = None
best_y_pred = None

for res in parallel_results:
    results.append({
        "feature_set": res["feature_set"],
        "engineering": res["engineering"],
        "depth": res["depth"],
        "learning_rate": res["learning_rate"],
        "iterations": res["iterations"],
        "l2_leaf_reg": res["l2_leaf_reg"],
        "rmse": res["rmse"],
        "mae": res["mae"],
        "r2": res["r2"]
    })
    # Track best
    if (res["rmse"] < best_metrics["rmse"]) or \
       (res["rmse"] == best_metrics["rmse"] and res["r2"] > best_metrics["r2"]):
        best_metrics = {"rmse": res["rmse"], "mae": res["mae"], "r2": res["r2"]}
        best_config = {
            "feature_set": res["feature_set"],
            "engineering": res["engineering"],
            "depth": res["depth"],
            "learning_rate": res["learning_rate"],
            "iterations": res["iterations"],
            "l2_leaf_reg": res["l2_leaf_reg"]
        }
        best_model = res["model"]
        best_X_test = res["X_test"]
        best_y_test = res["y_test"]
        best_y_pred = res["y_pred"]

print(f"Best config: {best_config}")
print(f"Best RMSE: {best_metrics['rmse']:.4f}, MAE: {best_metrics['mae']:.4f}, R2: {best_metrics['r2']:.4f}")

# Save all results
results_df = pd.DataFrame(results)
results_df.to_csv(os.path.join(OUTPUT_DIR, "catboost_brent_search_results.csv"), index=False)

# Save best model
best_model.save_model(MODEL_PATH)
# Save best predictions
# Ensure all arrays for prediction DataFrame are of the same length
assert len(best_X_test) == len(best_y_test) == len(best_y_pred), (
    f"Prediction arrays have mismatched lengths: {len(best_X_test)}, {len(best_y_test)}, {len(best_y_pred)}"
)
# Ensure all arrays for prediction DataFrame are of the same length and aligned
min_len = min(len(best_X_test), len(best_y_test), len(best_y_pred))
best_X_test_aligned = best_X_test.iloc[:min_len]
best_y_test_aligned = best_y_test.iloc[:min_len]
best_y_pred_aligned = best_y_pred[:min_len] if hasattr(best_y_pred, '__len__') else np.array([best_y_pred]*min_len)

pred_df_best = pd.DataFrame({
    'Date': best_X_test_aligned.index if 'Date' not in best_X_test_aligned.columns else best_X_test_aligned['Date'],
    'Brent_Close_True': best_y_test_aligned,
    'Brent_Close_Pred': best_y_pred_aligned
})
pred_df_best.to_csv(PRED_PATH, index=False)
# Save best metrics
with open(os.path.join(OUTPUT_DIR, "catboost_brent_metrics.txt"), "w") as f:
    f.write(f"Best config: {best_config}\n")
    f.write(f"RMSE: {best_metrics['rmse']:.4f}\nMAE: {best_metrics['mae']:.4f}\nR2: {best_metrics['r2']:.4f}\n")

print(f"Systematic search complete. Best config and metrics saved.")

# --- SHAP feature importance for best model ---
import shap
import matplotlib.pyplot as plt

def save_shap_summary(model, X, feature_names, out_path):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X, feature_names=feature_names, show=False)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

shap_out_path = os.path.join(OUTPUT_DIR, "catboost_brent_shap_summary.png")
# Use the best model and its test set
save_shap_summary(best_model, best_X_test, best_X_test.columns, shap_out_path)
print(f"SHAP summary plot saved to {shap_out_path}")

# Save feature list used in best model
with open(os.path.join(OUTPUT_DIR, "catboost_brent_best_features.txt"), "w") as f:
    f.write("CatBoost Brent Best Model Features\n")
    f.write("="*33 + "\n\n")
    f.write(f"Best config: {best_config}\n\n")
    f.write("Feature List:\n")
    for feat in best_X_test.columns:
        f.write(f"- {feat}\n")

# --- Model selection and summary ---
# Remove legacy metrics block (now handled by search loop)
# metrics = {
#     'original': {'rmse': rmse, 'mae': mae, 'r2': r2, 'model': model, 'X_test': X_test, 'y_test': y_test, 'y_pred': y_pred},
#     'feature_selection': {'rmse': rmse_r, 'mae': mae_r, 'r2': r2_r, 'model': model_r, 'X_test': X_test_r, 'y_test': y_test_r, 'y_pred': y_pred_r},
#     'feature_engineering': {'rmse': rmse_e, 'mae': mae_e, 'r2': r2_e, 'model': model_e, 'X_test': X_test_e, 'y_test': y_test_e, 'y_pred': y_pred_e}
# }
# best_key = min(metrics, key=lambda k: metrics[k]['rmse'])
# best = metrics[best_key]

# Legacy model comparison and summary block removed; handled by search loop above.
# --- Feature engineering: add interaction and transformed features ---
# Use importance_df from previous block (already contains reduced features)
top_features = importance_df.sort_values('importance', ascending=False)['feature'].tolist()
if len(top_features) >= 2:
    f1, f2 = top_features[0], top_features[1]
    merged['interaction_term'] = merged[f1] * merged[f2]
    print(f"Added interaction term: {f1} * {f2}")
else:
    print("Not enough features for interaction term.")

# Add log transformation for most important numeric feature
numeric_top = None
for f in top_features:
    if np.issubdtype(merged[f].dtype, np.number):
        numeric_top = f
        break
if numeric_top:
    # Suppress RuntimeWarning and handle invalid values for log1p
    vals = merged[numeric_top].copy()
    vals = vals.replace({-np.inf: np.nan})
    vals = vals.where(vals >= 0)  # set negative values to NaN
    vals = vals.fillna(0)
    with np.errstate(invalid='ignore'):
        merged['log_' + numeric_top] = np.log1p(vals)
    print(f"Added log transformation: log1p({numeric_top})")
else:
    print("No numeric feature found for log transformation.")

# Update feature columns
feature_cols_eng = feature_cols_reduced.copy()
# Ensure SMA features are included in engineered feature set
for sma in ['SMA_3', 'SMA_6', 'SMA_12']:
    if sma not in feature_cols_eng:
        feature_cols_eng.append(sma)
if len(top_features) >= 2:
    feature_cols_eng.append('interaction_term')
if numeric_top:
    feature_cols_eng.append('log_' + numeric_top)
cat_features_eng = [i for i, c in enumerate(feature_cols_eng) if merged[c].dtype == 'object']

X_eng = merged[feature_cols_eng]
# Ensure all arrays for engineered features are of the same length
assert len(X_eng) == len(y), f"Engineered feature and target arrays have mismatched lengths: {len(X_eng)} vs {len(y)}"
X_train_e, X_test_e, y_train_e, y_test_e = train_test_split(X_eng, y, test_size=0.2, random_state=42)

model_e = CatBoostRegressor(
    iterations=1000,
    learning_rate=0.05,
    depth=6,
    loss_function='RMSE',
    cat_features=cat_features_eng,
    verbose=100
)
model_e.fit(X_train_e, y_train_e, eval_set=(X_test_e, y_test_e), use_best_model=True)
y_pred_e = model_e.predict(X_test_e)

rmse_e = np.sqrt(mean_squared_error(y_test_e, y_pred_e))
mae_e = mean_absolute_error(y_test_e, y_pred_e)
r2_e = r2_score(y_test_e, y_pred_e)

print("After feature engineering:")
# (Legacy/duplicate code block removed: all outputs are already saved above using the best model/config)