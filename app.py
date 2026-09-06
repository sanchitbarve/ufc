import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="UFC Fight Predictor", page_icon="🥊", layout="wide")

st.title("🥊 UFC Fight Predictor")
st.write("Select a weight class and two fighters to predict the winner based on historical stats.")


@st.cache_data
def load_data_and_train():
    df = pd.read_csv("ufc-master.csv")

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


def create_gauge_chart(fighter_name, probability, color):
    """Generate an interactive Plotly Gauge Chart for win probabilities."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=probability * 100,
            number={"suffix": "%", "font": {"size": 36}},
            title={"text": f"<b>{fighter_name}</b>", "font": {"size": 20}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": color},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "#cccccc",
                "steps": [
                    {"range": [0, 50], "color": "#f2f2f2"},
                    {"range": [50, 100], "color": "#e6e6e6"},
                ],
                "threshold": {
                    "line": {"color": "gold", "width": 4},
                    "thickness": 0.75,
                    "value": probability * 100,
                },
            },
        )
    )
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
    return fig


try:
    model, df, feature_names = load_data_and_train()

    # --- WEIGHT CLASS FILTERING ---
    if "weight_class" in df.columns:
        weight_classes = ["All Weight Classes"] + sorted(
            [str(wc) for wc in df["weight_class"].dropna().unique()]
        )
    else:
        weight_classes = ["All Weight Classes"]

    selected_wc = st.selectbox("🏋️ Filter by Weight Class", weight_classes)

    # Filter dataframe based on weight class selection
    if selected_wc != "All Weight Classes" and "weight_class" in df.columns:
        filtered_df = df[df["weight_class"] == selected_wc]
    else:
        filtered_df = df

    # Get unique fighters present in the filtered dataframe
    fighters = sorted(
        list(
            set(filtered_df["R_fighter"].dropna()).union(
                set(filtered_df["B_fighter"].dropna())
            )
        )
    )

    if not fighters:
        st.warning("No fighters found for the selected weight class.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            fighter_a = st.selectbox("Select Fighter A (Red Corner)", fighters, index=0)
        with col2:
            fighter_b = st.selectbox(
                "Select Fighter B (Blue Corner)",
                fighters,
                index=min(1, len(fighters) - 1),
            )

        if st.button("PREDICT FIGHT", type="primary"):
            if fighter_a == fighter_b:
                st.warning("Please select two different fighters.")
            else:
                stats_a = get_fighter_stats_dict(df, fighter_a, feature_names)
                stats_b = get_fighter_stats_dict(df, fighter_b, feature_names)

                # Construct input row matching model feature expectations
                input_row = []
                for col in feature_names:
                    if col.startswith("R_"):
                        stat_key = col[2:]
                        input_row.append(stats_a.get(stat_key, 0.0))
                    elif col.startswith("B_"):
                        stat_key = col[2:]
                        input_row.append(stats_b.get(stat_key, 0.0))
                    else:
                        input_row.append(0.0)

                input_data = pd.DataFrame([input_row], columns=feature_names)

                # Predict outcomes
                prediction = model.predict(input_data)[0]
                probs = model.predict_proba(input_data)[0]

                classes = list(model.classes_)
                red_idx = classes.index("Red") if "Red" in classes else 0
                blue_idx = classes.index("Blue") if "Blue" in classes else 1

                prob_a = probs[red_idx]
                prob_b = probs[blue_idx]

                winner = fighter_a if prediction == "Red" else fighter_b

                st.success(f"**Predicted Winner:** 🏆 {winner}")

                # Gauge Charts
                st.subheader("Win Probability Breakdown")
                col_gauge1, col_gauge2 = st.columns(2)

                with col_gauge1:
                    fig_a = create_gauge_chart(fighter_a, prob_a, "#d9534f")
                    st.plotly_chart(fig_a, use_container_width=True)

                with col_gauge2:
                    fig_b = create_gauge_chart(fighter_b, prob_b, "#0275d8")
                    st.plotly_chart(fig_b, use_container_width=True)

                # Detailed Matchup Statistics Comparison Table
                with st.expander("Show Matchup Statistics Comparison"):
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

                    comp_data = {"Metric": list(display_metrics.keys())}

                    comp_data[fighter_a] = [
                        f"{stats_a.get(raw_key, 0):.1f}"
                        for raw_key in display_metrics.values()
                    ]
                    comp_data[fighter_b] = [
                        f"{stats_b.get(raw_key, 0):.1f}"
                        for raw_key in display_metrics.values()
                    ]

                    comp_df = pd.DataFrame(comp_data)
                    st.dataframe(comp_df, use_container_width=True)

except Exception as e:
    st.error(f"Make sure 'ufc-master.csv' is in your folder. Error details: {e}")