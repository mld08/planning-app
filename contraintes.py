"""
Configuration des contraintes métier pour la planification
"""

# Contrainte 3 : Inspecteurs Certification Aéroport (exclus du CRSS)
INSPECTEURS_CERTIFICATION_AEROPORT = [
    "Oury BA",
    "Ndeye Maguette GUEYE",
    "Cheikhouna Ahmadou Bamba SECK",
    "Mamadou Awa NDAO",
    "Alioune FAYE"
]

# Contrainte 4 : Chefs d'équipe à la BVP
CHEFS_EQUIPE_BVP = [
    "Birama DIOP",
    "Cheikhouna Ahmadou Bamba SECK",
    "Mayoni LO",
    "Seydou SECK",
    "Amadou Abdoulaye SECK",
    "Alioune FAYE",
    "Bouna TALLA",
    "Alassane CISSOKHO",
    "Mamadou Awa NDAO"
]

# Contrainte 6 : Chefs d'équipe Inspection Usine
CHEFS_EQUIPE_INSPECTION_USINE = [
    "Amadou Abdoulaye SECK",
    "Mamadou Awa NDAO",
    "Alioune FAYE",
    "Bouna TALLA",
    "Cheikhouna Ahmadou Bamba SECK",
    "Alassane CISSOKHO"
]

def get_nom_complet(prenom, nom):
    """Retourne le nom complet formaté"""
    return f"{prenom} {nom}".strip()

def est_nom_dans_liste(prenom, nom, liste_noms):
    """Vérifie si le nom complet est dans une liste"""
    nom_complet = get_nom_complet(prenom, nom)
    return nom_complet in liste_noms