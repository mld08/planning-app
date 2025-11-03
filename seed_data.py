#!/usr/bin/env python3
"""
Script pour peupler la base de données avec des données de test
Usage: python seed_data.py
"""

from app import app, db
from models import User, Planning, Affectation
from scheduler import PlanningScheduler
from flask_mail import Mail
from datetime import date, timedelta

def create_sample_agents():
    """Crée des agents de test avec leurs contraintes"""
    print("👥 Création des agents de test...")
    
    agents_data = [
        # HOMMES
        {
            "nom": "DIOP", "prenom": "Birama", 
            "email": "birama.diop@test.com", 
            "username": "bdiop",
            "phone": "+221 77 123 45 01",
            "fonction": "Chef d'équipe BVP",
            "genre": "homme",
            "est_chef_equipe": True,
            "est_chef_equipe_bvp": True
        },
        {
            "nom": "SECK", "prenom": "Cheikhouna Ahmadou Bamba",
            "email": "cheikhouna.seck@test.com",
            "username": "cseck",
            "phone": "+221 77 234 56 02",
            "fonction": "Chef d'équipe BVP / Inspecteur Certification Aéroport",
            "genre": "homme",
            "est_chef_equipe_bvp": True,
            "est_certification_aeroport": True,
            "est_chef_equipe_usine": True
        },
        {
            "nom": "BA", "prenom": "Oury",
            "email": "oury.ba@test.com",
            "username": "oba",
            "phone": "+221 77 345 67 03",
            "fonction": "Inspecteur Certification Aéroport",
            "genre": "homme",
            "est_certification_aeroport": True
        },
        {
            "nom": "NDAO", "prenom": "Mamadou Awa",
            "email": "mamadou.ndao@test.com",
            "username": "mndao",
            "phone": "+221 77 456 78 04",
            "fonction": "Chef d'équipe BVP / Inspecteur Certification Aéroport",
            "genre": "homme",
            "est_chef_equipe_bvp": True,
            "est_certification_aeroport": True,
            "est_chef_equipe_usine": True
        },
        {
            "nom": "FAYE", "prenom": "Alioune",
            "email": "alioune.faye@test.com",
            "username": "afaye",
            "phone": "+221 77 567 89 05",
            "fonction": "Chef d'équipe BVP / Inspecteur Certification Aéroport",
            "genre": "homme",
            "est_chef_equipe_bvp": True,
            "est_certification_aeroport": True,
            "est_chef_equipe_usine": True
        },
        {
            "nom": "LO", "prenom": "Mayoni",
            "email": "mayoni.lo@test.com",
            "username": "mlo",
            "phone": "+221 77 678 90 06",
            "fonction": "Chef d'équipe BVP",
            "genre": "homme",
            "est_chef_equipe_bvp": True
        },
        {
            "nom": "SECK", "prenom": "Seydou",
            "email": "seydou.seck@test.com",
            "username": "sseck",
            "phone": "+221 77 789 01 07",
            "fonction": "Chef d'équipe BVP",
            "genre": "homme",
            "est_chef_equipe_bvp": True
        },
        {
            "nom": "SECK", "prenom": "Amadou Abdoulaye",
            "email": "amadou.seck@test.com",
            "username": "aseck",
            "phone": "+221 77 890 12 08",
            "fonction": "Chef d'équipe BVP / Chef équipe Inspection Usine",
            "genre": "homme",
            "est_chef_equipe_bvp": True,
            "est_chef_equipe_usine": True
        },
        {
            "nom": "TALLA", "prenom": "Bouna",
            "email": "bouna.talla@test.com",
            "username": "btalla",
            "phone": "+221 77 901 23 09",
            "fonction": "Chef d'équipe BVP / Chef équipe Inspection Usine",
            "genre": "homme",
            "est_chef_equipe_bvp": True,
            "est_chef_equipe_usine": True
        },
        {
            "nom": "CISSOKHO", "prenom": "Alassane",
            "email": "alassane.cissokho@test.com",
            "username": "acissokho",
            "phone": "+221 77 012 34 10",
            "fonction": "Chef d'équipe BVP / Chef équipe Inspection Usine",
            "genre": "homme",
            "est_chef_equipe_bvp": True,
            "est_chef_equipe_usine": True
        },
        {
            "nom": "SOW", "prenom": "Ibrahima",
            "email": "ibrahima.sow@test.com",
            "username": "isow",
            "phone": "+221 77 123 45 11",
            "fonction": "Agent de sécurité",
            "genre": "homme"
        },
        {
            "nom": "BA", "prenom": "Moussa",
            "email": "moussa.ba@test.com",
            "username": "mba",
            "phone": "+221 77 234 56 12",
            "fonction": "Agent de surveillance",
            "genre": "homme",
            "est_chef_bureau": True  # Chef de bureau exclu des veilles nocturnes
        },
        {
            "nom": "SARR", "prenom": "Omar",
            "email": "omar.sarr@test.com",
            "username": "osarr",
            "phone": "+221 77 345 67 13",
            "fonction": "Agent de sécurité",
            "genre": "homme"
        },
        {
            "nom": "CISSE", "prenom": "Abdoulaye",
            "email": "abdoulaye.cisse@test.com",
            "username": "acisse",
            "phone": "+221 77 456 78 14",
            "fonction": "Agent de sécurité",
            "genre": "homme"
        },
        
        # FEMMES
        {
            "nom": "GUEYE", "prenom": "Ndeye Maguette",
            "email": "ndeye.gueye@test.com",
            "username": "ngueye",
            "phone": "+221 77 567 89 15",
            "fonction": "Inspecteur Certification Aéroport",
            "genre": "femme",
            "est_certification_aeroport": True
        },
        {
            "nom": "NDIAYE", "prenom": "Fatou",
            "email": "fatou.ndiaye@test.com",
            "username": "fndiaye",
            "phone": "+221 77 678 90 16",
            "fonction": "Agent de sécurité",
            "genre": "femme"
        },
        {
            "nom": "FALL", "prenom": "Aissatou",
            "email": "aissatou.fall@test.com",
            "username": "afall",
            "phone": "+221 77 789 01 17",
            "fonction": "Agent de surveillance",
            "genre": "femme"
        },
        {
            "nom": "GUEYE", "prenom": "Aminata",
            "email": "aminata.gueye@test.com",
            "username": "agueye",
            "phone": "+221 77 890 12 18",
            "fonction": "Agent de sécurité",
            "genre": "femme"
        },
        {
            "nom": "SY", "prenom": "Khady",
            "email": "khady.sy@test.com",
            "username": "ksy",
            "phone": "+221 77 901 23 19",
            "fonction": "Agent de surveillance",
            "genre": "femme"
        },
        {
            "nom": "THIAM", "prenom": "Marieme",
            "email": "marieme.thiam@test.com",
            "username": "mthiam",
            "phone": "+221 77 012 34 20",
            "fonction": "Agent de sécurité",
            "genre": "femme"
        },
    ]
    
    created_count = 0
    
    for data in agents_data:
        # Vérifier si l'agent existe déjà (par username ou email)
        existing = User.query.filter(
            (User.email == data["email"]) | (User.username == data.get("username"))
        ).first()
        
        if not existing:
            agent = User(
                nom=data["nom"],
                prenom=data["prenom"],
                email=data["email"],
                username=data.get("username"),
                phone=data.get("phone"),
                fonction=data.get("fonction"),
                role='agent',
                disponibilite=True,
                # Nouveaux champs contraintes
                genre=data.get("genre"),
                est_chef_equipe=data.get("est_chef_equipe", False),
                est_chef_bureau=data.get("est_chef_bureau", False),
                est_certification_aeroport=data.get("est_certification_aeroport", False),
                est_chef_equipe_bvp=data.get("est_chef_equipe_bvp", False),
                est_chef_equipe_usine=data.get("est_chef_equipe_usine", False),
                est_observateur_embarque=data.get("est_observateur_embarque", False)
            )
            agent.set_password("password123")  # Mot de passe de test
            db.session.add(agent)
            created_count += 1
            
            # Afficher avec indicateurs de contraintes
            contraintes = []
            if data.get("genre") == "femme":
                contraintes.append("👩 Femme")
            if data.get("est_chef_equipe"):
                contraintes.append("👔 Chef équipe")
            if data.get("est_chef_bureau"):
                contraintes.append("👔 Chef bureau")
            if data.get("est_chef_equipe_bvp"):
                contraintes.append("🚢 Chef BVP")
            if data.get("est_certification_aeroport"):
                contraintes.append("✈️ Certif Aéro")
            if data.get("est_chef_equipe_usine"):
                contraintes.append("🏭 Chef Usine")
            
            contraintes_str = " | ".join(contraintes) if contraintes else "Agent standard"
            print(f"   ✅ {data['prenom']} {data['nom']}: {contraintes_str}")
        else:
            print(f"   ⏭️  Agent existe déjà: {data['prenom']} {data['nom']}")
    
    db.session.commit()
    print(f"\n✅ {created_count} nouveaux agents créés!")
    return created_count

def generate_test_planning():
    """Génère un planning de test pour la semaine en cours"""
    print("\n📅 Génération du planning de test...")
    
    # Calculer le lundi de cette semaine
    today = date.today()
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)
    
    # Vérifier si un planning existe déjà
    existing = Planning.query.filter_by(date_debut=monday).first()
    if existing:
        print(f"   ⏭️  Un planning existe déjà pour la semaine du {monday.strftime('%d/%m/%Y')}")
        return existing
    
    # Créer le planning
    mail = Mail(app)
    scheduler = PlanningScheduler(app, mail)
    
    try:
        planning = scheduler.generer_planning_semaine(date_debut=monday)
        print(f"   ✅ Planning généré: Semaine {planning.semaine}/{planning.annee}")
        print(f"   📆 Période: {planning.periode}")
        
        # Compter les affectations
        nb_affectations = Affectation.query.filter_by(planning_id=planning.id).count()
        print(f"   📋 {nb_affectations} affectations créées")
        
        # Vérifier les contraintes
        print("\n   🔍 Vérification des contraintes:")
        
        # Contrainte 1: Aucune femme de nuit
        femmes_nuit = db.session.query(User).join(Affectation).filter(
            Affectation.planning_id == planning.id,
            Affectation.shift == 'nuit',
            User.genre == 'femme'
        ).count()
        
        if femmes_nuit == 0:
            print(f"      ✅ Contrainte 1: Aucune femme affectée de nuit")
        else:
            print(f"      ❌ Contrainte 1: {femmes_nuit} femme(s) affectée(s) de nuit")
        
        # Contrainte 2: Aucun chef de nuit
        chefs_nuit = db.session.query(User).join(Affectation).filter(
            Affectation.planning_id == planning.id,
            Affectation.shift == 'nuit',
            (User.est_chef_equipe == True) | (User.est_chef_bureau == True)
        ).count()
        
        if chefs_nuit == 0:
            print(f"      ✅ Contrainte 2: Aucun chef affecté de nuit")
        else:
            print(f"      ❌ Contrainte 2: {chefs_nuit} chef(s) affecté(s) de nuit")
        
        # Contrainte 3: Aucun inspecteur certif aéro au CRSS
        certif_crss = db.session.query(User).join(Affectation).filter(
            Affectation.planning_id == planning.id,
            Affectation.equipe == 'CRSS',
            User.est_certification_aeroport == True
        ).count()
        
        if certif_crss == 0:
            print(f"      ✅ Contrainte 3: Aucun inspecteur Certif Aéro au CRSS")
        else:
            print(f"      ❌ Contrainte 3: {certif_crss} inspecteur(s) Certif Aéro au CRSS")
        
        # Contrainte 5: Chefs BVP max 1 fois
        from sqlalchemy import func
        chefs_bvp_multi = db.session.query(
            User.id, 
            func.count(Affectation.id).label('nb')
        ).join(Affectation).filter(
            Affectation.planning_id == planning.id,
            Affectation.equipe == 'BVP',
            Affectation.poste == 'chef',
            User.est_chef_equipe_bvp == True
        ).group_by(User.id).having(func.count(Affectation.id) > 1).count()
        
        if chefs_bvp_multi == 0:
            print(f"      ✅ Contrainte 5: Aucun chef BVP affecté plus d'1 fois")
        else:
            print(f"      ❌ Contrainte 5: {chefs_bvp_multi} chef(s) BVP affecté(s) 2+ fois")
        
        return planning
    except Exception as e:
        print(f"   ❌ Erreur lors de la génération: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def display_statistics():
    """Affiche les statistiques de la base de données"""
    print("\n📊 Statistiques de la base de données:")
    print("-" * 60)
    
    nb_admins = User.query.filter_by(role='admin').count()
    nb_agents = User.query.filter_by(role='agent').count()
    nb_agents_dispo = User.query.filter_by(role='agent', disponibilite=True).count()
    nb_plannings = Planning.query.count()
    nb_affectations = Affectation.query.count()
    
    # Statistiques par genre
    nb_hommes = User.query.filter_by(role='agent', genre='homme').count()
    nb_femmes = User.query.filter_by(role='agent', genre='femme').count()
    
    # Statistiques des contraintes
    nb_chefs_bvp = User.query.filter_by(role='agent', est_chef_equipe_bvp=True).count()
    nb_certif_aero = User.query.filter_by(role='agent', est_certification_aeroport=True).count()
    nb_chefs_equipe = User.query.filter_by(role='agent', est_chef_equipe=True).count()
    nb_chefs_bureau = User.query.filter_by(role='agent', est_chef_bureau=True).count()
    
    print(f"   👨‍💼 Administrateurs: {nb_admins}")
    print(f"   👥 Agents totaux: {nb_agents}")
    print(f"   ✅ Agents disponibles: {nb_agents_dispo}")
    print(f"   📅 Plannings: {nb_plannings}")
    print(f"   📋 Affectations: {nb_affectations}")
    print()
    print(f"   👨 Hommes: {nb_hommes}")
    print(f"   👩 Femmes: {nb_femmes}")
    print()
    print(f"   🚢 Chefs d'équipe BVP: {nb_chefs_bvp}")
    print(f"   ✈️  Inspecteurs Certif Aéroport: {nb_certif_aero}")
    print(f"   👔 Chefs d'équipe: {nb_chefs_equipe}")
    print(f"   👔 Chefs de bureau: {nb_chefs_bureau}")
    print("-" * 60)

def main():
    """Fonction principale"""
    print("=" * 60)
    print("   PEUPLEMENT DE LA BASE DE DONNÉES AVEC DES DONNÉES DE TEST")
    print("=" * 60)
    print()
    
    with app.app_context():
        try:
            # Créer les agents
            agents_created = create_sample_agents()
            
            # Générer un planning de test
            if agents_created > 0 or User.query.filter_by(role='agent').count() >= 6:
                generate_test_planning()
            else:
                print("\n⚠️  Pas assez d'agents pour générer un planning (minimum 6 requis)")
            
            # Afficher les statistiques
            display_statistics()
            
            print("\n" + "=" * 60)
            print("✨ Peuplement terminé avec succès!")
            print("=" * 60)
            print("\n📝 Informations de connexion des agents de test:")
            print("   Username: (voir ci-dessus)")
            print("   Mot de passe: password123")
            print()
            print("   Exemples de connexion:")
            print("   • bdiop / password123 (Birama DIOP - Chef BVP)")
            print("   • oba / password123 (Oury BA - Certif Aéro)")
            print("   • ngueye / password123 (Ndeye Maguette GUEYE - Femme + Certif Aéro)")
            print("   • fndiaye / password123 (Fatou NDIAYE - Femme)")
            print()
            print("   💡 Les contraintes métier sont appliquées:")
            print("   ✅ Femmes exclues des horaires nocturnes")
            print("   ✅ Chefs exclus des veilles nocturnes")
            print("   ✅ Inspecteurs Certif Aéro exclus du CRSS")
            print("   ✅ Chefs BVP max 1 fois/semaine")
            print()
            
        except Exception as e:
            print(f"\n❌ Erreur: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()