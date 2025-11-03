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
    """Crée des agents de test"""
    print("👥 Création des agents de test...")
    
    agents_data = [
        {"nom": "Diop", "prenom": "Mamadou", "email": "mamadou.diop@test.com"},
        {"nom": "Ndiaye", "prenom": "Fatou", "email": "fatou.ndiaye@test.com"},
        {"nom": "Sow", "prenom": "Ibrahima", "email": "ibrahima.sow@test.com"},
        {"nom": "Fall", "prenom": "Aissatou", "email": "aissatou.fall@test.com"},
        {"nom": "Ba", "prenom": "Moussa", "email": "moussa.ba@test.com"},
        {"nom": "Gueye", "prenom": "Aminata", "email": "aminata.gueye@test.com"},
        {"nom": "Sarr", "prenom": "Omar", "email": "omar.sarr@test.com"},
        {"nom": "Sy", "prenom": "Khady", "email": "khady.sy@test.com"},
        {"nom": "Cisse", "prenom": "Abdoulaye", "email": "abdoulaye.cisse@test.com"},
        {"nom": "Thiam", "prenom": "Marieme", "email": "marieme.thiam@test.com"},
    ]
    
    created_count = 0
    
    for data in agents_data:
        # Vérifier si l'agent existe déjà
        existing = User.query.filter_by(email=data["email"]).first()
        if not existing:
            agent = User(
                nom=data["nom"],
                prenom=data["prenom"],
                email=data["email"],
                role='agent',
                disponibilite=True
            )
            agent.set_password("password123")  # Mot de passe de test
            db.session.add(agent)
            created_count += 1
            print(f"   ✅ Agent créé: {data['prenom']} {data['nom']}")
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
        
        return planning
    except Exception as e:
        print(f"   ❌ Erreur lors de la génération: {str(e)}")
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
    
    print(f"   👨‍💼 Administrateurs: {nb_admins}")
    print(f"   👥 Agents totaux: {nb_agents}")
    print(f"   ✅ Agents disponibles: {nb_agents_dispo}")
    print(f"   📅 Plannings: {nb_plannings}")
    print(f"   📋 Affectations: {nb_affectations}")
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
            print("   Email: [prenom.nom]@test.com")
            print("   Mot de passe: password123")
            print("\n   Exemple: mamadou.diop@test.com / password123\n")
            
        except Exception as e:
            print(f"\n❌ Erreur: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()