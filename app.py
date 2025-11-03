import base64
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, date
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from config import Config
from models import db, User, Planning, Affectation, HistoriqueModification
from scheduler import PlanningScheduler

# Initialiser l'application Flask
app = Flask(__name__)
app.config.from_object(Config)
application = app  

# Initialiser les extensions
db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

# Initialiser le scheduler
scheduler_manager = PlanningScheduler(app, mail)
scheduler = BackgroundScheduler()


@login_manager.user_loader
def load_user(user_id):
    """Charge un utilisateur depuis la base de données"""
    return User.query.get(int(user_id))


# ==================== ROUTES D'AUTHENTIFICATION ====================

@app.route('/')
def index():
    """Page d'accueil - redirige vers le dashboard approprié"""
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('dashboard_admin'))
        else:
            return redirect(url_for('dashboard_agent'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            
            flash(f'Bienvenue {user.prenom} !', 'success')
            
            if next_page:
                return redirect(next_page)
            elif user.role == 'admin':
                return redirect(url_for('dashboard_admin'))
            else:
                return redirect(url_for('dashboard_agent'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription (réservée aux admins ou première installation)"""
    premier_utilisateur = User.query.count() == 0
    
    if not premier_utilisateur and (not current_user.is_authenticated or current_user.role != 'admin'):
        flash('Seuls les administrateurs peuvent créer des comptes.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username')
        phone = request.form.get('phone')
        fonction = request.form.get('fonction')
        chef_de_mission = request.form.get('chef_de_mission')
        role = request.form.get('role', 'agent')
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'danger')
        elif username and User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur est déjà utilisé.', 'danger')
        else:
            if premier_utilisateur:
                role = 'admin'
            
            user = User(
                nom=nom,
                prenom=prenom,
                email=email,
                username=username,
                phone=phone,
                fonction=fonction,
                chef_de_mission=chef_de_mission,
                role=role
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'Compte créé avec succès pour {prenom} {nom}!', 'success')
            
            if premier_utilisateur:
                login_user(user)
                return redirect(url_for('dashboard_admin'))
            else:
                return redirect(url_for('gestion_agents'))
    
    return render_template('register.html', premier_utilisateur=premier_utilisateur)


@app.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous êtes déconnecté.', 'info')
    return redirect(url_for('login'))


# ==================== DASHBOARD ADMIN ====================

@app.route('/admin/dashboard')
@login_required
def dashboard_admin():
    """Dashboard administrateur"""
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('dashboard_agent'))
    
    # Statistiques
    nb_agents = User.query.filter_by(role='agent').count()
    nb_agents_disponibles = User.query.filter_by(role='agent', disponibilite=True).count()
    
    # Planning actuel
    aujourd_hui = date.today()
    planning_actuel = Planning.query.filter(
        Planning.date_debut <= aujourd_hui,
        Planning.date_fin >= aujourd_hui
    ).first()
    
    # Plannings récents
    plannings_recents = Planning.query.order_by(Planning.date_debut.desc()).limit(5).all()
    
    return render_template('dashboard_admin.html',
                         nb_agents=nb_agents,
                         nb_agents_disponibles=nb_agents_disponibles,
                         planning_actuel=planning_actuel,
                         plannings_recents=plannings_recents)


# ==================== DASHBOARD AGENT ====================

@app.route('/agent/dashboard')
@login_required
def dashboard_agent():
    """Dashboard agent"""
    aujourd_hui = date.today()
    planning_actuel = Planning.query.filter(
        Planning.date_debut <= aujourd_hui,
        Planning.date_fin >= aujourd_hui
    ).first()
    
    affectations_semaine = []
    if planning_actuel:
        affectations_semaine = Affectation.query.filter_by(
            planning_id=planning_actuel.id,
            agent_id=current_user.id
        ).order_by(Affectation.jour).all()
    
    total_jours = current_user.compteur_jour
    total_nuits = current_user.compteur_nuit
    
    return render_template('dashboard_agent.html',
                         planning_actuel=planning_actuel,
                         affectations_semaine=affectations_semaine,
                         total_jours=total_jours,
                         total_nuits=total_nuits, 
                         timedelta=timedelta)


# ==================== GESTION DES AGENTS ====================

@app.route('/admin/agents')
@login_required
def gestion_agents():
    """Liste paginée des agents"""
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('dashboard_agent'))
    
    # Récupère le numéro de page depuis l’URL (par défaut 1)
    page = request.args.get('page', 1, type=int)
    per_page = 10  # nombre d'agents par page (modifiable)
    
    # Pagination
    pagination = User.query.filter_by(role='agent').paginate(page=page, per_page=per_page)
    agents = pagination.items  # agents de la page courante
    all_agents = User.query.filter_by(role='agent').all()
    
    return render_template('gestion_agents.html', agents=agents, pagination=pagination, all_agents=all_agents)


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
        username = request.form.get('username') or None
        email = request.form.get('email') or ''
        phone = request.form.get('phone') or ''
        password = request.form.get('password') or 'defaultpassword'
        fonction = request.form.get('fonction')
        chef_de_mission = request.form.get('chef_de_mission') or ''
        
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
                from datetime import datetime as dt
                date_embarquement = dt.strptime(date_emb_str, '%Y-%m-%d').date()
            if date_deb_str:
                date_debarquement_prevue = dt.strptime(date_deb_str, '%Y-%m-%d').date()
        # ===========================================================

        if username and User.query.filter_by(username=username).first():
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
                # Nouveaux champs contraintes
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
        agent.username = request.form.get('username') or None
        agent.phone = request.form.get('phone') or ''
        agent.email = request.form.get('email') or ''
        agent.fonction = request.form.get('fonction') 
        agent.chef_de_mission = request.form.get('chef_de_mission')
        agent.disponibilite = request.form.get('disponibilite') == 'on'
        
        # ========== NOUVEAUX CHAMPS CONTRAINTES ==========
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
                from datetime import datetime as dt
                agent.date_embarquement = dt.strptime(date_emb_str, '%Y-%m-%d').date()
            if date_deb_str:
                agent.date_debarquement_prevue = dt.strptime(date_deb_str, '%Y-%m-%d').date()
        else:
            agent.date_embarquement = None
            agent.date_debarquement_prevue = None
        # =================================================
        
        password = request.form.get('password')
        if password:
            agent.set_password(password)
        
        db.session.commit()
        flash(f'Agent {agent.prenom} {agent.nom} modifié avec succès!', 'success')
        return redirect(url_for('gestion_agents'))
    
    return render_template('modifier_agent.html', agent=agent)


@app.route('/admin/agents/<int:agent_id>/supprimer', methods=['POST'])
@login_required
def supprimer_agent(agent_id):
    """Supprimer un agent"""
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('dashboard_agent'))
    
    agent = User.query.get_or_404(agent_id)
    nom_complet = agent.nom_complet
    
    db.session.delete(agent)
    db.session.commit()
    
    flash(f'Agent {nom_complet} supprimé avec succès!', 'success')
    return redirect(url_for('gestion_agents'))


# ==================== GESTION DES PLANNINGS ====================

@app.route('/admin/plannings')
@login_required
def liste_plannings():
    """Liste de tous les plannings"""
    if current_user.role != 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('dashboard_agent'))
    
    plannings = Planning.query.order_by(Planning.date_debut.desc()).all()
    return render_template('liste_plannings.html', plannings=plannings)


@app.route('/admin/plannings/<int:planning_id>')
@login_required
def voir_planning(planning_id):
    """Voir un planning détaillé"""
    planning = Planning.query.get_or_404(planning_id)
    
    affectations_par_jour = {}
    jours_semaine = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    
    for i in range(7):
        jour = planning.date_debut + timedelta(days=i)
        affectations_jour = Affectation.query.filter_by(
            planning_id=planning.id,
            jour=jour
        ).all()
        
        affectations_par_jour[jours_semaine[i]] = {
            'date': jour,
            'affectations': affectations_jour
        }
    
    return render_template('voir_planning.html', 
                         planning=planning,
                         affectations_par_jour=affectations_par_jour,
                         jours_semaine=jours_semaine)


@app.route('/admin/plannings/generer', methods=['POST'])
@login_required
def generer_planning():
    """Générer automatiquement un nouveau planning"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    try:
        planning = scheduler_manager.generer_planning_semaine()
        flash(f'Planning genere pour la semaine du {planning.date_debut.strftime("%d/%m/%Y")}!', 'success')
        return redirect(url_for('voir_planning', planning_id=planning.id))
    except Exception as e:
        flash(f'Erreur lors de la génération du planning: {str(e)}', 'danger')
        return redirect(url_for('dashboard_admin'))


@app.route('/admin/plannings/<int:planning_id>/archiver', methods=['POST'])
@login_required
def archiver_planning(planning_id):
    """Archiver un planning"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    planning = Planning.query.get_or_404(planning_id)
    planning.statut = 'archive'
    db.session.commit()
    
    flash('Planning archivé avec succès!', 'success')
    return redirect(url_for('liste_plannings'))


# ==================== EXPORT ====================

@app.route('/admin/plannings/<int:planning_id>/export/pdf')
@login_required
def export_planning_pdf(planning_id):
    """Exporter un planning en PDF avec en-tête institutionnel"""
    planning = Planning.query.get_or_404(planning_id)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    
    styles = getSampleStyleSheet()
    style_center = ParagraphStyle(name='center', alignment=TA_CENTER, fontSize=10, leading=12)
    style_title = styles['Title']

    logo_img = None
    sig_img = None
    try:
        with open("static/img/dpsp.png", "rb") as f:
            logo_bytes = f.read()
            logo_img = Image(BytesIO(logo_bytes))
            logo_img.drawHeight = 40
            logo_img.drawWidth = 40
    except Exception:
        logo_img = None

    try:
        with open("static/img/senegal.jpg", "rb") as f:
            sig_bytes = f.read()
            sig_img = Image(BytesIO(sig_bytes))
            sig_img.drawHeight = 22
            sig_img.drawWidth = 22
    except Exception:
        sig_img = None

    haut_text = (
        "<strong>République du Sénégal</strong><br/>"
        "<em>Un Peuple – Un But – Une Foi</em><br/>"
    )
    haut_para = Paragraph(haut_text, style_center)

    bas_text = (
        "★★★★★<br/>"
        "MINISTÈRE DES PÊCHES ET<br/>DE L'ÉCONOMIE MARITIME<br/>"
        "★★★★★<br/>Direction de la Protection et de la<br/>Surveillance des Pêches (DPSP)"
    )
    bas_para = Paragraph(bas_text, style_center)

    if sig_img:
        gauche_col = Table(
            [[haut_para], [sig_img], [bas_para]],
            colWidths=[doc.width/3 - 10]
        )
        gauche_col.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('BOX', (0,0), (-1,-1), 0, colors.white)
        ]))
    else:
        gauche_col = Paragraph(haut_text + "★★★★★<br/>" + bas_text, style_center)

    centre_vide = Paragraph("", style_center)

    if logo_img:
        droite_col = Table([[logo_img]], colWidths=[doc.width/3 - 10])
        droite_col.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOX', (0,0), (-1,-1), 0, colors.white)
        ]))
    else:
        droite_col = Paragraph("", style_center)

    entete_table = Table(
        [[gauche_col, centre_vide, droite_col]],
        colWidths=[doc.width/3, doc.width/3, doc.width/3]
    )
    entete_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0, colors.white)
    ]))

    elements.append(entete_table)
    elements.append(Spacer(1, 10))

    titre = Paragraph(
        f"<b>Planning Semaine {planning.semaine}/{planning.annee}</b><br/>{planning.periode}",
        style_title
    )
    elements.append(titre)
    elements.append(Spacer(1, 12))

    jours_semaine = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    data = [['Agent'] + jours_semaine]
    
    agents = db.session.query(User).join(Affectation).filter(
        Affectation.planning_id == planning.id
    ).distinct().all()
    
    for agent in agents:
        row = [agent.nom_complet]
        for i in range(7):
            jour = planning.date_debut + timedelta(days=i)
            aff = Affectation.query.filter_by(
                planning_id=planning.id,
                agent_id=agent.id,
                jour=jour
            ).first()
            
            if aff:
                cell_text = f"{aff.shift.upper()}\n{aff.equipe}\n{aff.horaire}"
            else:
                cell_text = "Repos"
            row.append(cell_text)
        data.append(row)
    
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=planning_semaine_{planning.semaine}_{planning.annee}.pdf'
    return response
    
    # buffer.seek(0)
    # pdf_bytes = buffer.getvalue()
    

    # return send_file(
    #     BytesIO(pdf_bytes),
    #     as_attachment=True,
    #     download_name=f'planning_semaine_{planning.semaine}_{planning.annee}.pdf',
    #     mimetype='application/pdf'
    # )


@app.route('/admin/plannings/<int:planning_id>/export/excel')
@login_required
def export_planning_excel(planning_id):
    """Exporter un planning en Excel"""
    planning = Planning.query.get_or_404(planning_id)
    
    wb = Workbook()
    ws = wb.active
    ws.title = f"Semaine {planning.semaine}"
    
    jours_semaine = ['Agent', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    ws.append(jours_semaine)
    
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal='center')
    
    agents = db.session.query(User).join(Affectation).filter(
        Affectation.planning_id == planning.id
    ).distinct().all()
    
    for agent in agents:
        row = [agent.nom_complet]
        for i in range(7):
            jour = planning.date_debut + timedelta(days=i)
            aff = Affectation.query.filter_by(
                planning_id=planning.id,
                agent_id=agent.id,
                jour=jour
            ).first()
            
            if aff:
                cell_text = f"{aff.shift.upper()} - {aff.equipe}\n{aff.horaire}"
            else:
                cell_text = "Repos"
            
            row.append(cell_text)
        
        ws.append(row)
    
    for column in ws.columns:
        max_length = 0
        column = [cell for cell in column]
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column[0].column_letter].width = adjusted_width
    
    # Sauvegarder dans BytesIO
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    # Utiliser make_response pour éviter fileno
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename=planning_semaine_{planning.semaine}_{planning.annee}.xlsx'
    
    return response

# ==================== TÂCHES PLANIFIÉES ====================

def job_generation_automatique():
    """Job qui génère automatiquement le planning chaque dimanche"""
    print(f"[{datetime.now()}] Démarrage de la génération automatique du planning...")
    try:
        planning = scheduler_manager.generer_planning_semaine()
        print(f"[{datetime.now()}] Planning généré avec succès: Semaine {planning.semaine}/{planning.annee}")
    except Exception as e:
        print(f"[{datetime.now()}] Erreur lors de la génération automatique: {str(e)}")


# ==================== INITIALISATION ====================

@app.cli.command()
def init_db():
    """Initialise la base de données"""
    db.create_all()
    print("Base de données initialisée!")


@app.cli.command()
def create_admin():
    """Crée un compte administrateur"""
    email = input("Email: ")
    password = input("Mot de passe: ")
    nom = input("Nom: ")
    prenom = input("Prénom: ")
    
    if User.query.filter_by(email=email).first():
        print("Cet email existe déjà!")
        return
    
    admin = User(
        email=email,
        nom=nom,
        prenom=prenom,
        role='admin'
    )
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    print(f"Administrateur {prenom} {nom} créé avec succès!")


@app.cli.command()
def create_sample_agents():
    """Crée des agents de test"""
    agents_data = [
        {"nom": "Diop", "prenom": "Mamadou", "email": "mamadou.diop@example.com"},
        {"nom": "Ndiaye", "prenom": "Fatou", "email": "fatou.ndiaye@example.com"},
        {"nom": "Sow", "prenom": "Ibrahima", "email": "ibrahima.sow@example.com"},
        {"nom": "Fall", "prenom": "Aissatou", "email": "aissatou.fall@example.com"},
        {"nom": "Ba", "prenom": "Moussa", "email": "moussa.ba@example.com"},
        {"nom": "Gueye", "prenom": "Aminata", "email": "aminata.gueye@example.com"},
        {"nom": "Sarr", "prenom": "Omar", "email": "omar.sarr@example.com"},
        {"nom": "Sy", "prenom": "Khady", "email": "khady.sy@example.com"},
    ]
    
    for data in agents_data:
        if not User.query.filter_by(email=data["email"]).first():
            agent = User(
                nom=data["nom"],
                prenom=data["prenom"],
                email=data["email"],
                role='agent',
                disponibilite=True
            )
            agent.set_password("password123")
            db.session.add(agent)
    
    db.session.commit()
    print(f"{len(agents_data)} agents créés avec succès!")


if __name__ == '__main__':
    scheduler.add_job(
        func=job_generation_automatique,
        trigger='cron',
        day_of_week='sun',
        hour=20,
        minute=00,
        id='generation_planning_hebdomadaire'
    )
    
    scheduler.start()
    
    print("Scheduler démarré - Génération automatique chaque dimanche à 20h00")
    
    app.run(debug=True, use_reloader=False)