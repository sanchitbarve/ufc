import http.server
import json
import os
import sys
import urllib.parse
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# --- BACKEND CORE FUNCTIONS (UNCHANGED) ---

def load_data_and_train(csv_path="ufc-master.csv"):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"'{csv_path}' not found in current directory.")

    df = pd.read_csv(csv_path)

    # Expanded pre-fight features incorporating Reach, KO, Submissions, and Wins
    features = [
        # Physical & Reach Attributes
        "R_age", "B_age", 
        "R_height_cms", "B_height_cms", 
        "R_reach_cms", "B_reach_cms",
        
        # Fight History, Wins, & Streaks
        "R_wins", "B_wins", 
        "R_losses", "B_losses",
        "R_current_win_streak", "B_current_win_streak",
        "R_current_lose_streak", "B_current_lose_streak",
        
        # Finish Traits (KOs & Submissions)
        "R_win_by_KO/TKO", "B_win_by_KO/TKO",
        "R_win_by_Submission", "B_win_by_Submission",
        "R_avg_SUB_ATT", "B_avg_SUB_ATT",
        
        # Striking Metrics
        "R_avg_SIG_STR_pct", "B_avg_SIG_STR_pct",
        "R_avg_SIG_STR_landed", "B_avg_SIG_STR_landed",
        
        # Grappling Metrics
        "R_avg_TD_pct", "B_avg_TD_pct",
        "R_avg_TD_landed", "B_avg_TD_landed",
        
        # Betting Odds
        "R_odds", "B_odds"
    ]

    # Filter to columns that actually exist in your CSV
    existing_features = [col for col in features if col in df.columns]

    # Clean missing values with column medians
    df_clean = df.copy()
    df_clean[existing_features] = df_clean[existing_features].fillna(
        df_clean[existing_features].median()
    )
    df_clean = df_clean.dropna(subset=["Winner"])

    X = df_clean[existing_features]
    y = df_clean["Winner"]

    # Train Random Forest Classifier
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X, y)

    return model, df, existing_features


def get_fighter_stats_dict(df, fighter_name, feature_names):
    """Retrieve fighter statistics dynamically for all required model features."""
    r_matches = df[df["R_fighter"] == fighter_name]
    b_matches = df[df["B_fighter"] == fighter_name]

    stats = {}

    for col in feature_names:
        if col.startswith("R_"):
            clean_stat = col[2:]  # Remove 'R_' prefix
            b_col = f"B_{clean_stat}"

            if not r_matches.empty and pd.notna(r_matches[col].iloc[0]):
                val = r_matches[col].iloc[0]
            elif (
                not b_matches.empty
                and b_col in b_matches.columns
                and pd.notna(b_matches[b_col].iloc[0])
            ):
                val = b_matches[b_col].iloc[0]
            else:
                val = df[col].median()

            stats[clean_stat] = float(val)

    return stats


print("[BACKEND] Initializing UFC Fight Predictor core engine...")
MODEL, DF, FEATURE_NAMES = load_data_and_train()
print(f"[BACKEND] Engine ready! Model trained on {len(DF)} records.")

# Precompute weight classes and rosters for instant frontend response
if "weight_class" in DF.columns:
    RAW_CLASSES = sorted([str(wc) for wc in DF["weight_class"].dropna().unique()])
    ALL_WEIGHT_CLASSES = ["All Weight Classes"] + RAW_CLASSES
else:
    ALL_WEIGHT_CLASSES = ["All Weight Classes"]

WEIGHT_CLASS_FIGHTERS = {}
for wc in ALL_WEIGHT_CLASSES:
    if wc == "All Weight Classes" or "weight_class" not in DF.columns:
        filtered = DF
    else:
        filtered = DF[DF["weight_class"] == wc]
    
    roster = sorted(list(set(filtered["R_fighter"].dropna()).union(set(filtered["B_fighter"].dropna()))))
    WEIGHT_CLASS_FIGHTERS[wc] = roster

print(f"[BACKEND] Roster cached for {len(ALL_WEIGHT_CLASSES)} weight classes.")


# --- HTTP REQUEST HANDLER ---

class UFCPredictorHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for convenience
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/all-data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {
                "weight_classes": ALL_WEIGHT_CLASSES,
                "rosters": WEIGHT_CLASS_FIGHTERS,
                "total_bouts": len(DF),
                "features_count": len(FEATURE_NAMES)
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        elif path == "/api/weight-classes":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"weight_classes": ALL_WEIGHT_CLASSES}).encode("utf-8"))
            return

        elif path == "/api/fighters":
            query = urllib.parse.parse_qs(parsed.query)
            wc = query.get("weight_class", ["All Weight Classes"])[0]
            fighters = WEIGHT_CLASS_FIGHTERS.get(wc, WEIGHT_CLASS_FIGHTERS["All Weight Classes"])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"fighters": fighters, "weight_class": wc}).encode("utf-8"))
            return

        # Default: Serve static files (index.html, styles.css, app.js, etc.)
        if path == "/" or path == "":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/predict":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Invalid JSON: {e}"}).encode("utf-8"))
                return

            fighter_a = payload.get("fighter_a")
            fighter_b = payload.get("fighter_b")

            if not fighter_a or not fighter_b:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "fighter_a and fighter_b are required"}).encode("utf-8"))
                return

            if fighter_a == fighter_b:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Please select two different fighters."}).encode("utf-8"))
                return

            # --- EXACT PREDICTION LOGIC FROM APP.PY ---
            stats_a = get_fighter_stats_dict(DF, fighter_a, FEATURE_NAMES)
            stats_b = get_fighter_stats_dict(DF, fighter_b, FEATURE_NAMES)

            # Construct input row matching model feature expectations
            input_row = []
            for col in FEATURE_NAMES:
                if col.startswith("R_"):
                    stat_key = col[2:]
                    input_row.append(stats_a.get(stat_key, 0.0))
                elif col.startswith("B_"):
                    stat_key = col[2:]
                    input_row.append(stats_b.get(stat_key, 0.0))
                else:
                    input_row.append(0.0)

            input_data = pd.DataFrame([input_row], columns=FEATURE_NAMES)

            # Predict outcomes
            prediction = MODEL.predict(input_data)[0]
            probs = MODEL.predict_proba(input_data)[0]

            classes = list(MODEL.classes_)
            red_idx = classes.index("Red") if "Red" in classes else 0
            blue_idx = classes.index("Blue") if "Blue" in classes else 1

            prob_a = float(probs[red_idx])
            prob_b = float(probs[blue_idx])

            winner = fighter_a if prediction == "Red" else fighter_b

            # Comparison metrics
            display_metrics = {
                "Reach (cm)": "reach_cms",
                "Total Wins": "wins",
                "Total Losses": "losses",
                "KO/TKO Wins": "win_by_KO/TKO",
                "Submission Wins": "win_by_Submission",
                "Win Streak": "current_win_streak",
                "Sig. Striking %": "avg_SIG_STR_pct",
                "Takedown %": "avg_TD_pct",
            }

            comparison_rows = []
            for label, raw_key in display_metrics.items():
                val_a = float(stats_a.get(raw_key, 0.0))
                val_b = float(stats_b.get(raw_key, 0.0))
                comparison_rows.append({
                    "metric": label,
                    "val_a": round(val_a, 2),
                    "val_b": round(val_b, 2),
                    "leader": "a" if val_a > val_b else ("b" if val_b > val_a else "tie")
                })

            response_data = {
                "winner": winner,
                "winner_corner": "red" if prediction == "Red" else "blue",
                "fighter_a": fighter_a,
                "fighter_b": fighter_b,
                "prob_a": round(prob_a * 100, 1),
                "prob_b": round(prob_b * 100, 1),
                "stats_a": {k: round(v, 2) for k, v in stats_a.items()},
                "stats_b": {k: round(v, 2) for k, v in stats_b.items()},
                "comparison": comparison_rows
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


def run_server(port=5000):
    server_address = ("", port)
    httpd = http.server.ThreadingHTTPServer(server_address, UFCPredictorHandler)
    print(f"[SERVER] UFC Predictor Frontend & API running at: http://localhost:{port}")
    print(f"[SERVER] Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Server shutting down.")
        httpd.server_close()


if __name__ == "__main__":
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
