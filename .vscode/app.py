import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="UFC Fight Predictor", page_icon="🥊", layout="wide")

st.title("🥊 UFC Fight Predictor")
st.write(
    "Select two fighters to predict the winner based on historical statistics."
)


@st.cache_data
def load_data_and_train():
    # Update to look inside .vscode
    df = pd.read_csv(".vscode/ufc-master.csv")

    features = [
        "R_age",
        "B_age",
        "R_wins",
        "B_wins",
        "R_avg_SIG_STR_pct",
        "B_avg_SIG_STR_pct",
        "R_avg_TD_pct",
        "B_avg_TD_pct",
    ]

    df_clean = df.dropna(subset=features + ["Winner"]).copy()

    X = df_clean[features]
    y = df_clean["Winner"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    return model, df, features


def get_fighter_stats(df, fighter_name):
    """Retrieve fighter statistics across both Red and Blue corner entries."""
    r_matches = df[df["R_fighter"] == fighter_name]
    b_matches = df[df["B_fighter"] == fighter_name]

    age = (
        r_matches["R_age"].iloc[0]
        if not r_matches.empty and pd.notna(r_matches["R_age"].iloc[0])
        else (
            b_matches["B_age"].iloc[0]
            if not b_matches.empty and pd.notna(b_matches["B_age"].iloc[0])
            else df["R_age"].mean()
        )
    )

    wins = (
        r_matches["R_wins"].iloc[0]
        if not r_matches.empty and pd.notna(r_matches["R_wins"].iloc[0])
        else (
            b_matches["B_wins"].iloc[0]
            if not b_matches.empty and pd.notna(b_matches["B_wins"].iloc[0])
            else df["R_wins"].mean()
        )
    )

    sig_str = (
        r_matches["R_avg_SIG_STR_pct"].iloc[0]
        if not r_matches.empty
        and pd.notna(r_matches["R_avg_SIG_STR_pct"].iloc[0])
        else (
            b_matches["B_avg_SIG_STR_pct"].iloc[0]
            if not b_matches.empty
            and pd.notna(b_matches["B_avg_SIG_STR_pct"].iloc[0])
            else df["R_avg_SIG_STR_pct"].mean()
        )
    )

    td_pct = (
        r_matches["R_avg_TD_pct"].iloc[0]
        if not r_matches.empty and pd.notna(r_matches["R_avg_TD_pct"].iloc[0])
        else (
            b_matches["B_avg_TD_pct"].iloc[0]
            if not b_matches.empty
            and pd.notna(b_matches["B_avg_TD_pct"].iloc[0])
            else df["R_avg_TD_pct"].mean()
        )
    )

    return {
        "age": float(age),
        "wins": float(wins),
        "sig_str": float(sig_str),
        "td_pct": float(td_pct),
    }


try:
    model, df, feature_names = load_data_and_train()

    fighters = sorted(
        list(
            set(df["R_fighter"].dropna()).union(set(df["B_fighter"].dropna()))
        )
    )

    col1, col2 = st.columns(2)
    with col1:
        fighter_a = st.selectbox(
            "Select Fighter A (Red Corner)", fighters, index=0
        )
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
            stats_a = get_fighter_stats(df, fighter_a)
            stats_b = get_fighter_stats(df, fighter_b)

            input_data = pd.DataFrame(
                [[
                    stats_a["age"],
                    stats_b["age"],
                    stats_a["wins"],
                    stats_b["wins"],
                    stats_a["sig_str"],
                    stats_b["sig_str"],
                    stats_a["td_pct"],
                    stats_b["td_pct"],
                ]],
                columns=feature_names,
            )

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
                comp_df = pd.DataFrame(
                    {
                        "Metric": [
                            "Age",
                            "Total Wins",
                            "Sig. Strike %",
                            "Takedown %",
                        ],
                        fighter_a: [
                            f"{stats_a['age']:.0f}",
                            f"{stats_a['wins']:.0f}",
                            f"{stats_a['sig_str']*100:.1f}%",
                            f"{stats_a['td_pct']*100:.1f}%",
                        ],
                        fighter_b: [
                            f"{stats_b['age']:.0f}",
                            f"{stats_b['wins']:.0f}",
                            f"{stats_b['sig_str']*100:.1f}%",
                            f"{stats_b['td_pct']*100:.1f}%",
                        ],
                    }
                )
                st.dataframe(comp_df, use_container_width=True)

except Exception as e:
    st.error(
        f"Make sure 'ufc_data.csv' is in your folder and column names match."
        f" Error: {e}"
    )