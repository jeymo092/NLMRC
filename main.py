from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mwangaza.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Add custom filter for strftime
@app.template_filter('strftime')
def strftime_filter(date, format='%Y-%m-%d'):
    return date.strftime(format)

# Add current year to template context
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Client Model
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(100), nullable=False)
    secondName = db.Column(db.String(100), nullable=False)
    dateOfBirth = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    nickname = db.Column(db.String(100))
    admissionType = db.Column(db.String(20), nullable=False, default='STREET')
    referralInstitution = db.Column(db.String(200))
    referralContact = db.Column(db.String(50))
    streetName = db.Column(db.String(200))
    parentGuardianName = db.Column(db.String(200))
    parentGuardianLocation = db.Column(db.String(200))
    parentGuardianContact = db.Column(db.String(50))
    intake = db.Column(db.Integer, default=0)
    educationLevel = db.Column(db.String(100))
    grade = db.Column(db.String(20))
    secondaryForm = db.Column(db.String(20))
    status = db.Column(db.String(30), nullable=False, default='ACTIVE')
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationship to aftercare records
    aftercare_records = db.relationship('AfterCare', backref='client', lazy=True)

    # Relationship to home visits
    home_visits = db.relationship('HomeVisit', backref='client', lazy=True)

    # Relationship to student marks
    student_marks = db.relationship('StudentMark', backref='client', lazy=True)

# AfterCare Model
class AfterCare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='IN_PROGRESS')  # SUCCESSFUL, IN_PROGRESS, RELAPSED, ABSCONDED
    placement = db.Column(db.String(200))
    institution = db.Column(db.String(200))
    contact_person = db.Column(db.String(200))
    contact_phone = db.Column(db.String(50))
    placement_date = db.Column(db.Date)
    placement_completion_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'))

# HomeVisit Model
class HomeVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    conductedBy = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    report = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'))

# Subject Model
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationship to student marks
    student_marks = db.relationship('StudentMark', backref='subject', lazy=True)

# StudentMark Model
class StudentMark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False, default=100)
    test_date = db.Column(db.Date, nullable=False)
    term = db.Column(db.String(20), nullable=False)  # Term 1, Term 2, Term 3
    year = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    clients = Client.query.all()

    # Calculate comprehensive statistics
    total_clients = len(clients)
    active_clients = Client.query.filter_by(status='ACTIVE').count()
    completed_clients = Client.query.filter_by(status='COMPLETE').count()
    street_clients = Client.query.filter_by(admissionType='STREET').count()
    referral_clients = Client.query.filter_by(admissionType='REFERRAL').count()

    # Home visit statistics (only for active clients)
    total_home_visits = HomeVisit.query.join(Client).filter(Client.status == 'ACTIVE').count()
    recent_home_visits = HomeVisit.query.join(Client).filter(
        Client.status == 'ACTIVE',
        HomeVisit.createdAt >= datetime.now() - timedelta(days=30)
    ).count()

    # Aftercare statistics
    total_aftercare_records = AfterCare.query.count()
    successful_aftercare = AfterCare.query.filter_by(status='SUCCESSFUL').count()
    in_progress_aftercare = AfterCare.query.filter_by(status='IN_PROGRESS').count()

    # Age demographics (updated for 14-18 target range)
    age_groups = {
        'under_15': Client.query.filter(Client.age < 14).count(),  # Outside range (too young)
        '15_to_18': Client.query.filter(Client.age >= 14, Client.age <= 18).count(),  # Target group
        '19_to_25': Client.query.filter(Client.age >= 19, Client.age <= 25).count(),  # Outside range (too old)
        'over_25': Client.query.filter(Client.age > 18).count()  # Outside range (too old)
    }

    # Monthly registration trends (last 6 months)
    monthly_registrations = []
    for i in range(6):
        month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
        if i == 0:
            month_end = datetime.now()
        else:
            month_end = month_start + timedelta(days=31)
            month_end = month_end.replace(day=1) - timedelta(days=1)

        count = Client.query.filter(
            Client.createdAt >= month_start,
            Client.createdAt <= month_end
        ).count()

        monthly_registrations.append({
            'month': month_start.strftime('%B %Y'),
            'count': count
        })

    monthly_registrations.reverse()  # Show oldest to newest

    # Department-specific statistics
    department_stats = {}

    # Social Workers specific stats
    if current_user.department == 'socialworkers':
        clients_needing_aftercare = Client.query.filter_by(status='COMPLETE').filter(
            ~Client.id.in_(db.session.query(AfterCare.client_id))
        ).count()

        # Aftercare specific stats
        relapsed_clients = AfterCare.query.filter_by(status='RELAPSED').count()
        absconded_clients = AfterCare.query.filter_by(status='ABSCONDED').count()

        # Recent activities
        recent_completions = Client.query.filter(
            Client.status == 'COMPLETE',
            Client.createdAt >= datetime.now() - timedelta(days=30)
        ).count()

        # Current intake (active clients with intake numbers)
        current_intake = Client.query.filter(
            Client.status == 'ACTIVE',
            Client.intake > 0
        ).count()

        # Active clients with recent home visits (last 30 days)
        recent_visits_clients = db.session.query(HomeVisit.client_id).join(Client).filter(
            Client.status == 'ACTIVE',
            HomeVisit.createdAt >= datetime.now() - timedelta(days=30)
        ).distinct().count()

        # Get recent home visits with client details for display
        recent_home_visits_details = HomeVisit.query.join(Client).filter(
            HomeVisit.createdAt >= datetime.now() - timedelta(days=7),
            Client.status == 'ACTIVE'
        ).order_by(HomeVisit.createdAt.desc()).limit(5).all()

        department_stats.update({
            'clients_needing_aftercare': clients_needing_aftercare,
            'total_home_visits': total_home_visits,
            'recent_home_visits': recent_home_visits,
            'relapsed_clients': relapsed_clients,
            'absconded_clients': absconded_clients,
            'recent_completions': recent_completions,
            'current_intake': current_intake,
            'recent_visits_clients': recent_visits_clients,
            'recent_home_visits_details': recent_home_visits_details
        })

    # Education department specific stats
    elif current_user.department == 'education':
        subjects = Subject.query.all()
        total_assessments = StudentMark.query.count()

        # Calculate average performance
        all_marks = StudentMark.query.all()
        if all_marks:
            total_percentage = sum((mark.marks / mark.max_marks) * 100 for mark in all_marks)
            average_performance = round(total_percentage / len(all_marks), 1)
        else:
            average_performance = 0

        # Education specific metrics
        students_with_assessments = len(set(mark.client_id for mark in all_marks))
        students_without_assessments = active_clients - students_with_assessments

        # Recent assessments
        recent_assessments = StudentMark.query.filter(
            StudentMark.createdAt >= datetime.now() - timedelta(days=30)
        ).count()

        # Performance trends
        high_performers = StudentMark.query.filter(
            (StudentMark.marks / StudentMark.max_marks) >= 0.75
        ).count()

        department_stats.update({
            'subjects': subjects,
            'total_assessments': total_assessments,
            'average_performance': average_performance,
            'students_with_assessments': students_with_assessments,
            'students_without_assessments': students_without_assessments,
            'recent_assessments': recent_assessments,
            'high_performers': high_performers
        })

    # Counselling department specific stats
    elif current_user.department == 'counselling':
        # Counselling specific metrics
        new_admissions_this_month = Client.query.filter(
            Client.createdAt >= datetime.now().replace(day=1)
        ).count()

        long_term_clients = Client.query.filter(
            Client.status == 'ACTIVE',
            Client.createdAt <= datetime.now() - timedelta(days=365)
        ).count()

        young_clients = Client.query.filter(Client.age <= 15).count()
        adolescent_clients = Client.query.filter(Client.age >= 16, Client.age <= 18).count()

        department_stats.update({
            'new_admissions_this_month': new_admissions_this_month,
            'long_term_clients': long_term_clients,
            'young_clients': young_clients,
            'adolescent_clients': adolescent_clients,
            'clients_needing_assessment': active_clients  # Assuming all active clients need counselling assessment
        })

    # Empowerment department specific stats
    elif current_user.department == 'empowerment':
        # Empowerment/Life skills specific metrics
        clients_over_18 = Client.query.filter(Client.age >= 18, Client.status == 'ACTIVE').count()
        clients_15_to_17 = Client.query.filter(Client.age >= 15, Client.age <= 17, Client.status == 'ACTIVE').count()

        # Clients ready for programs
        vocational_ready = Client.query.filter(
            Client.age >= 16,
            Client.status == 'ACTIVE'
        ).count()

        life_skills_ready = Client.query.filter(
            Client.age >= 14,
            Client.status == 'ACTIVE'
        ).count()

        department_stats.update({
            'clients_over_18': clients_over_18,
            'clients_15_to_17': clients_15_to_17,
            'vocational_ready': vocational_ready,
            'life_skills_ready': life_skills_ready,
            'potential_graduates': completed_clients  # Those who completed programs
        })

    # Admin gets comprehensive statistics from all departments
    elif current_user.department == 'admin':
        clients_needing_aftercare = Client.query.filter_by(status='COMPLETE').filter(
            ~Client.id.in_(db.session.query(AfterCare.client_id))
        ).count()

        # System-wide metrics
        total_assessments = StudentMark.query.count()
        subjects = Subject.query.all()

        department_stats.update({
            'total_home_visits': total_home_visits,
            'recent_home_visits': recent_home_visits,
            'clients_needing_aftercare': clients_needing_aftercare,
            'subjects': subjects,
            'total_assessments': total_assessments,
            'system_users': User.query.count(),
            'database_records': total_clients + total_home_visits + total_aftercare_records + total_assessments
        })

    statistics = {
        'total_clients': total_clients,
        'active_clients': active_clients,
        'completed_clients': completed_clients,
        'street_clients': street_clients,
        'referral_clients': referral_clients,
        'total_aftercare_records': total_aftercare_records,
        'successful_aftercare': successful_aftercare,
        'in_progress_aftercare': in_progress_aftercare,
        'age_groups': age_groups,
        'monthly_registrations': monthly_registrations
    }

    return render_template('dashboard.html', 
                         clients=clients, 
                         user=current_user, 
                         statistics=statistics,
                         **department_stats)

@app.route('/register_client', methods=['GET', 'POST'])
@login_required
def register_client():
    # Only Admin and Social Workers can register new clients
    if current_user.department not in ['admin', 'socialworkers']:
        flash('Access denied. Only Admin and Social Workers can register new clients.')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        try:
            # Parse date of birth
            dob = datetime.strptime(request.form['dateOfBirth'], '%Y-%m-%d').date()
            age = int(request.form['age'])

            # Validate age range (14-18 years)
            if age < 14 or age > 18:
                flash(f'Client age must be between 14 and 18 years. Current age: {age} years.')
                return render_template('register_client.html')

            client = Client(
                firstName=request.form['firstName'],
                secondName=request.form['secondName'],
                dateOfBirth=dob,
                age=int(request.form['age']),
                nickname=request.form.get('nickname', ''),
                admissionType=request.form['admissionType'],
                referralInstitution=request.form.get('referralInstitution', ''),
                referralContact=request.form.get('referralContact', ''),
                streetName=request.form.get('streetName', ''),
                parentGuardianName=request.form.get('parentGuardianName', ''),
                parentGuardianLocation=request.form.get('parentGuardianLocation', ''),
                parentGuardianContact=request.form.get('parentGuardianContact', ''),
                intake=int(request.form.get('intake', 0)),
                educationLevel=request.form.get('educationLevel', ''),
                grade=request.form.get('grade', ''),
                secondaryForm=request.form.get('secondaryForm', ''),
                status=request.form.get('status', 'ACTIVE'),
                createdBy=current_user.id
            )

            db.session.add(client)
            db.session.commit()
            flash('Client registered successfully!')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Error registering client: {str(e)}')

    return render_template('register_client.html')

@app.route('/client/<int:client_id>')
@login_required
def view_client(client_id):
    client = Client.query.get_or_404(client_id)
    has_home_visits = HomeVisit.query.filter_by(client_id=client_id).count() > 0  # Check if client has home visits
    return render_template('client_detail.html', client=client, has_home_visits=has_home_visits)

@app.route('/client/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    # Only Admin and Social Workers can edit clients
    if current_user.department not in ['admin', 'socialworkers']:
        flash('Access denied. Only Admin and Social Workers can edit client information.')
        return redirect(url_for('view_client', client_id=client_id))

    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        try:
            # Parse date of birth
            dob = datetime.strptime(request.form['dateOfBirth'], '%Y-%m-%d').date()
            age = int(request.form['age'])

            # Validate age range (14-18 years)
            if age < 14 or age > 18:
                flash(f'Client age must be between 14 and 18 years. Current age: {age} years.')
                return render_template('edit_client.html', client=client)

            # Update client information
            client.firstName = request.form['firstName']
            client.secondName = request.form['secondName']
            client.dateOfBirth = dob
            client.age = int(request.form['age'])
            client.nickname = request.form.get('nickname', '')
            client.admissionType = request.form['admissionType']
            client.referralInstitution = request.form.get('referralInstitution', '')
            client.referralContact = request.form.get('referralContact', '')
            client.streetName = request.form.get('streetName', '')
            client.parentGuardianName = request.form.get('parentGuardianName', '')
            client.parentGuardianLocation = request.form.get('parentGuardianLocation', '')
            client.parentGuardianContact = request.form.get('parentGuardianContact', '')
            client.intake = int(request.form.get('intake', 0))
            client.educationLevel = request.form.get('educationLevel', '')
            client.grade = request.form.get('grade', '')
            client.secondaryForm = request.form.get('secondaryForm', '')
            client.status = request.form.get('status', 'ACTIVE')

            db.session.commit()
            flash('Client information updated successfully!')
            return redirect(url_for('view_client', client_id=client_id))
        except Exception as e:
            flash(f'Error updating client: {str(e)}')

    return render_template('edit_client.html', client=client)

@app.route('/client/<int:client_id>/export_pdf')
@login_required
def export_client_pdf(client_id):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.pdfgen import canvas
    from io import BytesIO
    import textwrap

    client = Client.query.get_or_404(client_id)
    home_visits = HomeVisit.query.filter_by(client_id=client_id).order_by(HomeVisit.date.desc()).all()

    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=1.5*cm, 
        leftMargin=1.5*cm, 
        topMargin=2*cm, 
        bottomMargin=2*cm
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define professional color palette
    PRIMARY_BLUE = colors.Color(0.2, 0.3, 0.6)  # Professional blue
    SECONDARY_BLUE = colors.Color(0.4, 0.5, 0.8)  # Lighter blue
    TEXT_GRAY = colors.Color(0.2, 0.2, 0.2)  # Dark gray for text
    LIGHT_GRAY = colors.Color(0.95, 0.95, 0.95)  # Very light gray
    ACCENT_GREEN = colors.Color(0.1, 0.6, 0.3)  # Professional green

    # Define professional typography styles
    styles = getSampleStyleSheet()

    # Organization Header Style - Professional and bold
    org_title_style = ParagraphStyle(
        'OrgTitle',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=3,
        alignment=TA_CENTER,
        textColor=PRIMARY_BLUE,
        fontName='Times-Bold',
        letterSpacing=0.5
    )

    # Report Title Style
    report_title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=10,
        alignment=TA_CENTER,
        textColor=TEXT_GRAY,
        fontName='Times-Roman',
        letterSpacing=0.3
    )

    # Main Section Header - Clean and professional
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading1'],
        fontSize=10,
        spaceAfter=4,
        spaceBefore=8,
        textColor=colors.white,
        fontName='Times-Bold',
        backColor=PRIMARY_BLUE,
        borderPadding=4,
        leftIndent=0,
        rightIndent=0
    )

    # Subsection Header Style
    subsection_style = ParagraphStyle(
        'SubsectionHeader',
        parent=styles['Heading2'],
        fontSize=10,
        spaceAfter=4,
        spaceBefore=8,
        textColor=PRIMARY_BLUE,
        fontName='Times-Bold'
    )

    # Body text style - Clean and readable
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=4,
        alignment=TA_LEFT,
        fontName='Times-Roman',
        textColor=TEXT_GRAY,
        leading=11
    )

    # Report content style for longer text
    content_style = ParagraphStyle(
        'ContentText',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName='Times-Roman',
        textColor=TEXT_GRAY,
        leading=12,
        leftIndent=5,
        rightIndent=5
    )

    # Header with organization info
    elements.append(Paragraph("NEW LIFE MWANGAZA", org_title_style))
    elements.append(Paragraph("CLIENT COMPREHENSIVE REPORT", report_title_style))
    elements.append(Spacer(1, 8))

    # Report metadata in a clean format
    metadata_data = [
        ['Report Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
        ['Generated By:', current_user.username.title()],
        ['Client ID:', f"#{client.id:04d}"],
        ['Report Classification:', 'Confidential']
    ]

    metadata_table = Table(metadata_data, colWidths=[3.5*cm, 10*cm])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), SECONDARY_BLUE),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), TEXT_GRAY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, PRIMARY_BLUE)
    ]))
    elements.append(metadata_table)
    elements.append(Spacer(1, 12))

    # SECTION 1: Personal Information
    elements.append(Paragraph("PERSONAL INFORMATION", section_style))
    elements.append(Spacer(1, 3))

    personal_data = [
        ['Full Name', f"{client.firstName} {client.secondName}"],
        ['Nickname', client.nickname or 'Not specified'],
        ['Date of Birth', client.dateOfBirth.strftime('%B %d, %Y')],
        ['Current Age', f"{client.age} years old"],
        ['Client Status', client.status.replace('_', ' ').title()],
        ['Registration Date', client.createdAt.strftime('%B %d, %Y') if client.createdAt else 'Not available']
    ]

    personal_table = Table(personal_data, colWidths=[3.5*cm, 10*cm])
    personal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_GRAY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
    ]))
    elements.append(personal_table)
    elements.append(Spacer(1, 15))

    # SECTION 2: Admission Details
    elements.append(Paragraph("ADMISSION DETAILS", section_style))
    elements.append(Spacer(1, 6))

    admission_data = [
        ['Admission Type', client.admissionType.replace('_', ' ').title()],
        ['Intake Number', f"#{client.intake}" if client.intake > 0 else 'Not assigned']
    ]

    if client.admissionType == 'REFERRAL':
        admission_data.extend([
            ['Referral Institution', client.referralInstitution or 'Not specified'],
            ['Referral Contact', client.referralContact or 'Not provided']
        ])
    elif client.admissionType == 'STREET':
        admission_data.append(['Street/Location Found', client.streetName or 'Not specified'])

    admission_table = Table(admission_data, colWidths=[3.5*cm, 10*cm])
    admission_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_GRAY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1,-1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
    ]))
    elements.append(admission_table)
    elements.append(Spacer(1, 15))

    # SECTION 3: Educational Background
    if client.educationLevel or client.grade or client.secondaryForm:
        elements.append(Paragraph("EDUCATIONAL BACKGROUND", section_style))
        elements.append(Spacer(1, 6))

        education_data = []
        if client.educationLevel:
            education_data.append(['Education Level', client.educationLevel])
        if client.grade:
            education_data.append(['Current Grade', client.grade])
        if client.secondaryForm:
            education_data.append(['Secondary Form', client.secondaryForm])

        education_table = Table(education_data, colWidths=[3.5*cm, 10*cm])
        education_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_GRAY),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
        ]))
        elements.append(education_table)
        elements.append(Spacer(1, 15))

    # SECTION 4: Family Information
    if client.parentGuardianName or client.parentGuardianLocation or client.parentGuardianContact:
        elements.append(Paragraph("FAMILY/GUARDIAN INFORMATION", section_style))
        elements.append(Spacer(1, 6))

        family_data = []
        if client.parentGuardianName:
            family_data.append(['Parent/Guardian Name', client.parentGuardianName])
        if client.parentGuardianLocation:
            family_data.append(['Location/Address', client.parentGuardianLocation])
        if client.parentGuardianContact:
            family_data.append(['Contact Information', client.parentGuardianContact])

        family_table = Table(family_data, colWidths=[3.5*cm, 10*cm])
        family_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_GRAY),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
        ]))
        elements.append(family_table)
        elements.append(Spacer(1, 15))

    # SECTION 5: Home Visit Records
    if home_visits:
        elements.append(Paragraph("HOME VISIT RECORDS", section_style))
        elements.append(Spacer(1, 6))

        # Summary
        summary_text = f"Total home visits conducted: <b>{len(home_visits)}</b> | Latest visit: <b>{home_visits[0].date.strftime('%B %d, %Y')}</b>"
        elements.append(Paragraph(summary_text, body_style))
        elements.append(Spacer(1, 10))

        for i, visit in enumerate(home_visits, 1):
            # Keep each visit together on the same page
            visit_elements = []

            # Visit header with number and date
            visit_header = f"Visit #{i} • {visit.date.strftime('%B %d, %Y')}"
            visit_elements.append(Paragraph(visit_header, subsection_style))

            # Visit details in compact table
            visit_info = [
                ['Conducted By:', visit.conductedBy],
                ['Department:', visit.department.replace('_', ' ').title()],
                ['Recorded:', visit.createdAt.strftime('%B %d, %Y') if visit.createdAt else 'Not available']
            ]

            visit_info_table = Table(visit_info, colWidths=[2.5*cm, 11*cm])
            visit_info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.95, 1)),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_GRAY),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
            ]))
            visit_elements.append(visit_info_table)
            visit_elements.append(Spacer(1, 6))

            # Visit Report
            if visit.report:
                visit_elements.append(Paragraph("<b>Visit Report:</b>", body_style))
                # Better text wrapping for long content
                report_text = visit.report.replace('\n', '<br/>')
                if len(report_text) > 500:
                    report_text = report_text[:500] + "..."
                visit_elements.append(Paragraph(report_text, content_style))
                visit_elements.append(Spacer(1, 6))

            # Recommendations
            if visit.recommendations:
                visit_elements.append(Paragraph("<b>Recommendations:</b>", body_style))
                recommendations_text = visit.recommendations.replace('\n', '<br/>')
                if len(recommendations_text) > 500:
                    recommendations_text = recommendations_text[:500] + "..."
                visit_elements.append(Paragraph(recommendations_text, content_style))
                visit_elements.append(Spacer(1, 6))

            # Add the visit as a KeepTogether group
            elements.append(KeepTogether(visit_elements))

            # Add separator between visits (except for the last one)
            if i < len(home_visits):
                elements.append(Spacer(1, 8))
                separator_line = Table([['', '']], colWidths=[13.5*cm, 0*cm])
                separator_line.setStyle(TableStyle([
                    ('LINEABOVE', (0, 0), (-1, -1), 1, colors.lightgrey),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0)
                ]))
                elements.append(separator_line)
                elements.append(Spacer(1, 8))
    else:
        elements.append(Paragraph("HOME VISIT RECORDS", section_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("No home visit records found for this client.", body_style))

    # Additional spacing at end of document
    elements.append(Spacer(1, 20))

    # Professional page template
    def professional_page_template(canvas, doc):
        canvas.saveState()

        # Header with logo area and title
        canvas.setFillColor(PRIMARY_BLUE)
        canvas.rect(1.5*cm, A4[1] - 1.5*cm, A4[0] - 3*cm, 8*mm, fill=1)

        canvas.setFillColor(colors.white)
        canvas.setFont('Times-Bold', 10)
        canvas.drawString(2*cm, A4[1] - 1.2*cm, f"NEW LIFE MWANGAZA")

        canvas.setFont('Times-Roman', 8)
        canvas.drawRightString(A4[0] - 2*cm, A4[1] - 1.2*cm, f"Client: {client.firstName} {client.secondName}")

        # Footer with page number and confidentiality notice
        canvas.setFillColor(colors.Color(0.95, 0.95, 0.95))
        canvas.rect(1.5*cm, 0.5*cm, A4[0] - 3*cm, 8*mm, fill=1)

        canvas.setFillColor(TEXT_GRAY)
        canvas.setFont('Times-Roman', 7)
        canvas.drawString(2*cm, 0.8*cm, "© New Life Mwangaza - Confidential Document")
        canvas.drawRightString(A4[0] - 2*cm, 0.8*cm, f"Page {doc.page}")

        canvas.restoreState()

    # Build PDF with professional styling
    doc.build(elements, onFirstPage=professional_page_template, onLaterPages=professional_page_template)

    # Get PDF data
    pdf = buffer.getvalue()
    buffer.close()

    # Return PDF as response
    from flask import Response
    response = Response(pdf, content_type='application/pdf')
    response.headers['Content-Disposition'] = f'attachment; filename=NLM_Client_Report_{client.firstName}_{client.secondName}_{datetime.now().strftime("%Y%m%d")}.pdf'
    return response

@app.route('/aftercare')
@login_required
def aftercare():
    # Only Social Workers can access aftercare
    if current_user.department != 'socialworkers':
        flash('Access denied. Only Social Workers can access aftercare records.')
        return redirect(url_for('dashboard'))

    # Get all completed clients with their aftercare records (if any)
    completed_clients = Client.query.filter_by(status='COMPLETE').all()
    aftercare_records = AfterCare.query.join(Client).all()
    return render_template('aftercare.html', aftercare_records=aftercare_records, completed_clients=completed_clients)

@app.route('/alumni')
@login_required
def alumni():
    # Only Social Workers can access alumni
    if current_user.department != 'socialworkers':
        flash('Access denied. Only Social Workers can access alumni records.')
        return redirect(url_for('dashboard'))

    alumni_clients = Client.query.filter_by(status='COMPLETE').all()
    return render_template('alumni.html', alumni_clients=alumni_clients)

@app.route('/client/<int:client_id>/complete', methods=['POST'])
@login_required
def complete_client(client_id):
    # Only Admin and Social Workers can mark clients as completed
    if current_user.department not in ['admin', 'socialworkers']:
        flash('Access denied. Only Admin and Social Workers can mark clients as completed.')
        return redirect(url_for('dashboard'))

    client = Client.query.get_or_404(client_id)

    if client.status == 'COMPLETE':
        flash('Client is already marked as completed.')
        return redirect(url_for('dashboard'))

    try:
        client.status = 'COMPLETE'
        db.session.commit()
        flash(f'Client {client.firstName} {client.secondName} has been successfully marked as completed and moved to alumni list!')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Error marking client as completed: {str(e)}')
        return redirect(url_for('dashboard'))

@app.route('/add_aftercare/<int:client_id>', methods=['GET', 'POST'])
@login_required
def add_aftercare(client_id):
    # Only Social Workers can add aftercare records
    if current_user.department != 'socialworkers':
        flash('Access denied. Only Social Workers can add aftercare records.')
        return redirect(url_for('dashboard'))

    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        try:
            placement_date = None
            if request.form.get('placement_date'):
                placement_date = datetime.strptime(request.form['placement_date'], '%Y-%m-%d').date()

            placement_completion_date = None
            if request.form.get('placement_completion_date'):
                placement_completion_date = datetime.strptime(request.form['placement_completion_date'], '%Y-%m-%d').date()

            aftercare = AfterCare(
                client_id=client_id,
                status=request.form['status'],
                placement=request.form.get('placement', ''),
                institution=request.form.get('institution', ''),
                contact_person=request.form.get('contact_person', ''),
                contact_phone=request.form.get('contact_phone', ''),
                placement_date=placement_date,
                placement_completion_date=placement_completion_date,
                notes=request.form.get('notes', ''),
                createdBy=current_user.id
            )

            db.session.add(aftercare)

            # If status is COMPLETE, update client status
            if request.form['status'] == 'SUCCESSFUL':
                client.status = 'COMPLETE'

            db.session.commit()
            flash('Aftercare record added successfully!')
            return redirect(url_for('aftercare'))
        except Exception as e:
            flash(f'Error adding aftercare record: {str(e)}')

    return render_template('add_aftercare.html', client=client)

@app.route('/edit_aftercare/<int:aftercare_id>', methods=['GET', 'POST'])
@login_required
def edit_aftercare(aftercare_id):
    # Only Social Workers can edit aftercare records
    if current_user.department != 'socialworkers':
        flash('Access denied. Only Social Workers can edit aftercare records.')
        return redirect(url_for('dashboard'))

    aftercare = AfterCare.query.get_or_404(aftercare_id)
    client = aftercare.client

    if request.method == 'POST':
        try:
            placement_date = None
            if request.form.get('placement_date'):
                placement_date = datetime.strptime(request.form['placement_date'], '%Y-%m-%d').date()

            placement_completion_date = None
            if request.form.get('placement_completion_date'):
                placement_completion_date = datetime.strptime(request.form['placement_completion_date'], '%Y-%m-%d').date()

            # Update aftercare record
            aftercare.status = request.form['status']
            aftercare.placement = request.form.get('placement', '')
            aftercare.institution = request.form.get('institution', '')
            aftercare.contact_person = request.form.get('contact_person', '')
            aftercare.contact_phone = request.form.get('contact_phone', '')
            aftercare.placement_date = placement_date
            aftercare.placement_completion_date = placement_completion_date
            aftercare.notes = request.form.get('notes', '')

            # Update client status if needed
            if request.form['status'] == 'SUCCESSFUL':
                client.status = 'COMPLETE'

            db.session.commit()
            flash('Aftercare record updated successfully!')
            return redirect(url_for('aftercare'))
        except Exception as e:
            flash(f'Error updating aftercare record: {str(e)}')

    return render_template('edit_aftercare.html', aftercare=aftercare, client=client)

@app.route('/delete_aftercare/<int:aftercare_id>', methods=['POST'])
@login_required
def delete_aftercare(aftercare_id):
    # Only Social Workers can delete aftercare records
    if current_user.department != 'socialworkers':
        flash('Access denied. Only Social Workers can delete aftercare records.')
        return redirect(url_for('dashboard'))

    aftercare = AfterCare.query.get_or_404(aftercare_id)

    try:
        db.session.delete(aftercare)
        db.session.commit()
        flash('Aftercare record deleted successfully!')
    except Exception as e:
        flash(f'Error deleting aftercare record: {str(e)}')

    return redirect(url_for('aftercare'))

@app.route('/home_visits')
@login_required
def home_visits():
    # All departments can access home visits
    home_visits = HomeVisit.query.join(Client).filter(Client.status == 'ACTIVE').all()
    active_clients = Client.query.filter_by(status='ACTIVE').all()
    return render_template('home_visits.html', home_visits=home_visits, active_clients=active_clients)

@app.route('/add_home_visit/<int:client_id>', methods=['GET', 'POST'])
@login_required
def add_home_visit(client_id):
    client = Client.query.get_or_404(client_id)

    # Only allow home visits for active clients
    if client.status != 'ACTIVE':
        flash('Home visits can only be added for active clients.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            visit_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()

            home_visit = HomeVisit(
                client_id=client_id,
                date=visit_date,
                conductedBy=request.form['conductedBy'],
                department=request.form['department'],
                report=request.form.get('report', ''),
                recommendations=request.form.get('recommendations', ''),
                createdBy=current_user.id
            )

            db.session.add(home_visit)
            db.session.commit()
            flash('Home visit record added successfully!')
            return redirect(url_for('home_visits'))
        except Exception as e:
            flash(f'Error adding home visit record: {str(e)}')

    return render_template('add_home_visit.html', client=client)

@app.route('/client/<int:client_id>/home_visits')
@login_required
def client_home_visits(client_id):
    client = Client.query.get_or_404(client_id)
    visits = HomeVisit.query.filter_by(client_id=client_id).order_by(HomeVisit.date.desc()).all()
    return render_template('client_home_visits.html', client=client, visits=visits)

@app.route('/edit_home_visit/<int:visit_id>', methods=['GET', 'POST'])
@login_required
def edit_home_visit(visit_id):
    visit = HomeVisit.query.get_or_404(visit_id)
    client = visit.client

    if request.method == 'POST':
        try:
            visit_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()

            visit.date = visit_date
            visit.conductedBy = request.form['conductedBy']
            visit.department = request.form['department']
            visit.report = request.form.get('report', '')
            visit.recommendations = request.form.get('recommendations', '')

            db.session.commit()
            flash('Home visit record updated successfully!')
            return redirect(url_for('client_home_visits', client_id=client.id))
        except Exception as e:
            flash(f'Error updating home visit record: {str(e)}')

    return render_template('edit_home_visit.html', visit=visit, client=client)

@app.route('/api/clients')
@login_required
def api_clients():
    clients = Client.query.all()
    return jsonify([{
        'id': client.id,
        'firstName': client.firstName,
        'secondName': client.secondName,
        'age': client.age,
        'status': client.status,
        'admissionType': client.admissionType
    } for client in clients])

@app.route('/api/next_intake')
@login_required
def api_next_intake():
    # Get current year
    current_year = datetime.now().year

    # Get the highest intake number for current year
    # Intake format: YYYY### (e.g., 2025001, 2025002, etc.)
    year_prefix = current_year * 1000  # e.g., 2025000
    year_max = year_prefix + 999       # e.g., 2025999

    highest_intake = db.session.query(db.func.max(Client.intake)).filter(
        Client.intake >= year_prefix,
        Client.intake <= year_max
    ).scalar()

    # Generate next intake number
    if highest_intake:
        next_intake = highest_intake + 1
    else:
        # First intake for this year
        next_intake = year_prefix + 1  # e.g., 2025001

    return jsonify({'next_intake': next_intake})

# Education Management Routes
@app.route('/education')
@login_required
def education():
    # Only Education department can access this
    if current_user.department != 'education':
        flash('Access denied. Only Education department can access this section.')
        return redirect(url_for('dashboard'))

    subjects = Subject.query.all()
    active_clients = Client.query.filter_by(status='ACTIVE').all()
    return render_template('education.html', subjects=subjects, active_clients=active_clients)

@app.route('/add_subject', methods=['GET', 'POST'])
@login_required
def add_subject():
    # Only Education department can add subjects
    if current_user.department != 'education':
        flash('Access denied. Only Education department can add subjects.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            subject = Subject(
                name=request.form['name'],
                description=request.form.get('description', ''),
                createdBy=current_user.id
            )

            db.session.add(subject)
            db.session.commit()
            flash('Subject added successfully!')
            return redirect(url_for('education'))
        except Exception as e:
            flash(f'Error adding subject: {str(e)}')

    return render_template('add_subject.html')

@app.route('/add_marks/<int:client_id>', methods=['GET', 'POST'])
@login_required
def add_marks(client_id):
    # Only Education department can add marks
    if current_user.department != 'education':
        flash('Access denied. Only Education department can add marks.')
        return redirect(url_for('dashboard'))

    client = Client.query.get_or_404(client_id)

    # Only allow marks for active clients
    if client.status != 'ACTIVE':
        flash('Marks can only be added for active clients.')
        return redirect(url_for('education'))

    if request.method == 'POST':
        try:
            test_date = datetime.strptime(request.form['test_date'], '%Y-%m-%d').date()

            student_mark = StudentMark(
                client_id=client_id,
                subject_id=int(request.form['subject_id']),
                marks=float(request.form['marks']),
                max_marks=float(request.form.get('max_marks', 100)),
                test_date=test_date,
                term=request.form['term'],
                year=int(request.form['year']),
                notes=request.form.get('notes', ''),
                createdBy=current_user.id
            )

            db.session.add(student_mark)
            db.session.commit()
            flash('Marks added successfully!')
            return redirect(url_for('client_report', client_id=client_id))
        except Exception as e:
            flash(f'Error adding marks: {str(e)}')

    subjects = Subject.query.all()
    return render_template('add_marks.html', client=client, subjects=subjects)

@app.route('/client/<int:client_id>/report')
@login_required
def client_report(client_id):
    # Only Education department can view academic reports
    if current_user.department != 'education':
        flash('Access denied. Only Education department can view academic reports.')
        return redirect(url_for('dashboard'))

    client = Client.query.get_or_404(client_id)
    marks = StudentMark.query.filter_by(client_id=client_id).join(Subject).order_by(StudentMark.year.desc(), StudentMark.term.desc(), Subject.name).all()

    # Calculate overall performance
    total_percentage = 0
    total_subjects = 0

    for mark in marks:
        percentage = (mark.marks / mark.max_marks) * 100
        total_percentage += percentage
        total_subjects += 1

    overall_average = total_percentage / total_subjects if total_subjects > 0 else 0

    return render_template('client_report.html', client=client, marks=marks, overall_average=overall_average)

@app.route('/search_clients')
@login_required
def search_clients():
    query = request.args.get('q', '').strip()

    if not query:
        return redirect(url_for('dashboard'))

    # Search by name, intake, or nickname
    clients = Client.query.filter(
        db.or_(
            Client.firstName.ilike(f'%{query}%'),
            Client.secondName.ilike(f'%{query}%'),
            Client.nickname.ilike(f'%{query}%'),
            Client.intake.like(f'%{query}%')
        )
    ).order_by(Client.firstName, Client.secondName).all()

    return render_template('search_results.html', clients=clients, query=query)

@app.route('/all_clients')
@login_required
def all_clients():
    # Get all clients with pagination support
    page = request.args.get('page', 1, type=int)
    per_page = 50  # Show 50 clients per page

    # Order by status (ACTIVE first), then by name
    clients = Client.query.order_by(
        Client.status.desc(),  # ACTIVE comes before COMPLETE alphabetically
        Client.firstName, 
        Client.secondName
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Statistics for all clients
    total_count = Client.query.count()
    active_count = Client.query.filter_by(status='ACTIVE').count()
    completed_count = Client.query.filter_by(status='COMPLETE').count()

    stats = {
        'total': total_count,
        'active': active_count,
        'completed': completed_count,
        'street_admissions': Client.query.filter_by(admissionType='STREET').count(),
        'referral_admissions': Client.query.filter_by(admissionType='REFERRAL').count()
    }

    return render_template('all_clients.html', clients=clients, stats=stats)

@app.route('/clients_14_18')
@login_required
def clients_14_18():
    # Get clients aged between 14-18
    clients_14_18 = Client.query.filter(
        Client.age >= 14,
        Client.age <= 18
    ).order_by(Client.age, Client.firstName).all()

    # Statistics for this age group
    total_count = len(clients_14_18)
    active_count = len([c for c in clients_14_18 if c.status == 'ACTIVE'])
    completed_count = len([c for c in clients_14_18 if c.status == 'COMPLETE'])

    stats = {
        'total': total_count,
        'active': active_count,
        'completed': completed_count,
        'street_admissions': len([c for c in clients_14_18 if c.admissionType == 'STREET']),
        'referral_admissions': len([c for c in clients_14_18 if c.admissionType == 'REFERRAL'])
    }

    return render_template('clients_14_18.html', clients=clients_14_18, stats=stats)


# User Management Routes (Admin only)
@app.route('/users')
@login_required
def manage_users():
    # Only Admin can manage users
    if current_user.department != 'admin':
        flash('Access denied. Only Admin can manage users.')
        return redirect(url_for('dashboard'))

    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    # Only Admin can add users
    if current_user.department != 'admin':
        flash('Access denied. Only Admin can add users.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            username = request.form['username']
            department = request.form['department']
            password = request.form['password']

            # Check if username already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists. Please choose a different username.')
                return render_template('add_user.html')

            user = User(username=username, department=department)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash(f'User {username} created successfully!')
            return redirect(url_for('manage_users'))
        except Exception as e:
            flash(f'Error creating user: {str(e)}')

    departments = ['admin', 'socialworkers', 'counselling', 'education', 'empowerment']
    return render_template('add_user.html', departments=departments)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Only Admin can edit users
    if current_user.department != 'admin':
        flash('Access denied. Only Admin can edit users.')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        try:
            username = request.form['username']
            department = request.form['department']

            # Check if username already exists (except for current user)
            existing_user = User.query.filter_by(username=username).first()
            if existing_user and existing_user.id != user_id:
                flash('Username already exists. Please choose a different username.')
                return render_template('edit_user.html', user=user)

            user.username = username
            user.department = department

            # Update password if provided
            if request.form.get('password'):
                user.set_password(request.form['password'])

            db.session.commit()
            flash(f'User {username} updated successfully!')
            return redirect(url_for('manage_users'))
        except Exception as e:
            flash(f'Error updating user: {str(e)}')

    departments = ['admin', 'socialworkers', 'counselling', 'education', 'empowerment']
    return render_template('edit_user.html', user=user, departments=departments)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Only Admin can delete users
    if current_user.department != 'admin':
        flash('Access denied. Only Admin can delete users.')
        return redirect(url_for('manage_users'))

    # Prevent deleting current user
    if user_id == current_user.id:
        flash('You cannot delete your own account.')
        return redirect(url_for('manage_users'))

    user = User.query.get_or_404(user_id)

    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'User {username} deleted successfully!')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}')

    return redirect(url_for('manage_users'))

@app.route('/delete_client/<int:client_id>', methods=['POST'])
@login_required
def delete_client(client_id):
    # Only Admin can delete clients
    if current_user.department != 'admin':
        flash('Access denied. Only Admin can delete clients.')
        return redirect(url_for('dashboard'))

    client = Client.query.get_or_404(client_id)

    try:
        client_name = f"{client.firstName} {client.secondName}"

        # Delete related records first (due to foreign key constraints)
        # Delete home visits
        HomeVisit.query.filter_by(client_id=client_id).delete()

        # Delete aftercare records
        AfterCare.query.query.filter_by(client_id=client_id).delete()

        # Delete student marks
        StudentMark.query.filter_by(client_id=client_id).delete()

        # Finally delete the client
        db.session.delete(client)
        db.session.commit()

        flash(f'Client {client_name} and all related records have been permanently deleted!')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting client: {str(e)}')

    return redirect(url_for('dashboard'))



    # Statistics for this age group
    total_count = len(clients_14_18)
    active_count = len([c for c in clients_14_18 if c.status == 'ACTIVE'])
    completed_count = len([c for c in clients_14_18 if c.status == 'COMPLETE'])

    stats = {
        'total': total_count,
        'active': active_count,
        'completed': completed_count,
        'street_admissions': len([c for c in clients_14_18 if c.admissionType == 'STREET']),
        'referral_admissions': len([c for c in clients_14_18 if c.admissionType == 'REFERRAL'])
    }

    return render_template('clients_14_18.html', clients=clients_14_18, stats=stats)

@app.route('/overall_report')
@login_required
def overall_report():
    # Only Education department can view overall reports
    if current_user.department != 'education':
        flash('Access denied. Only Education department can view overall reports.')
        return redirect(url_for('dashboard'))

    # Get all active clients with their marks
    active_clients = Client.query.filter_by(status='ACTIVE').all()
    client_reports = []

    for client in active_clients:
        marks = StudentMark.query.filter_by(client_id=client.id).all()
        if marks:
            total_percentage = sum((mark.marks / mark.max_marks) * 100 for mark in marks)
            average = total_percentage / len(marks)
            client_reports.append({
                'client': client,
                'average': average,
                'total_subjects': len(marks)
            })

    # Sort by average in descending order
    client_reports.sort(key=lambda x: x['average'], reverse=True)

    return render_template('overall_report.html', client_reports=client_reports)

def create_default_users():
    """Create default users for each department with proper naming"""
    default_users = [
        {'username': 'admin_user', 'department': 'admin', 'password': 'admin123'},
        {'username': 'social_worker', 'department': 'socialworkers', 'password': 'social123'},
        {'username': 'counselor', 'department': 'counselling', 'password': 'counsel123'},
        {'username': 'educator', 'department': 'education', 'password': 'edu123'},
        {'username': 'empowerment_staff', 'department': 'empowerment', 'password': 'empower123'}
    ]

    for user_data in default_users:
        if not User.query.filter_by(username=user_data['username']).first():
            user = User(
                username=user_data['username'], 
                department=user_data['department']
            )
            user.set_password(user_data['password'])
            db.session.add(user)

    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_users()

    app.run(host='0.0.0.0', port=5000, debug=True)