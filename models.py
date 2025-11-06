from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modèle pour les utilisateurs (agents et admins)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False, index=True)
    username = db.Column(db.String(50), unique=True, nullable=True, index=True)  # NOUVEAU
    phone = db.Column(db.String(20), nullable=True)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    fonction = db.Column(db.String(100), nullable=True)
    chef_de_mission = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='agent')  # 'admin' ou 'agent'
    disponibilite = db.Column(db.Boolean, default=True)
    # ========== NOUVEAUX CHAMPS POUR LES CONTRAINTES ==========
    genre = db.Column(db.String(10), nullable=True)  # 'homme', 'femme'
    est_chef_equipe = db.Column(db.Boolean, default=False)
    est_chef_bureau = db.Column(db.Boolean, default=False)
    est_certification_aeroport = db.Column(db.Boolean, default=False)
    est_chef_equipe_bvp = db.Column(db.Boolean, default=False)
    est_chef_equipe_usine = db.Column(db.Boolean, default=False)
    est_observateur_embarque = db.Column(db.Boolean, default=False)
    est_chauffeur = db.Column(db.Boolean, default=False)
    est_operateur_veille_crss = db.Column(db.Boolean, default=False)
    date_embarquement = db.Column(db.Date, nullable=True)
    date_debarquement_prevue = db.Column(db.Date, nullable=True)
    compteur_jour = db.Column(db.Integer, default=0)
    compteur_nuit = db.Column(db.Integer, default=0)
    dernier_shift = db.Column(db.String(10), nullable=True)  # 'jour', 'nuit', ou None
    derniere_affectation = db.Column(db.Date, nullable=True)
    cree_le = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    affectations = db.relationship('Affectation', backref='agent', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash le mot de passe"""
        self.mot_de_passe = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return check_password_hash(self.mot_de_passe, password)
    
    @property
    def nom_complet(self):
        """Retourne le nom complet"""
        return f"{self.prenom} {self.nom}"
    
    def __repr__(self):
        return f'<User {self.email}>'


class Planning(db.Model):
    """Modèle pour les plannings hebdomadaires"""
    __tablename__ = 'plannings'
    
    id = db.Column(db.Integer, primary_key=True)
    semaine = db.Column(db.Integer, nullable=False)  # Numéro de semaine
    annee = db.Column(db.Integer, nullable=False)  # Année
    date_debut = db.Column(db.Date, nullable=False, index=True)
    date_fin = db.Column(db.Date, nullable=False)
    statut = db.Column(db.String(20), default='actif')  # 'actif', 'archive'
    cree_le = db.Column(db.DateTime, default=datetime.utcnow)
    cree_par = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relations
    affectations = db.relationship('Affectation', backref='planning', lazy='dynamic', cascade='all, delete-orphan')
    createur = db.relationship('User', foreign_keys=[cree_par])
    
    def __repr__(self):
        return f'<Planning Semaine {self.semaine}/{self.annee}>'
    
    @property
    def periode(self):
        """Retourne la période formatée"""
        return f"{self.date_debut.strftime('%d/%m/%Y')} - {self.date_fin.strftime('%d/%m/%Y')}"


class Affectation(db.Model):
    """Modèle pour les affectations individuelles"""
    __tablename__ = 'affectations'
    
    id = db.Column(db.Integer, primary_key=True)
    planning_id = db.Column(db.Integer, db.ForeignKey('plannings.id'), nullable=False, index=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    jour = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(10), nullable=False)  # 'jour' ou 'nuit'
    equipe = db.Column(db.String(20), nullable=False)  # 'CRSS' ou 'BVP'
    poste = db.Column(db.String(50), nullable=True)  # 'chef', 'inspecteur', 'agent'
    notes = db.Column(db.Text, nullable=True)
    cree_le = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Index composé pour optimiser les requêtes
    __table_args__ = (
        db.Index('idx_planning_jour', 'planning_id', 'jour'),
        db.Index('idx_agent_jour', 'agent_id', 'jour'),
    )
    
    def __repr__(self):
        return f'<Affectation {self.agent.nom_complet} - {self.jour} {self.shift}>'
    
    @property
    def horaire(self):
        """Retourne l'horaire formaté"""
        if self.shift == 'jour':
            return '08h–17h'
        else:
            return '17h–08h'


class HistoriqueModification(db.Model):
    """Modèle pour tracer les modifications manuelles"""
    __tablename__ = 'historique_modifications'
    
    id = db.Column(db.Integer, primary_key=True)
    planning_id = db.Column(db.Integer, db.ForeignKey('plannings.id'), nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # Description de l'action
    details = db.Column(db.Text, nullable=True)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    utilisateur = db.relationship('User')
    
    def __repr__(self):
        return f'<HistoriqueModification {self.action}>'