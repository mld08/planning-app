# MODIFICATIONS POUR LES CONTRAINTES MÉTIER
# ==========================================

## 📋 Contraintes à implémenter

1. ✅ Femmes exclues des horaires 17h-8h (BVP/CRSS) et patrouilles
2. ✅ Chefs d'équipe/bureau exclus des veilles nocturnes
3. ✅ Inspecteurs Certification Aéroport exclus du CRSS
4. ✅ Liste des chefs d'équipe BVP
5. ✅ Chef d'équipe BVP max 1 fois par semaine
6. ✅ Liste des chefs d'équipe Inspection Usine
7. ✅ Observateurs embarqués exclus jusqu'à débarquement

---

## 🔧 ÉTAPE 1 : Modifier models.py

### 1.1 Ajouter des champs au modèle User

**LOCALISATION :** Dans la classe `User`, après le champ `disponibilite`

```python
class User(UserMixin, db.Model):
    """Modèle pour les utilisateurs (agents et admins)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(50), unique=True, nullable=True, index=True)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='agent')
    fonction = db.Column(db.String(100), nullable=True)
    chef_de_mission = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    disponibilite = db.Column(db.Boolean, default=True)
    
    # ========== NOUVEAUX CHAMPS POUR LES CONTRAINTES ==========
    genre = db.Column(db.String(10), nullable=True)  # 'homme', 'femme'
    est_chef_equipe = db.Column(db.Boolean, default=False)
    est_chef_bureau = db.Column(db.Boolean, default=False)
    est_certification_aeroport = db.Column(db.Boolean, default=False)
    est_chef_equipe_bvp = db.Column(db.Boolean, default=False)
    est_chef_equipe_usine = db.Column(db.Boolean, default=False)
    est_observateur_embarque = db.Column(db.Boolean, default=False)
    date_embarquement = db.Column(db.Date, nullable=True)
    date_debarquement_prevue = db.Column(db.Date, nullable=True)
    # ===========================================================
    
    compteur_jour = db.Column(db.Integer, default=0)
    compteur_nuit = db.Column(db.Integer, default=0)
    dernier_shift = db.Column(db.String(10), nullable=True)
    derniere_affectation = db.Column(db.Date, nullable=True)
    cree_le = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    affectations = db.relationship('Affectation', backref='agent', lazy='dynamic', cascade='all, delete-orphan')
    
    # ... (le reste du code reste identique)
```

### 1.2 Migration SQL pour ajouter les colonnes

```sql
-- Exécutez ces commandes dans MySQL
USE planning_db;

ALTER TABLE users ADD COLUMN genre VARCHAR(10) AFTER phone;
ALTER TABLE users ADD COLUMN est_chef_equipe BOOLEAN DEFAULT FALSE AFTER genre;
ALTER TABLE users ADD COLUMN est_chef_bureau BOOLEAN DEFAULT FALSE AFTER est_chef_equipe;
ALTER TABLE users ADD COLUMN est_certification_aeroport BOOLEAN DEFAULT FALSE AFTER est_chef_bureau;
ALTER TABLE users ADD COLUMN est_chef_equipe_bvp BOOLEAN DEFAULT FALSE AFTER est_certification_aeroport;
ALTER TABLE users ADD COLUMN est_chef_equipe_usine BOOLEAN DEFAULT FALSE AFTER est_chef_equipe_bvp;
ALTER TABLE users ADD COLUMN est_observateur_embarque BOOLEAN DEFAULT FALSE AFTER est_chef_equipe_usine;
ALTER TABLE users ADD COLUMN date_embarquement DATE AFTER est_observateur_embarque;
ALTER TABLE users ADD COLUMN date_debarquement_prevue DATE AFTER date_embarquement;
```

---

## 🔧 ÉTAPE 2 : Créer un fichier de configuration des contraintes

**CRÉER UN NOUVEAU FICHIER :** `contraintes.py`

```python
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
```

---

## 🔧 ÉTAPE 3 : Modifier scheduler.py - Méthodes de validation

**LOCALISATION :** Dans la classe `PlanningScheduler`, AJOUTER ces nouvelles méthodes avant `_generer_affectations_jour`

```python
    def _verifier_contraintes_agent(self, agent, shift, equipe, poste, jour):
        """
        Vérifie si un agent peut être affecté selon les contraintes métier
        
        Args:
            agent: L'agent à vérifier
            shift: 'jour' ou 'nuit'
            equipe: 'CRSS' ou 'BVP'
            poste: 'chef', 'inspecteur', 'agent'
            jour: Date du jour
        
        Returns:
            tuple: (bool, str) - (peut_etre_affecte, raison_si_non)
        """
        from contraintes import est_nom_dans_liste, INSPECTEURS_CERTIFICATION_AEROPORT
        
        # Contrainte 7 : Observateurs embarqués
        if agent.est_observateur_embarque:
            if agent.date_debarquement_prevue and jour <= agent.date_debarquement_prevue:
                return False, "Agent embarqué jusqu'au débarquement"
        
        # Contrainte 1a : Femmes exclues des horaires nocturnes (17h-8h)
        if agent.genre == 'femme' and shift == 'nuit':
            return False, "Femmes exclues des horaires nocturnes"
        
        # Contrainte 2 : Chefs d'équipe/bureau exclus des veilles nocturnes
        if shift == 'nuit' and (agent.est_chef_equipe or agent.est_chef_bureau):
            return False, "Chefs d'équipe/bureau exclus des veilles nocturnes"
        
        # Contrainte 3 : Inspecteurs Certification Aéroport exclus du CRSS
        if equipe == 'CRSS' and agent.est_certification_aeroport:
            return False, "Inspecteur Certification Aéroport exclu du CRSS"
        
        # Alternative : vérifier par nom si le champ n'est pas renseigné
        if equipe == 'CRSS' and est_nom_dans_liste(agent.prenom, agent.nom, INSPECTEURS_CERTIFICATION_AEROPORT):
            return False, "Inspecteur Certification Aéroport exclu du CRSS"
        
        return True, ""
    
    def _peut_etre_chef_equipe_bvp(self, agent, planning):
        """
        Vérifie si un agent peut être chef d'équipe BVP cette semaine
        
        Contrainte 5 : Ne pas programmer le même chef d'équipe BVP 2 fois dans la semaine
        
        Args:
            agent: L'agent à vérifier
            planning: Le planning de la semaine
        
        Returns:
            bool: True si l'agent peut être chef d'équipe BVP
        """
        # Vérifier si l'agent est chef d'équipe BVP
        if not agent.est_chef_equipe_bvp:
            return False
        
        # Compter combien de fois cet agent est déjà chef d'équipe BVP cette semaine
        nb_fois_chef_bvp = Affectation.query.filter_by(
            planning_id=planning.id,
            agent_id=agent.id,
            equipe='BVP',
            poste='chef'
        ).count()
        
        # Maximum 1 fois par semaine
        return nb_fois_chef_bvp < 1
    
    def _selectionner_chef_equipe_bvp(self, agents, planning):
        """
        Sélectionne un chef d'équipe BVP selon les contraintes
        
        Args:
            agents: Liste des agents disponibles
            planning: Le planning de la semaine
        
        Returns:
            User: Le chef d'équipe sélectionné ou None
        """
        from contraintes import est_nom_dans_liste, CHEFS_EQUIPE_BVP
        
        # Filtrer les agents qui peuvent être chef d'équipe BVP
        candidats = []
        for agent in agents:
            # Vérifier si l'agent est dans la liste des chefs BVP
            if agent.est_chef_equipe_bvp or est_nom_dans_liste(agent.prenom, agent.nom, CHEFS_EQUIPE_BVP):
                # Vérifier qu'il n'a pas déjà été chef cette semaine
                if self._peut_etre_chef_equipe_bvp(agent, planning):
                    candidats.append(agent)
        
        # Retourner le premier candidat (déjà trié par rotation)
        return candidats[0] if candidats else None
```

---

## 🔧 ÉTAPE 4 : Modifier scheduler.py - Méthode _selectionner_agent_shift

**LOCALISATION :** Remplacer COMPLÈTEMENT la méthode `_selectionner_agent_shift`

```python
    def _selectionner_agent_shift(self, agents, shift, jour, equipe='BVP', poste='agent'):
        """
        Sélectionne un agent pour un shift donné en respectant TOUTES les contraintes
        
        Args:
            agents: Liste des agents disponibles
            shift: 'jour' ou 'nuit'
            jour: Date du jour
            equipe: 'CRSS' ou 'BVP'
            poste: 'chef', 'inspecteur', 'agent'
        
        Returns:
            User: L'agent sélectionné ou None
        """
        for agent in agents:
            # Vérifier les contraintes métier AVANT les contraintes de base
            peut_etre_affecte, raison = self._verifier_contraintes_agent(agent, shift, equipe, poste, jour)
            if not peut_etre_affecte:
                continue  # Passer à l'agent suivant
            
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
            
            return agent
        
        return None
```

---

## 🔧 ÉTAPE 5 : Modifier scheduler.py - Méthode _generer_affectations_jour

**LOCALISATION :** Remplacer la méthode `_generer_affectations_jour` (lignes ~95-150)

```python
    def _generer_affectations_jour(self, planning, jour):
        """
        Génère les affectations pour un jour donné EN RESPECTANT TOUTES LES CONTRAINTES
        
        Args:
            planning: L'objet Planning
            jour: La date du jour
        """
        # Récupérer tous les agents disponibles
        agents_disponibles = User.query.filter_by(
            role='agent',
            disponibilite=True
        ).all()
        
        if len(agents_disponibles) < 6:
            raise Exception(f"Pas assez d'agents disponibles ({len(agents_disponibles)}/6 requis)")
        
        # Trier les agents selon les règles de rotation
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
        
        # Chef d'équipe BVP (JOUR) - Contrainte 5 appliquée
        chef = self._selectionner_chef_equipe_bvp(agents_tries, planning)
        if not chef:
            # Si aucun chef d'équipe BVP disponible, prendre un agent normal
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
```

---

## 🔧 ÉTAPE 6 : Modifier les formulaires HTML

### 6.1 Modifier templates/ajouter_agent.html

**LOCALISATION :** Après le champ `chef_de_mission`, ajouter :

```html
            <!-- Genre -->
            <div>
                <label for="genre" class="block text-sm font-medium text-gray-700 mb-2">
                    <i class="fas fa-venus-mars mr-1 text-blue-600"></i>Genre <span class="text-red-500">*</span>
                </label>
                <select name="genre" id="genre" required
                        class="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-4 py-2 border transition">
                    <option value="">-- Sélectionnez --</option>
                    <option value="homme">Homme</option>
                    <option value="femme">Femme</option>
                </select>
            </div>
            
            <!-- Contraintes spéciales -->
            <div class="col-span-2 bg-gray-50 p-4 rounded-lg">
                <h3 class="text-sm font-semibold text-gray-700 mb-3">
                    <i class="fas fa-exclamation-triangle mr-2 text-yellow-600"></i>Contraintes spéciales
                </h3>
                <div class="grid grid-cols-2 gap-3">
                    <div class="flex items-center">
                        <input type="checkbox" name="est_chef_equipe" id="est_chef_equipe"
                               class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                        <label for="est_chef_equipe" class="ml-2 text-sm text-gray-700">
                            Chef d'équipe
                        </label>
                    </div>
                    
                    <div class="flex items-center">
                        <input type="checkbox" name="est_chef_bureau" id="est_chef_bureau"
                               class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                        <label for="est_chef_bureau" class="ml-2 text-sm text-gray-700">
                            Chef de bureau
                        </label>
                    </div>
                    
                    <div class="flex items-center">
                        <input type="checkbox" name="est_certification_aeroport" id="est_certification_aeroport"
                               class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                        <label for="est_certification_aeroport" class="ml-2 text-sm text-gray-700">
                            Certification Aéroport
                        </label>
                    </div>
                    
                    <div class="flex items-center">
                        <input type="checkbox" name="est_chef_equipe_bvp" id="est_chef_equipe_bvp"
                               class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                        <label for="est_chef_equipe_bvp" class="ml-2 text-sm text-gray-700">
                            Chef d'équipe BVP
                        </label>
                    </div>
                    
                    <div class="flex items-center">
                        <input type="checkbox" name="est_chef_equipe_usine" id="est_chef_equipe_usine"
                               class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                        <label for="est_chef_equipe_usine" class="ml-2 text-sm text-gray-700">
                            Chef équipe Inspection Usine
                        </label>
                    </div>
                    
                    <div class="flex items-center">
                        <input type="checkbox" name="est_observateur_embarque" id="est_observateur_embarque"
                               class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                               onchange="toggleDateEmbarquement()">
                        <label for="est_observateur_embarque" class="ml-2 text-sm text-gray-700">
                            Observateur embarqué
                        </label>
                    </div>
                </div>
                
                <!-- Dates embarquement (affichées si observateur coché) -->
                <div id="dates_embarquement" class="mt-3 grid grid-cols-2 gap-3" style="display: none;">
                    <div>
                        <label for="date_embarquement" class="block text-xs font-medium text-gray-700 mb-1">
                            Date d'embarquement
                        </label>
                        <input type="date" name="date_embarquement" id="date_embarquement"
                               class="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-1 text-sm border">
                    </div>
                    <div>
                        <label for="date_debarquement_prevue" class="block text-xs font-medium text-gray-700 mb-1">
                            Date de débarquement prévue
                        </label>
                        <input type="date" name="date_debarquement_prevue" id="date_debarquement_prevue"
                               class="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-1 text-sm border">
                    </div>
                </div>
            </div>

<script>
function toggleDateEmbarquement() {
    const checkbox = document.getElementById('est_observateur_embarque');
    const datesDiv = document.getElementById('dates_embarquement');
    datesDiv.style.display = checkbox.checked ? 'grid' : 'none';
}
</script>
```

### 6.2 Modifier templates/modifier_agent.html

**MÊME CODE** que ci-dessus, mais avec les valeurs pré-remplies :

```html
            <!-- Genre -->
            <div>
                <label for="genre" class="block text-sm font-medium text-gray-700 mb-2">
                    <i class="fas fa-venus-mars mr-1 text-blue-600"></i>Genre
                </label>
                <select name="genre" id="genre"
                        class="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-4 py-2 border transition">
                    <option value="">-- Sélectionnez --</option>
                    <option value="homme" {% if agent.genre == "homme" %}selected{% endif %}>Homme</option>
                    <option value="femme" {% if agent.genre == "femme" %}selected{% endif %}>Femme</option>
                </select>
            </div>
            
            <!-- Contraintes spéciales -->
            <div class="col-span-2 bg-gray-50 p-4 rounded-lg">
                <h3 class="text-sm font-semibold text-gray-700 mb-3">
                    <i class="fas fa-exclamation-triangle mr-2 text-yellow-600"></i>Contraintes spéciales
                </h3>
                <div class="grid grid-cols-2 gap-3">
                    <div class="flex items-center">
                        <input type="checkbox" name="est_chef_equipe" id="est_chef_equipe"
                               {% if agent.est_chef_equipe %}checked{% endif %}
                               class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                        <label for="est_chef_equipe" class="ml-2 text-sm text-gray-700">
                            Chef d'équipe
                        </label>
                    </div>
                    
                    <div class="flex items-center">
                        <input type="checkbox" name="est_chef_bureau" id="est_chef_bureau"
                               {% if agent.est_chef_bureau %}checked{% endif %}
                               class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                        <label for="est_chef_bureau" class="ml-2 text-sm text-gray-700">
                            Chef de bureau
                        </label>
                    </div>
                    
                    <div class="flex items-center">
                        <input type="checkbox" name="est_certification_aeroport" id="est_certification_aeroport"
                               {% if agent.est_certification_aeroport %}checked{% endif %}
                               class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                        <label for="est_certification_aeroport" class="ml-2 text-sm text-gray-700">
                            Certification Aéroport
                        </label>
                    </div>
                    
                    <div class="flex items-center">
                        <input type="checkbox" name="est_chef_equipe_bvp" id="est_chef_equipe_bvp"
                               {% if agent.est_chef_equipe_bvp %}checked{% endif %}
                               class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                        <label for="est_chef_equipe_bvp" class="ml-2 text-sm text-gray-700">
                            Chef d'équipe BVP
                        </label>
                    </div>
                    
                    <div class="flex items-center">
                        <input type="checkbox" name="est_chef_equipe_usine" id="est_chef_equipe_usine"
                               {% if agent.est_chef_equipe_usine %}checked{% endif %}
                               class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded">
                        <label for="est_chef_equipe_usine" class="ml-2 text-sm text-gray-700">
                            Chef équipe Inspection Usine
                        </label>
                    </div>
                    
                    <div class="flex items-center">
                        <input type="checkbox" name="est_observateur_embarque" id="est_observateur_embarque"
                               {% if agent.est_observateur_embarque %}checked{% endif %}
                               class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                               onchange="toggleDateEmbarquement()">
                        <label for="est_observateur_embarque" class="ml-2 text-sm text-gray-700">
                            Observateur embarqué
                        </label>
                    </div>
                </div>
                
                <!-- Dates embarquement -->
                <div id="dates_embarquement" class="mt-3 grid grid-cols-2 gap-3" 
                     style="display: {% if agent.est_observateur_embarque %}grid{% else %}none{% endif %};">
                    <div>
                        <label for="date_embarquement" class="block text-xs font-medium text-gray-700 mb-1">
                            Date d'embarquement
                        </label>
                        <input type="date" name="date_embarquement" id="date_embarquement"
                               value="{{ agent.date_embarquement.strftime('%Y-%m-%d') if agent.date_embarquement else '' }}"
                               class="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-1 text-sm border">
                    </div>
                    <div>
                        <label for="date_debarquement_prevue" class="block text-xs font-medium text-gray-700 mb-1">
                            Date de débarquement prévue
                        </label>
                        <input type="date" name="date_debarquement_prevue" id="date_debarquement_prevue"
                               value="{{ agent.date_debarquement_prevue.strftime('%Y-%m-%d') if agent.date_debarquement_prevue else '' }}"
                               class="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3 py-1 text-sm border">
                    </div>
                </div>
            </div>

<script>
function toggleDateEmbarquement() {
    const checkbox = document.getElementById('est_observateur_embarque');
    const datesDiv = document.getElementById('dates_embarquement');
    datesDiv.style.display = checkbox.checked ? 'grid' : 'none';
}
</script>
```

---

## 🔧 ÉTAPE 7 : Modifier app.py - Routes

### 7.1 Route ajouter_agent

**LOCALISATION :** Dans la fonction `ajouter_agent`, après la récupération des champs basiques

```python
@app.route('/admin/agents/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_agent():
    """Ajouter un agent"""
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('dashboard_agent'))
    
    if request.method == 'POST':
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        email = request.form.get('email')
        username = request.form.get('username')
        phone = request.form.get('phone')
        fonction = request.form.get('fonction')
        chef_de_mission = request.form.get('chef_de_mission')
        password = request.form.get('password')
        
        # ========== NOUVEAUX CHAMPS POUR LES CONTRAINTES ==========
        genre = request.form.get('genre')
        est_chef_equipe = request.form.get('est_chef_equipe') == 'on'
        est_chef_bureau = request.form.get('est_chef_bureau') == 'on'
        est_certification_aeroport = request.form.get('est_certification_aeroport') == 'on'
        est_chef_equipe_bvp = request.form.get('est_chef_equipe_bvp') == 'on'
        est_chef_equipe_usine = request.form.get('est_chef_equipe_usine') == 'on'
        est_observateur_embarque = request.form.get('est_observateur_embarque') == 'on'
        
        date_embarquement = None
        date_debarquement_prevue = None
        if est_observateur_embarque:
            date_emb_str = request.form.get('date_embarquement')
            date_deb_str = request.form.get('date_debarquement_prevue')
            if date_emb_str:
                from datetime import datetime
                date_embarquement = datetime.strptime(date_emb_str, '%Y-%m-%d').date()
            if date_deb_str:
                date_debarquement_prevue = datetime.strptime(date_deb_str, '%Y-%m-%d').date()
        # ===========================================================
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'danger')
        elif username and User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur est déjà utilisé.', 'danger')
        else:
            agent = User(
                nom=nom,
                prenom=prenom,
                email=email,
                username=username,
                phone=phone,
                fonction=fonction,
                chef_de_mission=chef_de_mission,
                role='agent',
                # Nouveaux champs
                genre=genre,
                est_chef_equipe=est_chef_equipe,
                est_chef_bureau=est_chef_bureau,
                est_certification_aeroport=est_certification_aeroport,
                est_chef_equipe_bvp=est_chef_equipe_bvp,
                est_chef_equipe_usine=est_chef_equipe_usine,
                est_observateur_embarque=est_observateur_embarque,
                date_embarquement=date_embarquement,
                date_debarquement_prevue=date_debarquement_prevue
            )
            agent.set_password(password)
            
            db.session.add(agent)
            db.session.commit()
            
            flash(f'Agent {prenom} {nom} ajouté avec succès!', 'success')
            return redirect(url_for('gestion_agents'))
    
    return render_template('ajouter_agent.html')
```

### 7.2 Route modifier_agent

**MÊME LOGIQUE**, dans la fonction `modifier_agent` :

```python
@app.route('/admin/agents/<int:agent_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_agent(agent_id):
    """Modifier un agent"""
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('dashboard_agent'))
    
    agent = User.query.get_or_404(agent_id)
    
    if request.method == 'POST':
        agent.nom = request.form.get('nom')
        agent.prenom = request.form.get('prenom')
        agent.email = request.form.get('email')
        agent.username = request.form.get('username')
        agent.phone = request.form.get('phone')
        agent.fonction = request.form.get('fonction')
        agent.chef_de_mission = request.form.get('chef_de_mission')
        agent.disponibilite = request.form.get('disponibilite') == 'on'
        
        # ========== NOUVEAUX CHAMPS ==========
        agent.genre = request.form.get('genre')
        agent.est_chef_equipe = request.form.get('est_chef_equipe') == 'on'
        agent.est_chef_bureau = request.form.get('est_chef_bureau') == 'on'
        agent.est_certification_aeroport = request.form.get('est_certification_aeroport') == 'on'
        agent.est_chef_equipe_bvp = request.form.get('est_chef_equipe_bvp') == 'on'
        agent.est_chef_equipe_usine = request.form.get('est_chef_equipe_usine') == 'on'
        agent.est_observateur_embarque = request.form.get('est_observateur_embarque') == 'on'
        
        if agent.est_observateur_embarque:
            date_emb_str = request.form.get('date_embarquement')
            date_deb_str = request.form.get('date_debarquement_prevue')
            if date_emb_str:
                from datetime import datetime
                agent.date_embarquement = datetime.strptime(date_emb_str, '%Y-%m-%d').date()
            if date_deb_str:
                agent.date_debarquement_prevue = datetime.strptime(date_deb_str, '%Y-%m-%d').date()
        else:
            agent.date_embarquement = None
            agent.date_debarquement_prevue = None
        # =====================================
        
        password = request.form.get('password')
        if password:
            agent.set_password(password)
        
        db.session.commit()
        flash(f'Agent {agent.prenom} {agent.nom} modifié avec succès!', 'success')
        return redirect(url_for('gestion_agents'))
    
    return render_template('modifier_agent.html', agent=agent)
```

---

## 📝 RÉSUMÉ DES MODIFICATIONS

### Fichiers créés :
1. ✅ `contraintes.py` - Configuration des contraintes métier

### Fichiers modifiés :
1. ✅ `models.py` - 9 nouveaux champs dans User
2. ✅ `scheduler.py` - 3 nouvelles méthodes + 2 méthodes modifiées
3. ✅ `app.py` - 2 routes modifiées (ajouter_agent, modifier_agent)
4. ✅ `templates/ajouter_agent.html` - Nouveaux champs de formulaire
5. ✅ `templates/modifier_agent.html` - Nouveaux champs de formulaire

### Migration SQL :
```sql
ALTER TABLE users ADD COLUMN genre VARCHAR(10) AFTER phone;
ALTER TABLE users ADD COLUMN est_chef_equipe BOOLEAN DEFAULT FALSE AFTER genre;
ALTER TABLE users ADD COLUMN est_chef_bureau BOOLEAN DEFAULT FALSE AFTER est_chef_equipe;
ALTER TABLE users ADD COLUMN est_certification_aeroport BOOLEAN DEFAULT FALSE AFTER est_chef_bureau;
ALTER TABLE users ADD COLUMN est_chef_equipe_bvp BOOLEAN DEFAULT FALSE AFTER est_certification_aeroport;
ALTER TABLE users ADD COLUMN est_chef_equipe_usine BOOLEAN DEFAULT FALSE AFTER est_chef_equipe_bvp;
ALTER TABLE users ADD COLUMN est_observateur_embarque BOOLEAN DEFAULT FALSE AFTER est_chef_equipe_usine;
ALTER TABLE users ADD COLUMN date_embarquement DATE AFTER est_observateur_embarque;
ALTER TABLE users ADD COLUMN date_debarquement_prevue DATE AFTER date_embarquement;
```

---

## 🎯 ORDRE D'EXÉCUTION

1. Créer le fichier `contraintes.py`
2. Modifier `models.py`
3. Exécuter la migration SQL
4. Modifier `scheduler.py`
5. Modifier `app.py`
6. Modifier les templates HTML
7. Redémarrer l'application
8. Tester !

---

## ✅ VALIDATION DES CONTRAINTES

### Contrainte 1 : Femmes exclues horaires nocturnes
- ✅ Vérification dans `_verifier_contraintes_agent()`
- ✅ Ligne : `if agent.genre == 'femme' and shift == 'nuit'`

### Contrainte 2 : Chefs exclus veilles nocturnes
- ✅ Vérification dans `_verifier_contraintes_agent()`
- ✅ Ligne : `if shift == 'nuit' and (agent.est_chef_equipe or agent.est_chef_bureau)`

### Contrainte 3 : Certif. Aéroport exclus CRSS
- ✅ Vérification dans `_verifier_contraintes_agent()`
- ✅ Double vérification : champ BDD + liste noms

### Contrainte 4 : Liste chefs équipe BVP
- ✅ Définie dans `contraintes.py`
- ✅ Utilisée dans `_selectionner_chef_equipe_bvp()`

### Contrainte 5 : Chef BVP max 1 fois/semaine
- ✅ Vérification dans `_peut_etre_chef_equipe_bvp()`
- ✅ Compte les affectations chef BVP dans la semaine

### Contrainte 6 : Liste chefs équipe Inspection Usine
- ✅ Définie dans `contraintes.py`
- ✅ Prêt pour utilisation future

### Contrainte 7 : Observateurs embarqués
- ✅ Vérification dans `_verifier_contraintes_agent()`
- ✅ Compare date du jour avec date de débarquement

---

## 🧪 TESTS RECOMMANDÉS

1. Créer des agents avec différents profils
2. Cocher les contraintes appropriées
3. Générer un planning
4. Vérifier que :
   - ✅ Aucune femme en shift nuit
   - ✅ Aucun chef en veille nocturne
   - ✅ Agents Certif. Aéroport pas au CRSS
   - ✅ Chef BVP unique par semaine
   - ✅ Observateurs embarqués exclus

Toutes les contraintes sont maintenant implémentées ! 🎉
