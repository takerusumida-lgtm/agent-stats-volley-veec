import streamlit as st
from datetime import datetime

# --- DONNÉES PRÉ-DÉFINIES (MODIFIEZ CECI POUR VOTRE ÉQUIPE) ---
LISTE_JOUEURS_PREDEFINIE = [
    {"numero": 1, "nom": "N. Le Passeur"},
    {"numero": 4, "nom": "D. Le Pointu"},
    {"numero": 6, "nom": "M. Le Central"},
    {"numero": 8, "nom": "A. Le Libero"},
    {"numero": 10, "nom": "C. Le Réceptionneur"},
    {"numero": 12, "nom": "E. Le Serviteur"},
    {"numero": 14, "nom": "S. Le Remplaçant"},
    {"numero": 16, "nom": "T. Le Jeune"},
]
# --- Fin des données pré-définies ---

# --- INITIALISATION DE L'ÉTAT DE SESSION ---
def init_session_state():
    """Initialise toutes les variables de session nécessaires."""
    if 'config_complete' not in st.session_state:
        st.session_state['config_complete'] = False
    if 'joueurs_disponibles' not in st.session_state:
        st.session_state['joueurs_disponibles'] = LISTE_JOUEURS_PREDEFINIE
    if 'formation_actuelle' not in st.session_state:
        # P1 à P6 (Clés: Position, Valeurs: Dictionnaire du joueur)
        st.session_state['formation_actuelle'] = {i: None for i in range(1, 7)}
    if 'set_actuel' not in st.session_state:
        st.session_state['set_actuel'] = 1
    if 'score_equipe' not in st.session_state:
        st.session_state['score_equipe'] = 0
    if 'score_adverse' not in st.session_state:
        st.session_state['score_adverse'] = 0
    if 'historique_stats' not in st.session_state:
        st.session_state['historique_stats'] = []
    if 'joueur_selectionne' not in st.session_state:
        st.session_state['joueur_selectionne'] = None

# --- LOGIQUE DU JEU ---
def appliquer_rotation(formation):
    """Effectue une rotation standard : 1->6, 6->5, ..., 2->1."""
    # S'assurer que nous travaillons sur une copie pour éviter les effets de bord indésirables
    new_formation = formation.copy()
    
    # Sauvegarde du joueur en P1
    joueur_p1 = new_formation[1]
    
    # Décalage des joueurs (P2 va en P1, P3 en P2, etc.)
    for i in range(1, 6):
        new_formation[i] = new_formation[i + 1]
    
    # Le joueur de P1 se retrouve en P6
    new_formation[6] = joueur_p1
    
    # Mettre à jour la variable de session
    st.session_state['formation_actuelle'] = new_formation
    
    return new_formation

def fin_de_set():
    """Gère la fin d'un set et prépare la re-configuration."""
    
    # 1. Avancer au set suivant
    st.session_state['set_actuel'] += 1
    
    # 2. Réinitialiser les scores
    st.session_state['score_equipe'] = 0
    st.session_state['score_adverse'] = 0
    
    # 3. Forcer la re-configuration de la formation
    st.session_state['config_complete'] = False 
    st.session_state['joueur_selectionne'] = None
    
    # Redémarrer l'application pour afficher l'écran de configuration
    st.experimental_rerun()

def log_stat(position, joueur, action_code, resultat):
    """
    Log une action (simule l'écriture dans le GSheet).
    À terme, remplacé par une connexion gspread.
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'set': st.session_state['set_actuel'],
        'score': f"{st.session_state['score_equipe']}-{st.session_state['score_adverse']}",
        'position': position,
        'joueur_nom': joueur['nom'],
        'action_code': action_code,
        'resultat': resultat
    }
    
    # Ajout à l'historique
    st.session_state['historique_stats'].insert(0, log_entry)
    
    # Réinitialiser l'état de clic pour masquer le panneau d'actions
    st.session_state['joueur_selectionne'] = None 
    st.experimental_rerun()


# --- ÉCRAN DE CONFIGURATION (PRÉ-SET) ---
def afficher_ecran_configuration():
    """Affiche la page d'assignation de la formation de départ."""
    st.title("🏐 Configuration de Match - Assignation des Postes")
    st.markdown(f"### Set {st.session_state['set_actuel']}")
    st.info("Assignez le joueur de départ pour chaque position sur le terrain.")
    
    
    options_joueurs_affichage = [""] + [
        f"{j['numero']} - {j['nom']}" for j in st.session_state['joueurs_disponibles']
    ]
    joueurs_map = {
        f"{j['numero']} - {j['nom']}": j for j in st.session_state['joueurs_disponibles']
    }

    cols_position = st.columns(3)
    
    # Ordre des positions pour l'affichage
    positions_affichage = {
        1: "Position 1 (Service)", 6: "Position 6 (Arrière Centre)", 5: "Position 5 (Arrière Gauche)",
        2: "Position 2 (Attaque Droit)", 3: "Position 3 (Attaque Centre)", 4: "Position 4 (Attaque Gauche)"
    }
    
    # Afficher les menus déroulants pour chaque position
    for i, (pos_num, pos_name) in enumerate(positions_affichage.items()):
        with cols_position[i % 3]:
            selection = st.selectbox(
                pos_name, 
                options=options_joueurs_affichage, 
                key=f"select_pos_{pos_num}"
            )
            if selection and selection != "":
                st.session_state['formation_actuelle'][pos_num] = joueurs_map[selection]
            else:
                st.session_state['formation_actuelle'][pos_num] = None

    # Bouton de validation
    st.markdown("---")
    
    if st.button("Valider la Formation et Commencer le Match 🚀", type="primary"):
        
        joueurs_selectionnes = [p for p in st.session_state['formation_actuelle'].values() if p is not None]
        
        if len(joueurs_selectionnes) < 6:
            st.error("Veuillez assigner exactement 6 joueurs aux positions 1 à 6.")
            return

        noms_selectionnes = [p['nom'] for p in joueurs_selectionnes]
        if len(noms_selectionnes) != len(set(noms_selectionnes)):
            st.error("Un même joueur ne peut pas occuper plusieurs positions de départ. Vérifiez vos sélections.")
            return
        
        st.session_state['config_complete'] = True
        st.experimental_rerun()

# --- ÉCRAN DE MATCH (SAISIE DES STATS) ---
def afficher_ecran_match():
    
    # --- ZONE 1 : EN-TÊTE ET CONTRÔLES ---
    st.title(f"🏐 Match en Cours - Set {st.session_state['set_actuel']}")
    
    col_score, col_controle_score, col_controle_match = st.columns([1, 1.5, 1])
    
    with col_score:
        st.metric(label="Score Actuel", value=f"{st.session_state['score_equipe']} - {st.session_state['score_adverse']}")
        
    with col_controle_score:
        # Ce bouton doit appeler la rotation ET incrémenter le score Équipe
        if st.button("Point Équipe (avec Rotation) ➕"):
            appliquer_rotation(st.session_state['formation_actuelle'])
            st.session_state['score_equipe'] += 1
            st.experimental_rerun()
            
        if st.button("Point Adverse ➖"):
            st.session_state['score_adverse'] += 1
            st.experimental_rerun()

    with col_controle_match:
        if st.button("Fin du Set (Passer à la Re-config)", type="secondary"):
            fin_de_set()
    
    st.markdown("---")
    
    # --- ZONE 2 : SCHÉMA DU TERRAIN ET CLIC SUR LE JOUEUR ---
    st.header("Schéma du Terrain : Clic pour Saisir une Stat")
    
    formation = st.session_state['formation_actuelle']
    
    # On simule le terrain avec des colonnes et des espaces
    col_gauche, col_centre, col_droite = st.columns(3)
    
    def creer_bouton_position(col, pos, formation):
        """Crée un bouton de position dans la colonne spécifiée."""
        with col:
            joueur = formation[pos]
            btn_label = f"P{pos}: {joueur['nom']} ({joueur['numero']})"
            
            # La fonction on_click met à jour l'état du joueur sélectionné
            st.button(
                btn_label, 
                key=f'btn_p{pos}',
                on_click=lambda: st.session_state.update(joueur_selectionne={'pos': pos, 'data': joueur})
            )
            # Ajout d'espaces après les positions 4, 3, 2 pour simuler le filet
            if pos in [4, 3, 2]:
                 st.markdown("<br><br><br>", unsafe_allow_html=True) 
    
    creer_bouton_position(col_gauche, 4, formation)
    creer_bouton_position(col_centre, 3, formation)
    creer_bouton_position(col_droite, 2, formation)
    creer_bouton_position(col_gauche, 5, formation)
    creer_bouton_position(col_centre, 6, formation)
    creer_bouton_position(col_droite, 1, formation)

    st.markdown("---")
    
    # --- ZONE 3 : PANNEAU D'ACTIONS DYNAMIQUES ET HISTORIQUE ---
    if st.session_state['joueur_selectionne']:
        joueur_sel = st.session_state['joueur_selectionne']
        
        st.subheader(f"Stat pour : {joueur_sel['data']['nom']} (P{joueur_sel['pos']})")
        
        col_succes, col_echec, col_neutre = st.columns(3)

        # Boutons d'Action (Les coachs adjoints appuient ici)
        with col_succes:
            st.button("🎯 Attaque Gagnante (Kill)", type="primary", use_container_width=True, on_click=log_stat, 
                      args=(joueur_sel['pos'], joueur_sel['data'], "ATK_KILL", "SUCCES"))
            st.button("✅ Réception Parfaite", type="primary", use_container_width=True, on_click=log_stat, 
                      args=(joueur_sel['pos'], joueur_sel['data'], "REC_PERF", "SUCCES"))
            st.button("🛡️ Block Gagnant", type="primary", use_container_width=True, on_click=log_stat, 
                      args=(joueur_sel['pos'], joueur_sel['data'], "BLK_GAIN", "SUCCES"))
            
        with col_echec:
            st.button("❌ Attaque Manquée", type="secondary", use_container_width=True, on_click=log_stat, 
                      args=(joueur_sel['pos'], joueur_sel['data'], "ATK_FAUTE", "ECHEC"))
            st.button("💥 Service Manqué", type="secondary", use_container_width=True, on_click=log_stat, 
                      args=(joueur_sel['pos'], joueur_sel['data'], "SVC_FAUTE", "ECHEC"))
            st.button("💔 Réception Manquée", type="secondary", use_container_width=True, on_click=log_stat, 
                      args=(joueur_sel['pos'], joueur_sel['data'], "REC_FAUTE", "ECHEC"))

        with col_neutre:
            st.button("👐 Attaque Manusiée", use_container_width=True, on_click=log_stat, 
                      args=(joueur_sel['pos'], joueur_sel['data'], "ATK_MANU", "NEUTRE"))
            st.button("🔄 Service (Dans le jeu)", use_container_width=True, on_click=log_stat, 
                      args=(joueur_sel['pos'], joueur_sel['data'], "SVC_OK", "NEUTRE"))
            
    st.markdown("---")
    
    if st.session_state['historique_stats']:
        st.subheader("Historique (5 Dernières Saisies)")
        st.dataframe(st.session_state['historique_stats'][:5], use_container_width=True)

# --- FONCTION PRINCIPALE DE L'APPLICATION ---
def main_app():
    init_session_state()
    
    # Affichage conditionnel entre la configuration (Pré-Set) et le Match
    if st.session_state['config_complete'] == False:
        afficher_ecran_configuration()
    else:
        afficher_ecran_match()

# --- EXÉCUTION ---
if __name__ == "__main__":
    main_app()
