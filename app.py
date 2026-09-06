import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="UFC Fight Predictor", page_icon="🥊", layout="wide")

st.title("🥊 UFC Fight Predictor")
st.write("Select two fighters to predict the winner based on historical statistics.")


@st.cache_data
def load_data_and_train():
    df = pd.read_csv("ufc-master.csv")

    # Explicitly selected pre-fight features
    features = [
        # Physical Attributes
        "R_age", "B_age", "R_height_cms", "B_height_cms", "R_reach_cms", "B_reach_cms",
        # Fight History & Streaks
        "R_wins", "B_wins", "R_losses", "B_losses",
        "R_current_win_streak", "B_current_win_streak",
        "R_current_lose_streak", "B_current_lose_streak",
        # Striking Metrics
        "R_avg_SIG_STR_pct", "B_avg_SIG_STR_pct",
        "R_avg_SIG_STR_landed", "B_avg_SIG_STR_landed",
        # Grappling Metrics
        "R_avg_TD_pct", "B_avg_TD_pct",
        "R_avg_TD_landed", "B_avg_TD_landed",
        "R_avg_SUB_ATT", "B_avg_SUB_ATT",
        # Betting Odds
        "R_odds", "B_odds"
    ]

    # Filter to columns that exist in CSV
    existing_features = [col for col in features if col in df.columns]

    # Clean missing values
    df_clean = df.copy()
    df_clean[existing_features] = df_clean[existing_features].fillna(df_clean[existing_features].median())
    df_clean = df_clean.dropna(subset=["Winner"])

    X = df_clean[existing_features]
    y = df_clean["Winner"]

    # Train Random Forest
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X, y)

    return model, df, existing_features


def get_fighter_stats_dict(df, fighter_name, feature_names):
    """Retrieve fighter statistics dynamically for all required model features."""
    r_matches = df[df["R_fighter"] == fighter_name]
    b_matches = df[df["B_fighter"] == fighter_name]
    
    stats = {}
    
    # Process Red corner features
    for col in feature_names:
        if col.startswith("R_"):
            clean_stat = col[2:] # Remove 'R_' prefix
            b_col = f"B_{clean_stat}"
            
            if not r_matches.empty and pd.notna(r_matches[col].iloc[0]):
                val = r_matches[col].iloc[0]
            elif not b_matches.empty and b_col in b_matches.columns and pd.notna(b_matches[b_col].iloc[0]):
                val = b_matches[b_col].iloc[0]
            else:
                val = df[col].median()
                
            stats[clean_stat] = float(val)
            
    return stats


try:
    model, df, feature_names = load_data_and_train()

    fighters = sorted(
        list(set(df["R_fighter"].dropna()).union(set(df["B_fighter"].dropna())))
    )

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

            # Construct input row matching model feature expectations exactly
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

            prediction = model.predict(input_data)[0]
            probs = model.predict_proba(input_data)[0]

            classes = list(model.classes_)
            red_idx = classes.index("Red") if "Red" in classes else 0
            blue_idx = classes.index("Blue") if "Blue" in classes else 1

            prob_a = probs[red_idx]
            prob_b = probs[blue_idx]

            winner = fighter_a if prediction == "Red" else fighter_b

            st.success(f"**Predicted Winner:** 🏆 {winner}")

            st.write(f"**{fighter_a}** (Red Corner Win Probability)")
            st.progress(float(prob_a), text=f"{prob_a * 100:.1f}%")

            st.write(f"**{fighter_b}** (Blue Corner Win Probability)")
            st.progress(float(prob_b), text=f"{prob_b * 100:.1f}%")

            with st.expander("Show Matchup Statistics Comparison"):
                metrics_to_show = ["age", "wins", "losses", "current_win_streak", "avg_SIG_STR_pct", "avg_TD_pct"]
                comp_data = {"Metric": metrics_to_show}
                
                comp_data[fighter_a] = [f"{stats_a.get(m, 0):.2f}" for m in metrics_to_show]
                comp_data[fighter_b] = [f"{stats_b.get(m, 0):.2f}" for m in metrics_to_show]
                
                comp_df = pd.DataFrame(comp_data)
                st.dataframe(comp_df, use_container_width=True)

except Exception as e:
    st.error(f"Make sure 'ufc-master.csv' is in your folder. Error details: {e}")