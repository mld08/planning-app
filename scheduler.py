from datetime import datetime, timedelta, date
from models import db, User, Planning, Affectation, HistoriqueModification
from flask_mail import Message
from flask import current_app
import random


class PlanningScheduler:
    """Gestionnaire de planification automatique des Ã©quipes avec contraintes mÃ©tier"""
    
    def __init__(self, app=None, mail=None):
        self.app = app
        self.mail = mail
    
    def generer_planning_semaine(self, date_debut=None):
        """
        GÃ©nÃ¨re automatiquement le planning pour une semaine
        
        Args:
            date_debut: Date de dÃ©but de la semaine (lundi). Si None, prend la semaine suivante.
        
        Returns:
            Planning: Le planning crÃ©Ã©
        """
        with self.app.app_context():
            # DÃ©terminer la date de dÃ©but (lundi prochain si non spÃ©cifiÃ©)
            if date_debut is None:
                aujourd_hui = date.today()
                jours_jusqua_lundi = (7 - aujourd_hui.weekday()) % 7
                if jours_jusqua_lundi == 0:
                    jours_jusqua_lundi = 7
                date_debut = aujourd_hui + timedelta(days=jours_jusqua_lundi)
            
            date_fin = date_debut + timedelta(days=6)  # Dimanche
            
            # VÃ©rifier si un planning existe dÃ©jÃ  pour cette semaine
            planning_existant = Planning.query.filter(
                Planning.date_debut == date_debut
            ).first()
            
            if planning_existant:
                print(f"Un planning existe dÃ©jÃ  pour la semaine du {date_debut}")
                return planning_existant
            
            # CrÃ©er le nouveau planning
            semaine = date_debut.isocalendar()[1]
            annee = date_debut.year
            
            planning = Planning(
                semaine=semaine,
                annee=annee,
                date_debut=date_debut,
                date_fin=date_fin,
                statut='actif'
            )
            
            db.session.add(planning)
            db.session.flush()  # Pour obtenir l'ID du planning
            
            # GÃ©nÃ©rer les affectations pour chaque jour
            for i in range(7):
                jour = date_debut + timedelta(days=i)
                self._generer_affectations_jour(planning, jour)
            
            db.session.commit()
            
            # Envoyer les notifications par email
            #self._envoyer_notifications(planning)
            
            print(f"Planning gÃ©nÃ©rÃ© avec succÃ¨s pour la semaine du {date_debut}")
            return planning
    
    def _verifier_contraintes_agent(self, agent, shift, equipe, poste, jour):
        """
        VÃ©rifie si un agent peut Ãªtre affectÃ© selon les contraintes mÃ©tier
        
        Contraintes vÃ©rifiÃ©es:
        1. Femmes exclues des horaires nocturnes (17h-8h)
        2. Chefs d'Ã©quipe/bureau exclus des veilles nocturnes
        3. Inspecteurs Certification AÃ©roport exclus du CRSS
        7. Observateurs embarquÃ©s exclus jusqu'Ã  dÃ©barquement
        
        Args:
            agent: L'agent Ã  vÃ©rifier
            shift: 'jour' ou 'nuit'
            equipe: 'CRSS' ou 'BVP'
            poste: 'chef', 'inspecteur', 'agent'
            jour: Date du jour
        
        Returns:
            tuple: (bool, str) - (peut_etre_affecte, raison_si_non)
        """
        from contraintes import est_nom_dans_liste, INSPECTEURS_CERTIFICATION_AEROPORT
        
        # Contrainte 7 : Observateurs embarquÃ©s
        if agent.est_observateur_embarque:
            if agent.date_debarquement_prevue and jour <= agent.date_debarquement_prevue:
                return False, f"Agent embarquÃ© jusqu'au {agent.date_debarquement_prevue.strftime('%d/%m/%Y')}"
        
        # Contrainte 1a : Femmes exclues des horaires nocturnes (17h-8h)
        if agent.genre == 'femme' and shift == 'nuit':
            return False, "Femmes exclues des horaires nocturnes (Contrainte 1)"
        
        # Contrainte 2 : Chefs d'Ã©quipe/bureau exclus des veilles nocturnes
        if shift == 'nuit' and (agent.est_chef_equipe or agent.est_chef_bureau):
            return False, "Chefs d'Ã©quipe/bureau exclus des veilles nocturnes (Contrainte 2)"
        
        # Contrainte 3 : Inspecteurs Certification AÃ©roport exclus du CRSS
        if equipe == 'CRSS':
            if agent.est_certification_aeroport:
                return False, "Inspecteur Certification AÃ©roport exclu du CRSS (Contrainte 3)"
            
            # VÃ©rifier aussi par nom (fallback si le champ n'est pas renseignÃ©)
            if est_nom_dans_liste(agent.prenom, agent.nom, INSPECTEURS_CERTIFICATION_AEROPORT):
                return False, "Inspecteur Certification AÃ©roport exclu du CRSS (Contrainte 3)"
        
        return True, ""
    
    def _peut_etre_chef_equipe_bvp(self, agent, planning):
        """
        VÃ©rifie si un agent peut Ãªtre chef d'Ã©quipe BVP cette semaine
        
        Contrainte 5 : Ne pas programmer le mÃªme chef d'Ã©quipe BVP 2 fois dans la semaine
        
        Args:
            agent: L'agent Ã  vÃ©rifier
            planning: Le planning de la semaine
        
        Returns:
            bool: True si l'agent peut Ãªtre chef d'Ã©quipe BVP
        """
        # VÃ©rifier si l'agent est chef d'Ã©quipe BVP
        if not agent.est_chef_equipe_bvp:
            return False
        
        # Compter combien de fois cet agent est dÃ©jÃ  chef d'Ã©quipe BVP cette semaine
        nb_fois_chef_bvp = Affectation.query.filter_by(
            planning_id=planning.id,
            agent_id=agent.id,
            equipe='BVP',
            poste='chef'
        ).count()
        
        # Maximum 1 fois par semaine (Contrainte 5)
        return nb_fois_chef_bvp < 1
    
    def _selectionner_chef_equipe_bvp(self, agents, planning):
        """
        SÃ©lectionne un chef d'Ã©quipe BVP selon les contraintes
        
        Contrainte 4 : Liste des chefs d'Ã©quipe BVP
        Contrainte 5 : Maximum 1 fois par semaine
        
        Args:
            agents: Liste des agents disponibles
            planning: Le planning de la semaine
        
        Returns:
            User: Le chef d'Ã©quipe sÃ©lectionnÃ© ou None
        """
        from contraintes import est_nom_dans_liste, CHEFS_EQUIPE_BVP
        
        # Filtrer les agents qui peuvent Ãªtre chef d'Ã©quipe BVP
        candidats = []
        for agent in agents:
            # VÃ©rifier si l'agent est dans la liste des chefs BVP (Contrainte 4)
            if agent.est_chef_equipe_bvp or est_nom_dans_liste(agent.prenom, agent.nom, CHEFS_EQUIPE_BVP):
                # VÃ©rifier qu'il n'a pas dÃ©jÃ  Ã©tÃ© chef cette semaine (Contrainte 5)
                if self._peut_etre_chef_equipe_bvp(agent, planning):
                    candidats.append(agent)
        
        # Retourner le premier candidat (dÃ©jÃ  triÃ© par rotation)
        return candidats[0] if candidats else None
    
    def _generer_affectations_jour(self, planning, jour):
        """
        GÃ©nÃ¨re les affectations pour un jour donnÃ© EN RESPECTANT TOUTES LES CONTRAINTES
        
        Args:
            planning: L'objet Planning
            jour: La date du jour
        """
        # RÃ©cupÃ©rer tous les agents disponibles
        agents_disponibles = User.query.filter_by(
            role='agent',
            disponibilite=True
        ).all()
        
        if len(agents_disponibles) < 6:
            raise Exception(f"Pas assez d'agents disponibles ({len(agents_disponibles)}/6 requis)")
        
        # Trier les agents selon les rÃ¨gles de rotation
        agents_tries = self._trier_agents_rotation(agents_disponibles, jour)
        
        # ========== VEILLE CRSS (1 jour + 1 nuit) ==========
        
        # Agent CRSS JOUR
        agent_crss_jour = self._selectionner_agent_shift(
            agents_tries, 'jour', jour, equipe='CRSS', poste='agent'
        )
        if agent_crss_jour:
            self._creer_affectation(planning, agent_crss_jour, jour, 'jour', 'CRSS', 'agent')
            agents_tries.remove(agent_crss_jour)
        
        # Agent CRSS NUIT
        agent_crss_nuit = self._selectionner_agent_shift(
            agents_tries, 'nuit', jour, equipe='CRSS', poste='agent'
        )
        if agent_crss_nuit:
            self._creer_affectation(planning, agent_crss_nuit, jour, 'nuit', 'CRSS', 'agent')
            agents_tries.remove(agent_crss_nuit)
        
        # ========== BRIGADE PORTUAIRE (BVP) ==========
        
        # Chef d'Ã©quipe BVP (JOUR) - Contrainte 4 & 5 appliquÃ©es
        chef = self._selectionner_chef_equipe_bvp(agents_tries, planning)
        if not chef:
            # Si aucun chef d'Ã©quipe BVP disponible, prendre un agent normal pour le jour
            chef = self._selectionner_agent_shift(agents_tries, 'jour', jour, equipe='BVP', poste='chef')
        
        if chef:
            self._creer_affectation(planning, chef, jour, 'jour', 'BVP', 'chef')
            agents_tries.remove(chef)
        
        # Inspecteur BVP (JOUR)
        inspecteur = self._selectionner_agent_shift(
            agents_tries, 'jour', jour, equipe='BVP', poste='inspecteur'
        )
        if inspecteur:
            self._creer_affectation(planning, inspecteur, jour, 'jour', 'BVP', 'inspecteur')
            agents_tries.remove(inspecteur)
        
        # 2 Agents BVP JOUR
        for i in range(2):
            if agents_tries:
                agent = self._selectionner_agent_shift(
                    agents_tries, 'jour', jour, equipe='BVP', poste='agent'
                )
                if agent:
                    self._creer_affectation(planning, agent, jour, 'jour', 'BVP', 'agent')
                    agents_tries.remove(agent)
        
        # 1 Agent BVP NUIT
        if agents_tries:
            agent_nuit = self._selectionner_agent_shift(
                agents_tries, 'nuit', jour, equipe='BVP', poste='agent'
            )
            if agent_nuit:
                self._creer_affectation(planning, agent_nuit, jour, 'nuit', 'BVP', 'agent')
    
    def _trier_agents_rotation(self, agents, jour):
        """
        Trie les agents selon les rÃ¨gles de rotation Ã©quitable
        
        Args:
            agents: Liste des agents disponibles
            jour: Date du jour
        
        Returns:
            Liste triÃ©e d'agents
        """
        # Calculer un score pour chaque agent
        agents_scores = []
        
        for agent in agents:
            score = 0
            
            # PrivilÃ©gier ceux qui ont le moins travaillÃ©
            score += (agent.compteur_jour + agent.compteur_nuit) * 100
            
            # PÃ©naliser si a travaillÃ© rÃ©cemment
            if agent.derniere_affectation:
                jours_depuis = (jour - agent.derniere_affectation).days
                if jours_depuis < 2:
                    score += 1000  # Forte pÃ©nalitÃ©
                elif jours_depuis < 4:
                    score += 500
            
            agents_scores.append((agent, score))
        
        # Trier par score croissant (ceux avec le score le plus bas en premier)
        agents_scores.sort(key=lambda x: x[1])
        
        return [agent for agent, score in agents_scores]
    
    def _selectionner_agent_shift(self, agents, shift, jour, equipe='BVP', poste='agent'):
        """
        Sélectionne un agent pour un shift donné en respectant TOUTES les contraintes
        
        Args:
            agents: Liste des agents disponibles
            shift: 'jour' ou 'nuit'
            jour: Date du jour
            equipe: 'CRSS' ou 'BVP'
            poste: 'chef', 'inspecteur', 'agent', 'chauffeur'
        
        Returns:
            User: L'agent sélectionné ou None
        """
        # Trier les agents par pertinence selon le poste
        agents_tries = []
        
        for agent in agents:
            # ===== VÉRIFIER LES CONTRAINTES MÉTIER AVANT TOUT =====
            peut_etre_affecte, raison = self._verifier_contraintes_agent(agent, shift, equipe, poste, jour)
            if not peut_etre_affecte:
                continue  # Passer à l'agent suivant
            
            # ===== CONTRAINTES DE BASE =====
            
            # Règle : pas deux nuits consécutives
            if shift == 'nuit':
                # Vérifier si l'agent a fait la nuit la veille
                hier = jour - timedelta(days=1)
                affectation_hier = Affectation.query.filter_by(
                    agent_id=agent.id,
                    jour=hier,
                    shift='nuit'
                ).first()
                
                if affectation_hier:
                    continue  # Skip cet agent
                
                # Vérifier si déjà affecté de nuit aujourd'hui
                affectation_aujourdhui = Affectation.query.filter_by(
                    agent_id=agent.id,
                    jour=jour,
                    shift='nuit'
                ).first()
                
                if affectation_aujourdhui:
                    continue
            
            # Vérifier si déjà affecté aujourd'hui
            affectation_aujourdhui = Affectation.query.filter_by(
                agent_id=agent.id,
                jour=jour
            ).first()
            
            if affectation_aujourdhui:
                continue
            
            # Calculer un score de pertinence
            score = 0
            
            # PRIVILÉGIER les agents avec les bonnes contraintes
            if equipe == 'CRSS' and agent.est_operateur_veille_crss:
                score -= 1000  # Forte priorité pour opérateurs CRSS
            
            if poste == 'chauffeur' and agent.est_chauffeur:
                score -= 1000  # Forte priorité pour chauffeurs
            
            if 'chauffeur' in str(agent.fonction).lower():
                score -= 500  # Priorité moyenne si fonction = chauffeur
            
            agents_tries.append((agent, score))
        
        # Trier par score (plus bas = meilleur)
        agents_tries.sort(key=lambda x: x[1])
        
        # Retourner le meilleur agent
        if agents_tries:
            return agents_tries[0][0]
        
        return None
    
    def _creer_affectation(self, planning, agent, jour, shift, equipe, poste):
        """
        CrÃ©e une affectation et met Ã  jour les compteurs de l'agent
        
        Args:
            planning: L'objet Planning
            agent: L'agent Ã  affecter
            jour: Date du jour
            shift: 'jour' ou 'nuit'
            equipe: 'CRSS' ou 'BVP'
            poste: 'chef', 'inspecteur', 'agent'
        """
        affectation = Affectation(
            planning_id=planning.id,
            agent_id=agent.id,
            jour=jour,
            shift=shift,
            equipe=equipe,
            poste=poste
        )
        
        db.session.add(affectation)
        
        # Mettre Ã  jour les compteurs de l'agent
        if shift == 'jour':
            agent.compteur_jour += 1
        else:
            agent.compteur_nuit += 1
        
        agent.dernier_shift = shift
        agent.derniere_affectation = jour
        
        db.session.add(agent)
    
    def _envoyer_notifications(self, planning):
        """
        Envoie les notifications par email Ã  tous les agents affectÃ©s
        
        Args:
            planning: L'objet Planning
        """
        if not self.mail:
            print("Service email non configurÃ©, notifications non envoyÃ©es")
            return
        
        # RÃ©cupÃ©rer tous les agents affectÃ©s pour ce planning
        agents_affectations = db.session.query(User).join(Affectation).filter(
            Affectation.planning_id == planning.id
        ).distinct().all()
        
        for agent in agents_affectations:
            # RÃ©cupÃ©rer toutes les affectations de cet agent pour cette semaine
            affectations = Affectation.query.filter_by(
                planning_id=planning.id,
                agent_id=agent.id
            ).order_by(Affectation.jour).all()
            
            # Construire le contenu de l'email
            self._envoyer_email_agent(agent, planning, affectations)
    
    def _envoyer_email_agent(self, agent, planning, affectations):
        """
        Envoie un email Ã  un agent avec son planning
        
        Args:
            agent: L'agent
            planning: Le planning
            affectations: Liste des affectations de l'agent
        """
        jours_semaine = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        
        # CrÃ©er un dictionnaire des affectations par jour
        affectations_par_jour = {}
        for aff in affectations:
            affectations_par_jour[aff.jour] = aff
        
        # Construire le corps de l'email
        corps = f"""
Bonjour {agent.prenom},

Voici votre planning pour la semaine du {planning.date_debut.strftime('%d/%m/%Y')} au {planning.date_fin.strftime('%d/%m/%Y')} :

"""
        
        # Ajouter chaque jour
        for i in range(7):
            jour = planning.date_debut + timedelta(days=i)
            nom_jour = jours_semaine[i]
            
            if jour in affectations_par_jour:
                aff = affectations_par_jour[jour]
                horaire = aff.horaire
                equipe = aff.equipe
                poste = aff.poste.capitalize() if aff.poste else 'Agent'
                corps += f"- {nom_jour} {jour.strftime('%d/%m')} : {aff.shift.capitalize()} ({horaire}) - {equipe} ({poste})\n"
            else:
                corps += f"- {nom_jour} {jour.strftime('%d/%m')} : Repos\n"
        
        corps += """
Merci et bon service !

---
Direction de la Protection et de la Surveillance des PÃªches (DPSP)
Service de planification automatique
"""
        
        try:
            msg = Message(
                subject=f"Votre planning - Semaine {planning.semaine}/{planning.annee}",
                recipients=[agent.email] if agent.email else [],
                body=corps
            )
            if agent.email:
                self.mail.send(msg)
                print(f"Email envoyÃ© Ã  {agent.email}")
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email Ã  {agent.email if agent.email else 'N/A'}: {str(e)}")
    
    def archiver_anciens_plannings(self, jours=30):
        """
        Archive les plannings de plus de X jours
        
        Args:
            jours: Nombre de jours aprÃ¨s lesquels archiver
        """
        with self.app.app_context():
            date_limite = date.today() - timedelta(days=jours)
            
            plannings = Planning.query.filter(
                Planning.date_fin < date_limite,
                Planning.statut == 'actif'
            ).all()
            
            for planning in plannings:
                planning.statut = 'archive'
                db.session.add(planning)
            
            db.session.commit()
            print(f"{len(plannings)} plannings archivÃ©s")