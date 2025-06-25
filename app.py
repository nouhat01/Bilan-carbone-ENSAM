import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import os
from io import BytesIO

st.set_page_config(page_title="Bilan Carbone ENSAM", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-size: 13px;
        background-color: #f5f5f5;
        color: #222;
    }
    h1, h2, h3, h4 {
        font-size: 1.2em !important;
    }
    .stButton>button {
        font-size: 13px !important;
        padding: 6px 20px;
        border-radius: 10px;
        background-color: #4CAF50;
        color: white;
        border: none;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stSelectbox, .stNumberInput, .stTextInput {
        font-size: 13px !important;
    }
    .box {
        background-color: #ffffff;
        border: 1px solid #d3d3d3;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
""", unsafe_allow_html=True)


st.title("🌿 Application de Bilan Carbone - ENSAM Meknès")

mode = st.sidebar.radio("📋 Que souhaitez-vous faire ?", (
    "🧮 Estimer selon le nombre d'étudiants",
    "📝 Saisir des activités réelles"
), index=1)


@st.cache_data
def charger_facteurs():
    df = pd.read_excel("basecarbone_ensam_final_sources.xlsx")
    facteurs = {}
    for _, row in df.iterrows():
        poste = row["Nom poste français"]
        type_poste = row["Nom base français"]
        unite = row["Unité français"]
        facteur = row["Total poste non décomposé"]
        facteurs[(poste, type_poste)] = (unite, facteur)
    return facteurs

facteurs_dict = charger_facteurs()

scenarios_reduction = {
    "Électricité": [
        {"nom": "Installation de panneaux solaires", "reduction_pct": (50, 70)},
        {"nom": "Passage aux LED + capteurs", "reduction_pct": (20, 30)}
    ],
    "Transports": {
        "Bus": {"nom": "Optimisation bus hybrides", "reduction_pct": (15, 25)},
        "Voiture": {"nom": "Covoiturage obligatoire", "reduction_pct": (30, 50)},
        "Avion": {"nom": "Remplacé par visioconf.", "reduction_pct": (70, 100)}
    },
    "Achats": [
        {"poste": "Papier", "nom": "Zéro papier + recyclage", "reduction_pct": (80, 90)},
        {"poste": "Ordinateurs", "nom": "Reconditionnement", "reduction_pct": (40, 60)}
    ],
    "Numérique": [
        {"nom": "Green IT (streaming limité)", "reduction_pct": (30, 50)}
    ],
    "Déchets": [
        {"poste": "Ménagers", "nom": "Compostage + tri 5 flux", "reduction_pct": (60, 80)},
        {"poste": "Électroniques", "nom": "Collecte dédiée DEEE", "reduction_pct": (70, 90)}
    ],
    "Climatisation": [
        {"nom": "Remplacement par R32", "reduction_pct": 67}
    ]
}

if "saisies" not in st.session_state:
    st.session_state.saisies = []
if "afficher_resultats" not in st.session_state:
    st.session_state.afficher_resultats = False

if mode == "🧮 Estimer selon le nombre d'étudiants":
    st.markdown("<hr style='border: 1px solid #ccc;'>", unsafe_allow_html=True)
    st.header("📊🧮 Estimation du Bilan Carbone selon le nombre d'étudiants")
    nb_etudiants = st.number_input("👨‍🎓 Nombre d'étudiants", min_value=1, step=1, value=2000)

    emissions_moyennes_par_etudiant = {
        "Transports": 1.0,
        "Déchets ménagers": 0.3,
        "Numérique": 0.2,
        "Électricité": 1.48
    }

    st.subheader("🧾 Estimation poste par poste")
    total_estime = sum(val * nb_etudiants for val in emissions_moyennes_par_etudiant.values())
    for poste, val in emissions_moyennes_par_etudiant.items():
        st.markdown(f"<div class='box'>{poste} : {val * nb_etudiants:.1f} kg CO2e</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='box'>🧮 Total estimé : {total_estime/1000:.2f} tonnes CO2e/an</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='box'>👤 Moyenne par étudiant : {total_estime/nb_etudiants:.2f} kg CO2e/an/étudiant</div>", unsafe_allow_html=True)
    st.stop()

st.markdown("<hr style='border: 1px solid #ccc;'>", unsafe_allow_html=True)
st.header("📝➕ Ajouter une activité (transport, énergie, déchets...)")

st.number_input("👨‍🎓 Nombre d'étudiants (pour calcul par étudiant)", key="nb_etudiants", min_value=1, value=2000)

col1, col2 = st.columns(2)
with col1:
    postes = sorted(set(k[0] for k in facteurs_dict.keys()))
    poste = st.selectbox("📂 Poste", postes)
with col2:
    types = [k[1] for k in facteurs_dict.keys() if k[0] == poste]
    type_ = st.selectbox("📦 Type", types)

unite, facteur = facteurs_dict[(poste, type_)]

col3, col4 = st.columns(2)
with col3:
    quantite = st.number_input(f"🔢 Quantité ({unite})", min_value=0.0, value=0.0)
with col4:
    mois = st.selectbox("📅 Mois", ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre", "Global annuel"])

if st.button("➕ Ajouter l'activité", key="ajouter_activite"):
    emission = quantite * facteur
    st.session_state.saisies.append({
        "Poste": poste,
        "Type": type_,
        "Quantité": quantite,
        "Unité": unite,
        "Facteur": facteur,
        "Mois": mois,
        "Émissions (kg CO2e)": emission
    })
    st.rerun()

if st.session_state.saisies:
    st.markdown("<hr style='border: 1px solid #ccc;'>", unsafe_allow_html=True)
    st.subheader("📊 Activités saisies")
    df = pd.DataFrame(st.session_state.saisies)
    df.insert(0, "#", range(1, len(df) + 1))
    df.set_index("#", inplace=True)
    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Afficher les résultats", key="btn_afficher_resultats"):
            st.session_state.afficher_resultats = True
    with col2:
        if st.button("🔄 Réinitialiser", key="btn_reinitialiser"):
            st.session_state.saisies = []
            st.session_state.afficher_resultats = False
            st.rerun()

# Le bloc des résultats, scénarios, et PDF continue ensuite...


if st.session_state.afficher_resultats and st.session_state.saisies:
    df = pd.DataFrame(st.session_state.saisies)
    df["Poste"] = df["Poste"].astype(str).str.strip()
    df["Émissions (kg CO2e)"] = pd.to_numeric(df["Émissions (kg CO2e)"], errors="coerce").fillna(0)
    total = df["Émissions (kg CO2e)"].sum()
    par_poste = df.groupby("Poste")["Émissions (kg CO2e)"].sum()

    st.subheader("📊🌍 Résultats globaux")
    st.metric("🌡️ Total", f"{total/1000:.2f} t CO2e")
    st.metric("👤 Par étudiant", f"{total / st.session_state.nb_etudiants:.2f} kg CO2e")
    st.info("📌 L'évolution mensuelle des émissions est disponible dans le rapport PDF uniquement.")

    st.subheader("📈 Émissions par poste")
    if not par_poste.empty and par_poste.sum() > 0:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(par_poste, labels=par_poste.index, autopct="%1.1f%%", textprops={"fontsize": 8})
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.warning("Pas assez de données valides pour générer un graphique.")

    # === SCÉNARIOS DE RÉDUCTION ===
    st.subheader("🚀🧩 Scénarios de réduction proposés")
    reduction_totale_min = 0
    reduction_totale_max = 0
    scenarios_affiches = []

    for poste in par_poste.index:
        reductions = []
        if poste in scenarios_reduction:
            reductions = scenarios_reduction[poste]
        else:
            for cat in scenarios_reduction.values():
                if isinstance(cat, list):
                    for s in cat:
                        if s.get("poste") == poste:
                            reductions.append(s)
        if reductions:
            st.markdown(f"*{poste}*")
            for s in reductions:
                pct = s["reduction_pct"]
                if isinstance(pct, tuple):
                    gain_min = par_poste[poste] * pct[0] / 100
                    gain_max = par_poste[poste] * pct[1] / 100
                    reduction_totale_min += gain_min
                    reduction_totale_max += gain_max
                    st.markdown(f"- {s['nom']} → gain estimé : entre {gain_min:.1f} et {gain_max:.1f} kg CO2e")
                    scenarios_affiches.append((poste, s['nom'], gain_min, gain_max))
                else:
                    gain = par_poste[poste] * pct / 100
                    reduction_totale_min += gain
                    reduction_totale_max += gain
                    st.markdown(f"- {s['nom']} → gain estimé : {gain:.1f} kg CO2e")
                    scenarios_affiches.append((poste, s['nom'], gain, gain))

    # === COMPARATIF AVANT / APRÈS ===
    st.subheader("📉⚖️ Comparatif Avant / Après des émissions")
    total_apres_min = total - reduction_totale_max
    total_apres_max = total - reduction_totale_min

    comparatif_df = pd.DataFrame({
        "#": range(1, len(scenarios_affiches) + 1),
        "Scénario": [s[1] for s in scenarios_affiches],
        "Poste": [s[0] for s in scenarios_affiches],
        "Gain min (kg)": [round(s[2], 1) for s in scenarios_affiches],
        "Gain max (kg)": [round(s[3], 1) for s in scenarios_affiches]
    })
    comparatif_df.set_index("#", inplace=True)
    st.dataframe(comparatif_df)

    st.markdown(f"*Total actuel :* {total/1000:.2f} t CO2e")
    st.markdown(f"*Total après réduction (optimiste) :* {total_apres_min/1000:.2f} t CO2e")
    st.markdown(f"*Total après réduction (pessimiste) :* {total_apres_max/1000:.2f} t CO2e")

# === RAPPORT PDF FINAL ===
if st.button("🧾📄 Générer le rapport PDF complet"):
    pdf = FPDF()
    pdf.add_page()

    if os.path.exists("logo.png"):
        logo_width = 50
    page_width = pdf.w - 2 * pdf.l_margin
    logo_x = (page_width - logo_width) / 2 + pdf.l_margin
    pdf.image("logo.png", x=logo_x, y=10, w=logo_width)
    pdf.set_y(logo_width + 0.2)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Rapport Bilan Carbone - ENSAM Meknès", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Résultats globaux", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 10, f"Total : {total/1000:.2f} t CO2e", ln=True)
    pdf.cell(0, 10, f"Par étudiant : {total / st.session_state.nb_etudiants:.2f} kg CO2e", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Résumé des activités", ln=True)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 8, "Poste", border=1)
    pdf.cell(40, 8, "Type", border=1)
    pdf.cell(30, 8, "Quantité", border=1)
    pdf.cell(30, 8, "Unité", border=1)
    pdf.cell(40, 8, "Émissions (kg)", border=1, ln=True)
    pdf.set_font("Arial", "", 10)
    for i, row in df.iterrows():
        try:
            pdf.cell(40, 8, str(row['Poste'])[:18].encode('latin-1', 'replace').decode('latin-1'), border=1)
            pdf.cell(40, 8, str(row['Type'])[:18].encode('latin-1', 'replace').decode('latin-1'), border=1)
            pdf.cell(30, 8, f"{row['Quantité']:.2f}", border=1)
            pdf.cell(30, 8, str(row['Unité']), border=1)
            pdf.cell(40, 8, f"{row['Émissions (kg CO2e)']:.2f}", border=1, ln=True)
        except:
            continue
    pdf.ln(5)

    # Graphique Camembert
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(par_poste, labels=par_poste.index, autopct="%1.1f%%", textprops={"fontsize": 8})
    ax.axis("equal")
    camembert_path = "camembert.png"
    fig.savefig(camembert_path, dpi=100)
    plt.close(fig)
    pdf.image(camembert_path, x=60, w=90)
    pdf.ln(10)

    # Graphique courbe mensuelle si dispo
    mois_order = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    df_mensuel = df[df["Mois"] != "Global annuel"]
    df_mensuel["Mois"] = pd.Categorical(df_mensuel["Mois"], categories=mois_order, ordered=True)
    df_mois = df_mensuel.groupby("Mois")["Émissions (kg CO2e)"].sum().reindex(mois_order).fillna(0)
    if df_mois.sum() > 0:
        fig2, ax2 = plt.subplots(figsize=(5, 3))
        df_mois.plot(kind='line', marker='o', ax=ax2)
        ax2.set_title("Émissions mensuelles")
        courbe_path = "courbe_mois.png"
        fig2.savefig(courbe_path, dpi=100)
        plt.close(fig2)
        pdf.image(courbe_path, x=40, w=120)
        pdf.ln(10)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Comparatif Avant / Après", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 10, f"Total après réduction (optimiste) : {total_apres_min/1000:.2f} t CO2e", ln=True)
    pdf.cell(0, 10, f"Total après réduction (pessimiste) : {total_apres_max/1000:.2f} t CO2e", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Scénarios appliqués", ln=True)
    pdf.set_font("Arial", "", 10)
    for s in scenarios_affiches:
        poste, nom, gain_min, gain_max = s
        ligne = f"{poste} - {nom} : {gain_min:.1f} à {gain_max:.1f} kg CO2e"
        try:
            pdf.cell(0, 8, ligne, ln=True)
        except:
            pdf.cell(0, 8, ligne.encode('latin-1', 'replace').decode('latin-1'), ln=True)

    rapport_path = "rapport_bilan_complet.pdf"
    pdf.output(rapport_path)
    with open(rapport_path, "rb") as f:
        st.download_button("📥💾 Télécharger le rapport PDF complet", data=f, file_name=rapport_path, mime="application/pdf")