import os
from datetime import timedelta

class Config:
    """Configuration de base de l'application"""
    
    # Clé secrète pour les sessions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'votre-cle-secrete-tres-complexe-ici'
    
    # Configuration de la base de données MySQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
       'mysql+pymysql://planning_user:planning_pass_2025@localhost/planning_db'
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #    'mysql+pymysql://digbdspc_planning:Adp1fidx$@localhost/digbdspc_planningdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=2)
    
    # Configuration Email (Flask-Mail)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'votre-email@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'votre-mot-de-passe'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@planning.com'
    
    # Configuration du scheduler
    SCHEDULER_API_ENABLED = True
    
    # Fuseaux horaires
    TIMEZONE = 'Africa/Dakar'
    
    # Règles de planification
    SHIFTS = {
        'jour': {'debut': '08:00', 'fin': '17:00'},
        'nuit': {'debut': '17:00', 'fin': '08:00'}
    }
    
    EQUIPES = {
        'CRSS': {
            'nom': 'Veille CRSS',
            'agents_jour': 1,
            'agents_nuit': 1
        },
        'BVP': {
            'nom': 'Brigade Portuaire',
            'chef_equipe': 1,
            'inspecteurs': 1,
            'agents': 3
        }
    }