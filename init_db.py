#!/usr/bin/env python3
"""
Script d'initialisation de la base de données
Usage: python init_db.py
"""

from app import app, db
from models import User
import sys

def init_database():
    """Initialise la base de données et crée les tables"""
    print("🔧 Initialisation de la base de données...")
    
    with app.app_context():
        try:
            # Créer toutes les tables
            db.create_all()
            print("✅ Tables créées avec succès!")
            
            # Vérifier si un admin existe déjà
            admin_exists = User.query.filter_by(role='admin').first()
            
            if not admin_exists:
                print("\n👤 Aucun administrateur trouvé. Création du compte admin...")
                print("-" * 60)
                
                # Demander les informations
                prenom = "Admin"
                nom = ""
                email = "admin@gmail.com"
                username = "admin"
                
                while True:
                    password = "Adp1fidx$"
                    if len(password) >= 6:
                        break
                    print("⚠️  Le mot de passe doit contenir au moins 6 caractères!")
                
                # Créer l'admin
                admin = User(
                    prenom=prenom,
                    nom=nom,
                    email=email,
                    role='admin',
                    username=username,
                    disponibilite=True,
                    fonction="Administrateur",
                    chef_de_mission=None,
                    phone=None
                )
                admin.set_password(password)
                
                db.session.add(admin)
                db.session.commit()
                
                print(f"\n✅ Administrateur créé avec succès!")
                print(f"   Email: {email}")
                print(f"   Nom: {prenom} {nom}")
                print(f"   Email: {email}")
                print(f"   Username: {username}")
                print(f"   Mot de passe: {password}")
            else:
                print(f"\n✅ Un administrateur existe déjà: {admin_exists.email}")
            
            print("\n" + "=" * 60)
            print("✨ Initialisation terminée avec succès!")
            print("=" * 60)
            print("\n📝 Prochaines étapes:")
            print("   1. Configurer le fichier .env avec vos paramètres")
            print("   2. Lancer l'application: python app.py")
            print("   3. Accéder à http://localhost:5000")
            print("   4. Se connecter avec le compte admin créé")
            print("   5. Ajouter des agents via l'interface")
            print("   6. Générer le premier planning\n")
            
        except Exception as e:
            print(f"\n❌ Erreur lors de l'initialisation: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("   INITIALISATION DE L'APPLICATION DE PLANIFICATION")
    print("=" * 60)
    print()
    
    init_database()