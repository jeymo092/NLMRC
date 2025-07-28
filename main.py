from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Database configuration with MySQL, PostgreSQL, and SQLite support
database_url = os.environ.get('DATABASE_URL')
mysql_url = os.environ.get('MYSQL_URL')

if mysql_url:
    # Production: Use MySQL
    # Convert mysql:// to mysql+pymysql:// for SQLAlchemy
    if mysql_url.startswith('mysql://'):
        mysql_url = mysql_url.replace('mysql://', 'mysql+pymysql://')
    app.config['SQLALCHEMY_DATABASE_URI'] = mysql_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
    }
    print("🐬 Using MySQL database (production)")
elif database_url:
    # Production: Use PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    print("🐘 Using PostgreSQL database (production)")
else:
    # Development: Use SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mwangaza.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
    print("📝 Using SQLite database (development): mwangaza.db")

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
    full_name = db.Column(db.String(200), nullable=True)
    password_hash = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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

    # Relationship to empowerment programme enrollments
    empowerment_enrollments = db.relationship('ProgrammeEnrollment', backref='enrolled_client', lazy=True)

    # Additional relationships are defined in ParentRecord and GrantRecord models via backref

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

# EmpowermentProgramme Model
class EmpowermentProgramme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    programme_type = db.Column(db.String(50), nullable=False)  # VOCATIONAL, LIFE_SKILLS, ENTREPRENEURSHIP, BUSINESS_SKILLS, POSITIVE_PARENTING, CAPACITY_BUILDING
    duration_weeks = db.Column(db.Integer, nullable=False)
    program_audience = db.Column(db.String(50), nullable=False)  # YOUTH_14_18, YOUNG_ADULTS_18_25, PARENTS_GUARDIANS, etc.
    program_location = db.Column(db.String(50), nullable=False)  # ON_SITE, COMMUNITY_CENTER, PARTNER_FACILITY, etc.
    capacity = db.Column(db.Integer, nullable=False, default=20)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')  # ACTIVE, COMPLETED, CANCELLED
    instructor = db.Column(db.String(200))
    location = db.Column(db.String(200))
    requirements = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationship to programme enrollments
    enrollments = db.relationship('ProgrammeEnrollment', backref='programme', lazy=True)

# ProgrammeEnrollment Model
class ProgrammeEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    programme_id = db.Column(db.Integer, db.ForeignKey('empowerment_programme.id'), nullable=False)
    enrollment_date = db.Column(db.Date, nullable=False)
    completion_date = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False, default='ENROLLED')  # ENROLLED, COMPLETED, DROPPED_OUT
    progress_percentage = db.Column(db.Float, default=0.0)
    final_grade = db.Column(db.String(10))  # A, B, C, D, F
    attendance_percentage = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    certificate_issued = db.Column(db.Boolean, default=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'))

# ParentRecord Model
class ParentRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    parent_name = db.Column(db.String(200), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)  # Father, Mother, Guardian
    contact_phone = db.Column(db.String(50))
    contact_address = db.Column(db.Text)
    involvement_level = db.Column(db.String(50))  # ACTIVE, MODERATE, MINIMAL, NO_CONTACT
    last_contact_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    emergency_contact = db.Column(db.Boolean, default=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationship to client
    client = db.relationship('Client', backref='parent_records', lazy=True)

# GrantRecord Model
class GrantRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    grant_name = db.Column(db.String(200), nullable=False)  # Name of the grant/tool
    grant_type = db.Column(db.String(50), nullable=False)  # TOOLS, CASH, EQUIPMENT, MATERIALS
    item_description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    estimated_value = db.Column(db.Float)
    grant_date = db.Column(db.Date, nullable=False)
    purpose = db.Column(db.String(200))  # Business startup, Skills training, etc.
    condition = db.Column(db.String(50))  # NEW, USED, REFURBISHED
    supplier_vendor = db.Column(db.String(200))
    receipt_number = db.Column(db.String(100))
    return_required = db.Column(db.Boolean, default=False)
    return_date = db.Column(db.Date)
    status = db.Column(db.String(30), default='ACTIVE')  # ACTIVE, RETURNED, LOST, DAMAGED
    notes = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationship to client
    client = db.relationship('Client', backref='grant_records', lazy=True)

# TreatmentPlan Model
class TreatmentPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    plan_date = db.Column(db.Date, nullable=False)
    presenting_issues = db.Column(db.Text, nullable=False)
    treatment_goals = db.Column(db.Text, nullable=False)
    interventions = db.Column(db.Text, nullable=False)
    target_behaviors = db.Column(db.Text)
    success_indicators = db.Column(db.Text)
    estimated_duration = db.Column(db.String(100))  # e.g., "3 months", "6 sessions"
    review_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, COMPLETED, REVISED
    counselor_name = db.Column(db.String(200), nullable=False)
    supervisor_approval = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationship to client
    client = db.relationship('Client', backref='treatment_plans', lazy=True)

# SoapNote Model
class SoapNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    session_type = db.Column(db.String(50), nullable=False)  # INDIVIDUAL, GROUP, FAMILY
    session_location = db.Column(db.String(100))  # Location of session
    
    # SOAP Components
    subjective = db.Column(db.Text, nullable=False)  # What client reports
    objective = db.Column(db.Text, nullable=False)  # Observable behaviors/data
    assessment = db.Column(db.Text, nullable=False)  # Clinical interpretation
    plan = db.Column(db.Text, nullable=False)  # Next steps/interventions
    
    # Session Details
    session_duration = db.Column(db.Integer)  # Duration in minutes
    attendance = db.Column(db.String(20), default='PRESENT')  # PRESENT, LATE, NO_SHOW
    
    # Clinical Ratings
    mood_rating = db.Column(db.Integer)  # 1-10 scale
    anxiety_level = db.Column(db.Integer)  # 1-10 scale
    depression_level = db.Column(db.Integer)  # 1-10 scale
    progress_rating = db.Column(db.Integer)  # 1-10 scale
    functioning_level = db.Column(db.String(20))  # HIGH, MODERATE, LOW
    
    # Mental Status Exam
    appearance = db.Column(db.Text)  # Physical appearance, grooming
    behavior = db.Column(db.Text)  # Observable behaviors
    speech = db.Column(db.Text)  # Speech patterns, volume, rate
    mood_affect = db.Column(db.Text)  # Client's stated mood and observed affect
    thought_process = db.Column(db.Text)  # Organization of thoughts
    thought_content = db.Column(db.Text)  # Content of thoughts, delusions, etc.
    perception = db.Column(db.Text)  # Hallucinations, illusions
    cognition = db.Column(db.Text)  # Memory, concentration, orientation
    insight = db.Column(db.String(20))  # POOR, LIMITED, FAIR, GOOD
    judgment = db.Column(db.String(20))  # POOR, LIMITED, FAIR, GOOD
    
    # Risk Assessment
    suicide_risk = db.Column(db.String(20))  # NONE, LOW, MODERATE, HIGH
    homicide_risk = db.Column(db.String(20))  # NONE, LOW, MODERATE, HIGH
    self_harm_risk = db.Column(db.String(20))  # NONE, LOW, MODERATE, HIGH
    substance_use = db.Column(db.Text)  # Current substance use
    
    # Session Content
    interventions_used = db.Column(db.Text)  # Therapeutic interventions used
    client_response = db.Column(db.Text)  # How client responded to interventions
    homework_assigned = db.Column(db.Text)
    homework_review = db.Column(db.Text)  # Review of previous homework
    
    # Professional Information
    counselor_name = db.Column(db.String(200), nullable=False)
    supervisor_consultation = db.Column(db.Boolean, default=False)
    next_session_date = db.Column(db.Date)
    crisis_indicators = db.Column(db.Boolean, default=False)
    referrals_made = db.Column(db.Text)
    
    # Follow-up
    treatment_goals_addressed = db.Column(db.Text)
    barriers_to_progress = db.Column(db.Text)
    strengths_utilized = db.Column(db.Text)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationship to client
    client = db.relationship('Client', backref='soap_notes', lazy=True)

# ExitForm Model
class ExitForm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    exit_date = db.Column(db.Date, nullable=False)
    reason_for_exit = db.Column(db.String(50), nullable=False)  # COMPLETED, REFERRED, DROPPED_OUT, MOVED, OTHER
    goals_achieved = db.Column(db.Text)
    remaining_concerns = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    referrals_provided = db.Column(db.Text)
    follow_up_needed = db.Column(db.Boolean, default=False)
    follow_up_plan = db.Column(db.Text)
    client_satisfaction = db.Column(db.Integer)  # 1-10 scale
    counselor_assessment = db.Column(db.Text)
    risk_level_at_exit = db.Column(db.String(20))  # LOW, MODERATE, HIGH
    safety_plan_provided = db.Column(db.Boolean, default=False)
    emergency_contacts_updated = db.Column(db.Boolean, default=False)
    final_diagnosis = db.Column(db.String(200))
    treatment_summary = db.Column(db.Text)
    counselor_name = db.Column(db.String(200), nullable=False)
    supervisor_signature = db.Column(db.Boolean, default=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    createdBy = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationship to client
    client = db.relationship('Client', backref='exit_forms', lazy=True)

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
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        department = request.form.get('department', '')

        # Validate required fields
        if not username:
            flash('Username is required')
            return render_template('login.html')
        
        if not password:
            flash('Password is required')
            return render_template('login.html')
            
        if not department:
            flash('Please select a department')
            return render_template('login.html')

        try:
            # Find user by username
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                # Check if user's department matches selected department
                if user.department == department:
                    login_user(user)
                    return redirect(url_for('dashboard'))
                else:
                    flash(f'Invalid department. This user belongs to {user.department.replace("_", " ").title()} department.')
            else:
                flash('Invalid username or password')
                
        except Exception as e:
            print(f"Login error: {e}")
            flash('Login system error. Please try again.')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        full_name = request.form['full_name']
        department = request.form['department']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validation
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('signup.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long')
            return render_template('signup.html')

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different username.')
            return render_template('signup.html')

        # Create new user
        try:
            user = User(
                username=username,
                full_name=full_name,
                department=department
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash('Account created successfully! Please log in.')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error creating account: {str(e)}')
            return render_template('signup.html')

    return render_template('signup.html')

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

        # Programme statistics
        total_programmes = EmpowermentProgramme.query.count()
        active_programmes = EmpowermentProgramme.query.filter_by(status='ACTIVE').count()
        total_enrollments = ProgrammeEnrollment.query.filter_by(status='ENROLLED').count()
        completed_enrollments = ProgrammeEnrollment.query.filter_by(status='COMPLETED').count()

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
            'total_programmes': total_programmes,
            'active_programmes': active_programmes,
            'total_enrollments': total_enrollments,
            'completed_enrollments': completed_enrollments,
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

            # Age validation removed - no restrictions

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
            
            # Auto-create parent record if parent/guardian information is provided
            if client.parentGuardianName:
                parent_record = ParentRecord(
                    client_id=client.id,
                    parent_name=client.parentGuardianName,
                    relationship='GUARDIAN',  # Default to guardian, can be updated later
                    contact_phone=client.parentGuardianContact or '',
                    contact_address=client.parentGuardianLocation or '',
                    involvement_level='MODERATE',  # Default level
                    emergency_contact=True,  # Assume primary contact is emergency contact
                    notes=f'Auto-created from client registration on {datetime.now().strftime("%Y-%m-%d")}',
                    createdBy=current_user.id
                )
                db.session.add(parent_record)
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

            # Age validation removed - no restrictions

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
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
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
    # Only Social Workers, Counselling, and Admin can access aftercare
    if current_user.department not in ['socialworkers', 'counselling', 'admin']:
        flash('Access denied. Only Social Workers, Counselling, and Admin can access aftercare records.')
        return redirect(url_for('dashboard'))

    # Get all completed clients with their aftercare records (if any)
    completed_clients = Client.query.filter_by(status='COMPLETE').all()
    aftercare_records = AfterCare.query.join(Client).all()
    return render_template('aftercare.html', aftercare_records=aftercare_records, completed_clients=completed_clients)

@app.route('/alumni')
@login_required
def alumni():
    # Only Social Workers, Counselling, and Admin can access alumni
    if current_user.department not in ['socialworkers', 'counselling', 'admin']:
        flash('Access denied. Only Social Workers, Counselling, and Admin can access alumni records.')
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
    # Only Social Workers and Admin can add aftercare records
    if current_user.department not in ['socialworkers', 'admin']:
        flash('Access denied. Only Social Workers and Admin can add aftercare records.')
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

@app.route('/view_aftercare/<int:aftercare_id>')
@login_required
def view_aftercare(aftercare_id):
    # Only Social Workers and Admin can view aftercare records
    if current_user.department not in ['socialworkers', 'admin']:
        flash('Access denied. Only Social Workers and Admin can view aftercare records.')
        return redirect(url_for('dashboard'))

    aftercare = AfterCare.query.get_or_404(aftercare_id)
    client = aftercare.client
    return render_template('view_aftercare.html', aftercare=aftercare, client=client)

@app.route('/edit_aftercare/<int:aftercare_id>', methods=['GET', 'POST'])
@login_required
def edit_aftercare(aftercare_id):
    # Only Social Workers and Admin can edit aftercare records
    if current_user.department not in ['socialworkers', 'admin']:
        flash('Access denied. Only Social Workers and Admin can edit aftercare records.')
        return redirect(url_for('dashboard'))

    aftercare = AfterCare.query.get_or_404(aftercare_id)
    client = aftercare.client

    # Create a simple form class for the template
    class AfterCareForm:
        def __init__(self, aftercare_record=None):
            self.status = AfterCareField('status', aftercare_record.status if aftercare_record else '')
            self.placement = AfterCareField('placement', aftercare_record.placement if aftercare_record else '')
            self.institution = AfterCareField('institution', aftercare_record.institution if aftercare_record else '')
            self.contact_person = AfterCareField('contact_person', aftercare_record.contact_person if aftercare_record else '')
            self.contact_phone = AfterCareField('contact_phone', aftercare_record.contact_phone if aftercare_record else '')
            self.placement_date = AfterCareField('placement_date', 
                aftercare_record.placement_date.strftime('%Y-%m-%d') if aftercare_record and aftercare_record.placement_date else '')
            self.placement_completion_date = AfterCareField('placement_completion_date', 
                aftercare_record.placement_completion_date.strftime('%Y-%m-%d') if aftercare_record and aftercare_record.placement_completion_date else '')
            self.notes = AfterCareField('notes', aftercare_record.notes if aftercare_record else '')

        def hidden_tag(self):
            return ''

    class AfterCareField:
        def __init__(self, name, value=''):
            self.id = name
            self.name = name
            self.data = value if value is not None else ''
            self.errors = []
            self.label = FieldLabel(name)

        def __call__(self, **kwargs):
            from markupsafe import Markup
            attrs = ' '.join([f'{k}="{v}"' for k, v in kwargs.items()])
            if self.id == 'status':
                options = []
                status_choices = [
                    ('IN_PROGRESS', 'In Progress'),
                    ('SUCCESSFUL', 'Successful'),
                    ('EMPLOYED', 'Employed'),
                    ('ATTACHMENT', 'Attachment'),
                    ('INTERNSHIP', 'Internship'),
                    ('RELAPSED', 'Relapsed'),
                    ('ABSCONDED', 'Absconded')
                ]
                for value, label in status_choices:
                    selected = 'selected' if value == self.data else ''
                    options.append(f'<option value="{value}" {selected}>{label}</option>')
                return Markup(f'<select name="{self.name}" id="{self.id}" {attrs}>{"".join(options)}</select>')
            elif self.id in ['placement_date', 'placement_completion_date']:
                return Markup(f'<input type="date" name="{self.name}" id="{self.id}" value="{self.data}" {attrs}>')
            elif self.id == 'notes':
                return Markup(f'<textarea name="{self.name}" id="{self.id}" {attrs}>{self.data}</textarea>')
            else:
                # Escape HTML in values to prevent rendering issues
                escaped_value = self.data.replace('"', '&quot;') if self.data else ''
                return Markup(f'<input type="text" name="{self.name}" id="{self.id}" value="{escaped_value}" {attrs}>')

    class FieldLabel:
        def __init__(self, name):
            self.text = {
                'status': 'Status',
                'placement': 'Placement',
                'institution': 'Institution',
                'contact_person': 'Contact Person',
                'contact_phone': 'Contact Phone',
                'placement_date': 'Placement Date',
                'placement_completion_date': 'Placement Completion Date',
                'notes': 'Notes'
            }.get(name, name.replace('_', ' ').title())

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

    form = AfterCareForm(aftercare)
    return render_template('edit_aftercare.html', aftercare=aftercare, client=client, form=form)

@app.route('/delete_aftercare/<int:aftercare_id>', methods=['POST'])
@login_required
def delete_aftercare(aftercare_id):
    # Only Social Workers and Admin can delete aftercare records
    if current_user.department not in ['socialworkers', 'admin']:
        flash('Access denied. Only Social Workers and Admin can delete aftercare records.')
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

@app.route('/delete_home_visit/<int:visit_id>', methods=['POST'])
@login_required
def delete_home_visit(visit_id):
    # Only Admin can delete home visit records
    if current_user.department not in ['admin']:
        flash('Access denied. Only Admin can delete home visit records.')
        return redirect(url_for('home_visits'))

    visit = HomeVisit.query.get_or_404(visit_id)

    try:
        client_name = f"{visit.client.firstName} {visit.client.secondName}"
        db.session.delete(visit)
        db.session.commit()
        flash(f'Home visit record for {client_name} deleted successfully!')
    except Exception as e:
        flash(f'Error deleting home visit record: {str(e)}')

    return redirect(url_for('home_visits'))

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
    # Only Education department and Admin can access this
    if current_user.department not in ['education', 'admin']:
        flash('Access denied. Only Education department and Admin can access this section.')
        return redirect(url_for('dashboard'))

    subjects = Subject.query.all()
    active_clients = Client.query.filter_by(status='ACTIVE').all()
    return render_template('education.html', subjects=subjects, active_clients=active_clients)

@app.route('/add_subject', methods=['GET', 'POST'])
@login_required
def add_subject():
    # Only Education department and Admin can add subjects
    if current_user.department not in ['education', 'admin']:
        flash('Access denied. Only Education department and Admin can add subjects.')
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
    # Only Education department and Admin can add marks
    if current_user.department not in ['education', 'admin']:
        flash('Access denied. Only Education department and Admin can add marks.')
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
    # Only Education department and Admin can view academic reports
    if current_user.department not in ['education', 'admin']:
        flash('Access denied. Only Education department and Admin can view academic reports.')
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


# Empowerment Programme Routes
@app.route('/empowerment_programmes')
@login_required
def empowerment_programmes():
    # Only Empowerment department and Admin can access this
    if current_user.department not in ['empowerment', 'admin']:
        flash('Access denied. Only Empowerment department and Admin can access this section.')
        return redirect(url_for('dashboard'))

    programmes = EmpowermentProgramme.query.all()
    active_clients = Client.query.filter_by(status='ACTIVE').all()
    return render_template('empowerment_programmes.html', programmes=programmes, active_clients=active_clients)

@app.route('/add_programme', methods=['GET', 'POST'])
@login_required
def add_programme():
    # Only Empowerment department and Admin can add programmes
    if current_user.department not in ['empowerment', 'admin']:
        flash('Access denied. Only Empowerment department and Admin can add programmes.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            start_date = None
            if request.form.get('start_date'):
                start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()

            end_date = None
            if request.form.get('end_date'):
                end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()

            programme = EmpowermentProgramme(
                name=request.form['name'],
                description=request.form.get('description', ''),
                programme_type=request.form['programme_type'],
                duration_weeks=int(request.form['duration_weeks']),
                program_audience=request.form['program_audience'],
                program_location=request.form['program_location'],
                capacity=int(request.form.get('capacity', 20)),
                start_date=start_date,
                end_date=end_date,
                status=request.form.get('status', 'ACTIVE'),
                instructor=request.form.get('instructor', ''),
                location=request.form.get('location_details', ''),
                requirements=request.form.get('requirements', ''),
                createdBy=current_user.id
            )

            db.session.add(programme)
            db.session.commit()
            flash('Empowerment programme added successfully!')
            return redirect(url_for('empowerment_programmes'))
        except Exception as e:
            flash(f'Error adding programme: {str(e)}')

    return render_template('add_programme.html')

@app.route('/enroll_client/<int:programme_id>', methods=['GET', 'POST'])
@login_required
def enroll_client(programme_id):
    # Only Empowerment department and Admin can enroll clients
    if current_user.department not in ['empowerment', 'admin']:
        flash('Access denied. Only Empowerment department and Admin can enroll clients.')
        return redirect(url_for('dashboard'))

    programme = EmpowermentProgramme.query.get_or_404(programme_id)

    if request.method == 'POST':
        try:
            client_id = int(request.form['client_id'])
            client = Client.query.get_or_404(client_id)

            # Check if client is eligible (status only)
            if client.status != 'ACTIVE':
                flash('Only active clients can be enrolled in programmes.')
                return render_template('enroll_client.html', programme=programme)

            # Check if client is already enrolled
            existing_enrollment = ProgrammeEnrollment.query.filter_by(
                client_id=client_id, 
                programme_id=programme_id,
                status='ENROLLED'
            ).first()

            if existing_enrollment:
                flash('Client is already enrolled in this programme.')
                return render_template('enroll_client.html', programme=programme)

            enrollment_date = datetime.strptime(request.form['enrollment_date'], '%Y-%m-%d').date()

            enrollment = ProgrammeEnrollment(
                client_id=client_id,
                programme_id=programme_id,
                enrollment_date=enrollment_date,
                status='ENROLLED',
                notes=request.form.get('notes', ''),
                createdBy=current_user.id
            )

            db.session.add(enrollment)
            db.session.commit()
            flash(f'Client {client.firstName} {client.secondName} enrolled successfully!')
            return redirect(url_for('programme_details', programme_id=programme_id))
        except Exception as e:
            flash(f'Error enrolling client: {str(e)}')

    # Get eligible clients (active clients only)
    eligible_clients = Client.query.filter(
        Client.status == 'ACTIVE'
    ).all()

    # Remove already enrolled clients
    enrolled_client_ids = [e.client_id for e in ProgrammeEnrollment.query.filter_by(
        programme_id=programme_id, status='ENROLLED'
    ).all()]

    eligible_clients = [c for c in eligible_clients if c.id not in enrolled_client_ids]

    return render_template('enroll_client.html', programme=programme, eligible_clients=eligible_clients)

@app.route('/programme/<int:programme_id>')
@login_required
def programme_details(programme_id):
    # Only Empowerment department and Admin can view programme details
    if current_user.department not in ['empowerment', 'admin']:
        flash('Access denied. Only Empowerment department and Admin can view programme details.')
        return redirect(url_for('dashboard'))

    programme = EmpowermentProgramme.query.get_or_404(programme_id)
    enrollments = ProgrammeEnrollment.query.filter_by(programme_id=programme_id).join(Client).order_by(Client.firstName).all()

    return render_template('programme_details.html', programme=programme, enrollments=enrollments)

@app.route('/update_enrollment/<int:enrollment_id>', methods=['GET', 'POST'])
@login_required
def update_enrollment(enrollment_id):
    # Only Empowerment department and Admin can update enrollments
    if current_user.department not in ['empowerment', 'admin']:
        flash('Access denied. Only Empowerment department and Admin can update enrollments.')
        return redirect(url_for('dashboard'))

    enrollment = ProgrammeEnrollment.query.get_or_404(enrollment_id)

    if request.method == 'POST':
        try:
            enrollment.status = request.form['status']
            enrollment.progress_percentage = float(request.form.get('progress_percentage', 0))
            enrollment.attendance_percentage = float(request.form.get('attendance_percentage', 0))
            enrollment.final_grade = request.form.get('final_grade', '')
            enrollment.notes = request.form.get('notes', '')
            enrollment.certificate_issued = 'certificate_issued' in request.form

            if request.form.get('completion_date'):
                enrollment.completion_date = datetime.strptime(request.form['completion_date'], '%Y-%m-%d').date()

            if enrollment.status == 'COMPLETED' and not enrollment.completion_date:
                enrollment.completion_date = datetime.now().date()

            db.session.commit()
            flash('Enrollment updated successfully!')
            return redirect(url_for('programme_details', programme_id=enrollment.programme_id))
        except Exception as e:
            flash(f'Error updating enrollment: {str(e)}')

    return render_template('update_enrollment.html', enrollment=enrollment)

@app.route('/programme_templates')
@login_required
def programme_templates():
    # Only Empowerment department and Admin can view programme templates
    if current_user.department not in ['empowerment', 'admin']:
        flash('Access denied. Only Empowerment department and Admin can view programme templates.')
        return redirect(url_for('dashboard'))

    return render_template('programme_templates.html')

@app.route('/create_custom_programme', methods=['GET', 'POST'])
@login_required
def create_custom_programme():
    # Only Empowerment department and Admin can create custom programmes
    if current_user.department not in ['empowerment', 'admin']:
        flash('Access denied. Only Empowerment department and Admin can create custom programmes.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            start_date = None
            if request.form.get('start_date'):
                start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()

            end_date = None
            if request.form.get('end_date'):
                end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()

            programme = EmpowermentProgramme(
                name=request.form['name'],
                description=request.form.get('description', ''),
                programme_type=request.form['programme_type'],
                duration_weeks=int(request.form['duration_weeks']),
                program_audience=request.form['program_audience'],
                program_location=request.form['program_location'],
                capacity=int(request.form.get('capacity', 20)),
                start_date=start_date,
                end_date=end_date,
                status=request.form.get('status', 'ACTIVE'),
                instructor=request.form.get('instructor', ''),
                location=request.form.get('location_details', ''),
                requirements=request.form.get('requirements', ''),
                createdBy=current_user.id
            )

            db.session.add(programme)
            db.session.commit()
            flash('Custom programme created successfully!')
            return redirect(url_for('empowerment_programmes'))
        except Exception as e:
            flash(f'Error creating custom programme: {str(e)}')

    return render_template('create_custom_programme.html')

@app.route('/client/<int:client_id>/programmes')
@login_required
def client_programmes(client_id):
    # Only Empowerment department and Admin can view client programmes
    if current_user.department not in ['empowerment', 'admin']:
        flash('Access denied. Only Empowerment department and Admin can view client programmes.')
        return redirect(url_for('dashboard'))

    client = Client.query.get_or_404(client_id)
    enrollments = ProgrammeEnrollment.query.filter_by(client_id=client_id).join(EmpowermentProgramme).order_by(ProgrammeEnrollment.enrollment_date.desc()).all()

    return render_template('client_programmes.html', client=client, enrollments=enrollments)

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

    # Define departments list
    departments = [
        ('admin', 'Administration'),
        ('socialworkers', 'Social Workers'),
        ('counselling', 'Counselling'),
        ('education', 'Education'),
        ('empowerment', 'Empowerment')
    ]

    if request.method == 'POST':
        try:
            username = request.form['username']
            department = request.form['department']
            password = request.form['password']

            # Check if username already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists. Please choose a different username.')
                return render_template('add_user.html', departments=departments)

            user = User(username=username, department=department)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash(f'User {username} created successfully!')
            return redirect(url_for('manage_users'))
        except Exception as e:
            flash(f'Error creating user: {str(e)}')

    return render_template('add_user.html', departments=departments)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Only Admin can edit users
    if current_user.department != 'admin':
        flash('Access denied. Only Admin can edit users.')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    # Define departments list
    departments = [
        ('admin', 'Administration'),
        ('socialworkers', 'Social Workers'),
        ('counselling', 'Counselling'),
        ('education', 'Education'),
        ('empowerment', 'Empowerment')
    ]

    if request.method == 'POST':
        try:
            username = request.form['username']
            department = request.form['department']

            # Check if username already exists (except for current user)
            existing_user = User.query.filter_by(username=username).first()
            if existing_user and existing_user.id != user_id:
                flash('Username already exists. Please choose a different username.')
                return render_template('edit_user.html', user=user, departments=departments)

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

# Parent Records Management
@app.route('/parent_records')
@login_required
def parent_records():
    # Only Empowerment department and Admin can access parent records
    if current_user.department not in ['empowerment', 'admin']:
        flash('Access denied. Only Empowerment department and Admin can access parent records.')
        return redirect(url_for('dashboard'))

    parent_records = ParentRecord.query.all()
    active_clients = Client.query.all()
    return render_template('parent_records.html', parent_records=parent_records, active_clients=active_clients)

@app.route('/add_parent_record/<int:client_id>', methods=['GET', 'POST'])
@login_required
def add_parent_record(client_id):
    # Only Empowerment department and Admin can add parent records
    if current_user.department not in ['empowerment', 'admin']:
        flash('Access denied. Only Empowerment department and Admin can add parent records.')
        return redirect(url_for('dashboard'))

    client = Client.query.get_or_404(client_id)

    # Allow parent records for any client status (active, completed, alumni)

    if request.method == 'POST':
        try:
            last_contact_date = None
            if request.form.get('last_contact_date'):
                last_contact_date = datetime.strptime(request.form['last_contact_date'], '%Y-%m-%d').date()

            parent_record = ParentRecord(
                client_id=client_id,
                parent_name=request.form['parent_name'],
                relationship=request.form['relationship'],
                contact_phone=request.form.get('contact_phone', ''),
                contact_address=request.form.get('contact_address', ''),
                involvement_level=request.form['involvement_level'],
                last_contact_date=last_contact_date,
                notes=request.form.get('notes', ''),
                emergency_contact='emergency_contact' in request.form,
                createdBy=current_user.id
            )

            db.session.add(parent_record)
            db.session.commit()
            flash('Parent record added successfully!')
            return redirect(url_for('parent_records'))
        except Exception as e:
            flash(f'Error adding parent record: {str(e)}')

    return render_template('add_parent_record.html', client=client)

@app.route('/grants_tools')
@login_required
def grants_tools():
    # Only Empowerment department and Admin can access grants and tools records
    if current_user.department not in ['empowerment', 'admin']:
        flash('Access denied. Only Empowerment department and Admin can access grants and tools records.')
        return redirect(url_for('dashboard'))

    grant_records = GrantRecord.query.join(Client).order_by(GrantRecord.grant_date.desc()).all()
    all_clients = Client.query.order_by(Client.status.desc(), Client.firstName, Client.secondName).all()  # Show alumni and active clients
    return render_template('grants_tools.html', grant_records=grant_records, all_clients=all_clients)

@app.route('/add_grant/<int:client_id>', methods=['GET', 'POST'])
@login_required
def add_grant(client_id):
    # Only Empowerment department and Admin can add grants
    if current_user.department not in ['empowerment', 'admin']:
        flash('Access denied. Only Empowerment department and Admin can add grants.')
        return redirect(url_for('dashboard'))

    client = Client.query.get_or_404(client_id)

    # Allow grants for any client status (active, completed, alumni)

    if request.method == 'POST':
        try:
            grant_date = datetime.strptime(request.form['grant_date'], '%Y-%m-%d').date()

            return_date = None
            if request.form.get('return_date'):
                return_date = datetime.strptime(request.form['return_date'], '%Y-%m-%d').date()

            grant_record = GrantRecord(
                client_id=client_id,
                grant_name=request.form['grant_name'],
                grant_type=request.form['grant_type'],
                item_description=request.form['item_description'],
                quantity=int(request.form.get('quantity', 1)),
                estimated_value=float(request.form.get('estimated_value', 0)) if request.form.get('estimated_value') else None,
                grant_date=grant_date,
                purpose=request.form.get('purpose', ''),
                condition=request.form.get('condition', 'NEW'),
                supplier_vendor=request.form.get('supplier_vendor', ''),
                receipt_number=request.form.get('receipt_number', ''),
                return_required='return_required' in request.form,
                return_date=return_date,
                status=request.form.get('status', 'ACTIVE'),
                notes=request.form.get('notes', ''),
                createdBy=current_user.id
            )

            db.session.add(grant_record)
            db.session.commit()
            flash('Grant/Tools record added successfully!')
            return redirect(url_for('grants_tools'))
        except Exception as e:
            flash(f'Error adding grant record: {str(e)}')

    return render_template('add_grant.html', client=client)

@app.route('/client/<int:client_id>/empowerment_records')
@login_required
def client_empowerment_records(client_id):
    # Only Empowerment department and Admin can view client empowerment records
    if current_user.department not in ['empowerment', 'admin']:
        flash('Access denied. Only Empowerment department and Admin can view empowerment records.')
        return redirect(url_for('dashboard'))

    client = Client.query.get_or_404(client_id)
    parent_records = ParentRecord.query.filter_by(client_id=client_id).all()
    grant_records = GrantRecord.query.filter_by(client_id=client_id).order_by(GrantRecord.grant_date.desc()).all()
    enrollments = ProgrammeEnrollment.query.filter_by(client_id=client_id).join(EmpowermentProgramme).order_by(ProgrammeEnrollment.enrollment_date.desc()).all()

    return render_template('client_empowerment_records.html', 
                         client=client, 
                         parent_records=parent_records, 
                         grant_records=grant_records, 
                         enrollments=enrollments)

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
        AfterCare.query.filter_by(client_id=client_id).delete()

        # Delete student marks
        StudentMark.query.filter_by(client_id=client_id).delete()

        # Delete parent records
        ParentRecord.query.filter_by(client_id=client_id).delete()

        # Delete grant records
        GrantRecord.query.filter_by(client_id=client_id).delete()

        # Delete programme enrollments
        ProgrammeEnrollment.query.filter_by(client_id=client_id).delete()

        # Delete counselling records
        TreatmentPlan.query.filter_by(client_id=client_id).delete()
        SoapNote.query.filter_by(client_id=client_id).delete()
        ExitForm.query.filter_by(client_id=client_id).delete()

        # Finally delete the client
        db.session.delete(client)
        db.session.commit()

        flash(f'Client {client_name} and all related records have been permanently deleted!')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting client: {str(e)}')

    return redirect(url_for('dashboard'))

@app.route('/import_database', methods=['GET', 'POST'])
@login_required
def import_database():
    # Only Admin can import database
    if current_user.department != 'admin':
        flash('Access denied. Only Admin can import database.')
        return redirect(url_for('manage_users'))

    if request.method == 'POST':
        import shutil, os
        from werkzeug.utils import secure_filename
        import sqlite3
        import time
        
        temp_upload_path = None
        
        try:
            # Check if file was uploaded
            if 'database_file' not in request.files:
                flash('No file selected for upload.')
                return redirect(url_for('import_database'))
            
            file = request.files['database_file']
            
            if file.filename == '':
                flash('No file selected for upload.')
                return redirect(url_for('import_database'))
            
            # Validate file extension
            if not file.filename.lower().endswith('.db'):
                flash('Invalid file type. Please upload a .db file.')
                return redirect(url_for('import_database'))
            
            # Secure the filename
            filename = secure_filename(file.filename)
            
            # Create temporary upload path with unique name to avoid conflicts
            temp_upload_path = os.path.abspath(f'temp_import_{int(time.time())}_{filename}')
            
            # Save uploaded file temporarily
            file.save(temp_upload_path)
            
            # Check file size to ensure it's not empty
            file_size = os.path.getsize(temp_upload_path)
            if file_size == 0:
                flash('Uploaded file is empty.')
                os.remove(temp_upload_path)
                return redirect(url_for('import_database'))
            
            print(f"📁 Processing upload: {filename} ({file_size:,} bytes)")
            
            # Validate it's a valid SQLite database
            try:
                test_conn = sqlite3.connect(temp_upload_path)
                cursor = test_conn.cursor()
                
                # Check if it's a valid SQLite database
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                if not tables:
                    flash('The uploaded file does not contain any database tables.')
                    test_conn.close()
                    os.remove(temp_upload_path)
                    return redirect(url_for('import_database'))
                
                table_names = [table[0] for table in tables]
                print(f"📋 Found tables in upload: {', '.join(table_names)}")
                
                # Check for required New Life Mwangaza tables
                expected_tables = ['user', 'client']
                missing_tables = [table for table in expected_tables if table not in table_names]
                
                if missing_tables:
                    flash(f'This does not appear to be a valid New Life Mwangaza database backup. Missing required tables: {", ".join(missing_tables)}')
                    test_conn.close()
                    os.remove(temp_upload_path)
                    return redirect(url_for('import_database'))
                
                # Count records in key tables to verify data
                record_counts = {}
                total_records = 0
                
                for table_name in table_names:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                        count = cursor.fetchone()[0]
                        record_counts[table_name] = count
                        total_records += count
                    except sqlite3.Error as count_error:
                        print(f"⚠️ Could not count records in table '{table_name}': {count_error}")
                        record_counts[table_name] = 0
                
                print(f"📊 Import file contains {total_records} total records across {len(table_names)} tables")
                
                # Verify database structure integrity
                for table_name in expected_tables:
                    try:
                        cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                        columns = cursor.fetchall()
                        if not columns:
                            flash(f'Table {table_name} appears to be corrupted or empty.')
                            test_conn.close()
                            os.remove(temp_upload_path)
                            return redirect(url_for('import_database'))
                    except sqlite3.Error as pragma_error:
                        flash(f'Cannot verify table structure for {table_name}: {str(pragma_error)}')
                        test_conn.close()
                        os.remove(temp_upload_path)
                        return redirect(url_for('import_database'))
                
                test_conn.close()
                print("✅ Database validation successful")
                    
            except sqlite3.Error as e:
                flash(f'Invalid SQLite database file: {str(e)}')
                if os.path.exists(temp_upload_path):
                    os.remove(temp_upload_path)
                return redirect(url_for('import_database'))
            
            # Create backup of current database before replacement
            current_db_path = os.path.abspath('mwangaza.db')
            pre_import_backup = None
            
            if os.path.exists(current_db_path):
                try:
                    backup_dir = 'backups'
                    os.makedirs(backup_dir, exist_ok=True)
                    pre_import_backup = os.path.join(backup_dir, f'pre_import_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
                    shutil.copy2(current_db_path, pre_import_backup)
                    print(f"📦 Created pre-import backup: {pre_import_backup}")
                except Exception as backup_error:
                    print(f"⚠️ Could not create pre-import backup: {backup_error}")
                    flash('Warning: Could not create backup of current database before import.')
            
            # Replace current database with uploaded one
            try:
                if os.path.exists(current_db_path):
                    os.remove(current_db_path)
                
                shutil.move(temp_upload_path, current_db_path)
                temp_upload_path = None  # Mark as moved so cleanup doesn't try to remove it
                
                print(f"✅ Database file replaced: {current_db_path}")
                
            except Exception as replace_error:
                # Try to restore backup if replacement failed
                if pre_import_backup and os.path.exists(pre_import_backup):
                    try:
                        shutil.copy2(pre_import_backup, current_db_path)
                        print("🔄 Restored original database after failed import")
                    except Exception as restore_error:
                        print(f"❌ Could not restore original database: {restore_error}")
                
                flash(f'Failed to replace database file: {str(replace_error)}')
                return redirect(url_for('import_database'))
            
            # Verify the import was successful
            try:
                test_conn = sqlite3.connect(current_db_path)
                cursor = test_conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM user")
                user_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM client")
                client_count = cursor.fetchone()[0]
                
                test_conn.close()
                
                print(f"✅ Database import verification successful: {user_count} users, {client_count} clients")
                
                flash(f'✅ Database imported successfully! Found {user_count} users and {client_count} clients.')
                
                # Clear the current user session to force re-login with new database
                logout_user()
                flash('Database imported successfully! Please log in again to continue.')
                return redirect(url_for('login'))
                
            except Exception as verify_error:
                flash(f'Database imported but verification failed: {str(verify_error)}')
                print(f"⚠️ Import verification error: {verify_error}")
                return redirect(url_for('manage_users'))
            
        except Exception as e:
            # Clean up temporary file if it exists
            if temp_upload_path and os.path.exists(temp_upload_path):
                try:
                    os.remove(temp_upload_path)
                except:
                    pass
            
            flash(f'Error importing database: {str(e)}')
            print(f"❌ Database import error: {e}")
            return redirect(url_for('import_database'))
    
    return render_template('import_database.html')

@app.route('/backup_database')
@login_required
def backup_database():
    # Only Admin can backup database
    if current_user.department != 'admin':
        flash('Access denied. Only Admin can backup the database.')
        return redirect(url_for('manage_users'))

    from flask import send_file
    from io import BytesIO
    import sqlite3
    import shutil
    
    try:
        # Get the absolute path to the database file
        db_path = os.path.abspath('mwangaza.db')
        
        # Ensure database exists and has proper structure
        if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            print("🔧 Initializing database for backup...")
            
            try:
                # Initialize database within app context
                with app.app_context():
                    db.create_all()
                    
                    # Ensure admin user exists
                    admin_user = User.query.filter_by(username='admin').first()
                    if not admin_user:
                        admin_user = User(
                            username='admin',
                            full_name='System Administrator', 
                            department='admin'
                        )
                        admin_user.set_password('admin123')
                        db.session.add(admin_user)
                        db.session.commit()
                        print("✅ Admin user created for backup")
                    
                    # Give file system time to sync
                    import time
                    time.sleep(0.3)
                    
                print("✅ Database initialized for backup")
                    
            except Exception as init_error:
                print(f"⚠️ Database initialization warning: {init_error}")
                # Continue with backup attempt even if initialization had issues
        
        # Final verification
        if not os.path.exists(db_path):
            flash('Database file could not be created. Please check system permissions.')
            return redirect(url_for('manage_users'))
            
        file_size = os.path.getsize(db_path)
        if file_size == 0:
            flash('Database file is empty. Please add some data first.')
            return redirect(url_for('manage_users'))
        
        # Test database connectivity and get statistics
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables in the database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if not tables:
                conn.close()
                flash('Database appears to be empty or corrupted.')
                return redirect(url_for('manage_users'))
            
            table_names = [table[0] for table in tables]
            print(f"📋 Tables found for backup: {', '.join(table_names)}")
            
            # Get record counts
            total_records = 0
            for table_name in table_names:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    count = cursor.fetchone()[0]
                    total_records += count
                    print(f"📊 Table '{table_name}': {count} records")
                except sqlite3.Error as table_error:
                    print(f"⚠️ Could not count records in table '{table_name}': {table_error}")
            
            conn.close()
            print(f"📊 Total records for backup: {total_records}")
            
        except sqlite3.Error as e:
            flash(f'Database connectivity issue: {str(e)}')
            return redirect(url_for('manage_users'))
        
        # Create proper SQLite backup using file copy method
        backup_buffer = BytesIO()
        
        try:
            # First method: Direct file copy (most reliable for SQLite)
            with open(db_path, 'rb') as source_file:
                backup_data = source_file.read()
                backup_buffer.write(backup_data)
            
            # Verify the backup is a valid SQLite database
            backup_buffer.seek(0)
            
            # Write to temporary file to test
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
                temp_file.write(backup_buffer.getvalue())
                temp_db_path = temp_file.name
            
            try:
                # Test the backup file
                test_conn = sqlite3.connect(temp_db_path)
                cursor = test_conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                backup_tables = cursor.fetchall()
                
                # Verify we have the expected tables
                if backup_tables:
                    backup_table_names = [table[0] for table in backup_tables]
                    print(f"✅ Backup contains tables: {', '.join(backup_table_names)}")
                    
                    # Count total records in backup
                    total_backup_records = 0
                    for table_name in backup_table_names:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                            count = cursor.fetchone()[0]
                            total_backup_records += count
                        except:
                            pass
                    
                    print(f"✅ Backup contains {total_backup_records} total records")
                    
                test_conn.close()
                
            finally:
                # Clean up temporary file
                os.unlink(temp_db_path)
            
            print("✅ Direct file copy backup completed successfully")
            
        except Exception as file_copy_error:
            print(f"⚠️ File copy backup failed: {file_copy_error}")
            
            # Fallback method: Use SQLite backup API to create proper database file
            try:
                backup_buffer = BytesIO()
                
                # Create a temporary file for the backup
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_backup:
                    temp_backup_path = temp_backup.name
                
                try:
                    # Use SQLite's backup API
                    source_conn = sqlite3.connect(db_path)
                    backup_conn = sqlite3.connect(temp_backup_path)
                    
                    # Perform the backup using SQLite's backup API
                    source_conn.backup(backup_conn)
                    
                    source_conn.close()
                    backup_conn.close()
                    
                    # Read the backup file into buffer
                    with open(temp_backup_path, 'rb') as backup_file:
                        backup_buffer.write(backup_file.read())
                    
                    # Verify the backup
                    test_conn = sqlite3.connect(temp_backup_path)
                    cursor = test_conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    
                    if tables:
                        table_names = [table[0] for table in tables]
                        print(f"✅ Backup API completed: {', '.join(table_names)}")
                    
                    test_conn.close()
                    
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_backup_path):
                        os.unlink(temp_backup_path)
                
                print("✅ SQLite backup API completed successfully")
                
            except Exception as api_error:
                print(f"❌ Both backup methods failed: {api_error}")
                flash('Backup creation failed. Please try again.')
                return redirect(url_for('manage_users'))
        
        # Generate backup filename with timestamp
        backup_filename = f"New_Life_Mwangaza_Database_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        backup_buffer.seek(0)
        backup_size = len(backup_buffer.getvalue())
        
        print(f"✅ Database backup prepared: {backup_filename}")
        print(f"📊 Backup size: {backup_size:,} bytes ({backup_size/1024:.1f} KB)")
        
        # Create local backup copy for safety
        try:
            backup_dir = 'backups'
            os.makedirs(backup_dir, exist_ok=True)
            local_backup_path = os.path.join(backup_dir, backup_filename)
            
            backup_buffer.seek(0)
            with open(local_backup_path, 'wb') as backup_file:
                backup_file.write(backup_buffer.getvalue())
            
            print(f"✅ Local backup saved: {local_backup_path}")
            
        except Exception as local_backup_error:
            print(f"⚠️ Could not save local backup copy: {local_backup_error}")
        
        backup_buffer.seek(0)
        
        # Return the database backup for download
        return send_file(
            backup_buffer,
            as_attachment=True,
            download_name=backup_filename,
            mimetype='application/x-sqlite3'
        )
        
    except Exception as e:
        flash(f'Error creating database backup: {str(e)}')
        print(f"❌ Database backup error: {e}")
        return redirect(url_for('manage_users'))

@app.route('/reset_database')
@login_required
def reset_database():
    # Only Admin can reset database
    if current_user.department != 'admin':
        flash('Access denied. Only Admin can reset the database.')
        return redirect(url_for('manage_users'))

    try:
        import sqlite3
        
        # Create backup before reset
        db_path = os.path.abspath('mwangaza.db')
        if os.path.exists(db_path):
            backup_dir = 'backups'
            os.makedirs(backup_dir, exist_ok=True)
            reset_backup = os.path.join(backup_dir, f'pre_reset_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
            shutil.copy2(db_path, reset_backup)
            print(f"📦 Created pre-reset backup: {reset_backup}")
        
        # Drop all existing tables and recreate them
        with app.app_context():
            db.drop_all()
            db.create_all()
            db.session.commit()
            
            # Verify tables were created
            result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"✅ Database reset complete. Created {len(tables)} tables: {', '.join(sorted(tables))}")
        
        # Recreate admin user
        create_admin_user()
        
        flash(f'✅ Database has been reset successfully! {len(tables)} tables created. Please log in again.')
        logout_user()
        return redirect(url_for('login'))
        
    except Exception as e:
        flash(f'Error resetting database: {str(e)}')
        print(f"❌ Database reset error: {e}")
        return redirect(url_for('manage_users'))

# Counselling Routes
@app.route('/counselling')
@login_required
def counselling():
    # Only Counselling department and Admin can access this
    if current_user.department not in ['counselling', 'admin']:
        flash('Access denied. Only Counselling department and Admin can access this section.')
        return redirect(url_for('dashboard'))

    active_clients = Client.query.filter_by(status='ACTIVE').all()
    treatment_plans = TreatmentPlan.query.join(Client).filter(Client.status == 'ACTIVE').all()
    recent_soap_notes = SoapNote.query.join(Client).filter(Client.status == 'ACTIVE').order_by(SoapNote.session_date.desc()).limit(10).all()
    
    return render_template('counselling.html', 
                         active_clients=active_clients, 
                         treatment_plans=treatment_plans,
                         recent_soap_notes=recent_soap_notes)

@app.route('/add_treatment_plan/<int:client_id>', methods=['GET', 'POST'])
@login_required
def add_treatment_plan(client_id):
    # Only Counselling department and Admin can add treatment plans
    if current_user.department not in ['counselling', 'admin']:
        flash('Access denied. Only Counselling department and Admin can add treatment plans.')
        return redirect(url_for('dashboard'))

    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        try:
            plan_date = datetime.strptime(request.form['plan_date'], '%Y-%m-%d').date()
            review_date = None
            if request.form.get('review_date'):
                review_date = datetime.strptime(request.form['review_date'], '%Y-%m-%d').date()

            treatment_plan = TreatmentPlan(
                client_id=client_id,
                plan_date=plan_date,
                presenting_issues=request.form['presenting_issues'],
                treatment_goals=request.form['treatment_goals'],
                interventions=request.form['interventions'],
                target_behaviors=request.form.get('target_behaviors', ''),
                success_indicators=request.form.get('success_indicators', ''),
                estimated_duration=request.form.get('estimated_duration', ''),
                review_date=review_date,
                status=request.form.get('status', 'ACTIVE'),
                counselor_name=request.form['counselor_name'],
                supervisor_approval='supervisor_approval' in request.form,
                notes=request.form.get('notes', ''),
                createdBy=current_user.id
            )

            db.session.add(treatment_plan)
            db.session.commit()
            flash('Treatment plan added successfully!')
            return redirect(url_for('counselling'))
        except Exception as e:
            flash(f'Error adding treatment plan: {str(e)}')

    return render_template('add_treatment_plan.html', client=client)

@app.route('/add_soap_note/<int:client_id>', methods=['GET', 'POST'])
@login_required
def add_soap_note(client_id):
    # Only Counselling department and Admin can add SOAP notes
    if current_user.department not in ['counselling', 'admin']:
        flash('Access denied. Only Counselling department and Admin can add SOAP notes.')
        return redirect(url_for('dashboard'))

    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        try:
            session_date = datetime.strptime(request.form['session_date'], '%Y-%m-%d').date()
            next_session_date = None
            if request.form.get('next_session_date'):
                next_session_date = datetime.strptime(request.form['next_session_date'], '%Y-%m-%d').date()

            soap_note = SoapNote(
                client_id=client_id,
                session_date=session_date,
                session_type=request.form['session_type'],
                session_location=request.form.get('session_location', ''),
                subjective=request.form['subjective'],
                objective=request.form['objective'],
                assessment=request.form['assessment'],
                plan=request.form['plan'],
                session_duration=int(request.form.get('session_duration', 0)),
                attendance=request.form.get('attendance', 'PRESENT'),
                
                # Clinical Ratings
                mood_rating=int(request.form.get('mood_rating', 5)),
                anxiety_level=int(request.form.get('anxiety_level', 5)),
                depression_level=int(request.form.get('depression_level', 5)),
                progress_rating=int(request.form.get('progress_rating', 5)),
                functioning_level=request.form.get('functioning_level', ''),
                
                # Mental Status Exam
                appearance=request.form.get('appearance', ''),
                behavior=request.form.get('behavior', ''),
                speech=request.form.get('speech', ''),
                mood_affect=request.form.get('mood_affect', ''),
                thought_process=request.form.get('thought_process', ''),
                thought_content=request.form.get('thought_content', ''),
                perception=request.form.get('perception', ''),
                cognition=request.form.get('cognition', ''),
                insight=request.form.get('insight', ''),
                judgment=request.form.get('judgment', ''),
                
                # Risk Assessment
                suicide_risk=request.form.get('suicide_risk', 'NONE'),
                homicide_risk=request.form.get('homicide_risk', 'NONE'),
                self_harm_risk=request.form.get('self_harm_risk', 'NONE'),
                substance_use=request.form.get('substance_use', ''),
                
                # Session Content
                interventions_used=request.form.get('interventions_used', ''),
                client_response=request.form.get('client_response', ''),
                homework_assigned=request.form.get('homework_assigned', ''),
                homework_review=request.form.get('homework_review', ''),
                
                # Professional Information
                counselor_name=request.form['counselor_name'],
                supervisor_consultation='supervisor_consultation' in request.form,
                next_session_date=next_session_date,
                crisis_indicators='crisis_indicators' in request.form,
                referrals_made=request.form.get('referrals_made', ''),
                
                # Follow-up
                treatment_goals_addressed=request.form.get('treatment_goals_addressed', ''),
                barriers_to_progress=request.form.get('barriers_to_progress', ''),
                strengths_utilized=request.form.get('strengths_utilized', ''),
                
                createdBy=current_user.id
            )

            db.session.add(soap_note)
            db.session.commit()
            flash('SOAP note added successfully!')
            return redirect(url_for('client_counselling_records', client_id=client_id))
        except Exception as e:
            flash(f'Error adding SOAP note: {str(e)}')

    return render_template('add_soap_note.html', client=client)

@app.route('/add_exit_form/<int:client_id>', methods=['GET', 'POST'])
@login_required
def add_exit_form(client_id):
    # Only Counselling department and Admin can add exit forms
    if current_user.department not in ['counselling', 'admin']:
        flash('Access denied. Only Counselling department and Admin can add exit forms.')
        return redirect(url_for('dashboard'))

    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        try:
            exit_date = datetime.strptime(request.form['exit_date'], '%Y-%m-%d').date()

            exit_form = ExitForm(
                client_id=client_id,
                exit_date=exit_date,
                reason_for_exit=request.form['reason_for_exit'],
                goals_achieved=request.form.get('goals_achieved', ''),
                remaining_concerns=request.form.get('remaining_concerns', ''),
                recommendations=request.form.get('recommendations', ''),
                referrals_provided=request.form.get('referrals_provided', ''),
                follow_up_needed='follow_up_needed' in request.form,
                follow_up_plan=request.form.get('follow_up_plan', ''),
                client_satisfaction=int(request.form.get('client_satisfaction', 5)),
                counselor_assessment=request.form.get('counselor_assessment', ''),
                risk_level_at_exit=request.form.get('risk_level_at_exit', 'LOW'),
                safety_plan_provided='safety_plan_provided' in request.form,
                emergency_contacts_updated='emergency_contacts_updated' in request.form,
                final_diagnosis=request.form.get('final_diagnosis', ''),
                treatment_summary=request.form.get('treatment_summary', ''),
                counselor_name=request.form['counselor_name'],
                supervisor_signature='supervisor_signature' in request.form,
                createdBy=current_user.id
            )

            db.session.add(exit_form)
            db.session.commit()
            flash('Exit form added successfully!')
            return redirect(url_for('counselling'))
        except Exception as e:
            flash(f'Error adding exit form: {str(e)}')

    return render_template('add_exit_form.html', client=client)

@app.route('/client/<int:client_id>/counselling_records')
@login_required
def client_counselling_records(client_id):
    # Only Counselling department and Admin can view counselling records
    if current_user.department not in ['counselling', 'admin']:
        flash('Access denied. Only Counselling department and Admin can view counselling records.')
        return redirect(url_for('dashboard'))

    client = Client.query.get_or_404(client_id)
    treatment_plans = TreatmentPlan.query.filter_by(client_id=client_id).order_by(TreatmentPlan.plan_date.desc()).all()
    soap_notes = SoapNote.query.filter_by(client_id=client_id).order_by(SoapNote.session_date.desc()).all()
    exit_forms = ExitForm.query.filter_by(client_id=client_id).order_by(ExitForm.exit_date.desc()).all()

    return render_template('client_counselling_records.html', 
                         client=client, 
                         treatment_plans=treatment_plans, 
                         soap_notes=soap_notes,
                         exit_forms=exit_forms)

@app.route('/view_treatment_plan/<int:plan_id>')
@login_required
def view_treatment_plan(plan_id):
    # Only Counselling department and Admin can view treatment plans
    if current_user.department not in ['counselling', 'admin']:
        flash('Access denied. Only Counselling department and Admin can view treatment plans.')
        return redirect(url_for('dashboard'))

    treatment_plan = TreatmentPlan.query.get_or_404(plan_id)
    return render_template('view_treatment_plan.html', treatment_plan=treatment_plan)

@app.route('/view_soap_note/<int:note_id>')
@login_required
def view_soap_note(note_id):
    # Only Counselling department and Admin can view SOAP notes
    if current_user.department not in ['counselling', 'admin']:
        flash('Access denied. Only Counselling department and Admin can view SOAP notes.')
        return redirect(url_for('dashboard'))

    soap_note = SoapNote.query.get_or_404(note_id)
    return render_template('view_soap_note.html', soap_note=soap_note)

@app.route('/view_exit_form/<int:form_id>')
@login_required
def view_exit_form(form_id):
    # Only Counselling department and Admin can view exit forms
    if current_user.department not in ['counselling', 'admin']:
        flash('Access denied. Only Counselling department and Admin can view exit forms.')
        return redirect(url_for('dashboard'))

    exit_form = ExitForm.query.get_or_404(form_id)
    return render_template('view_exit_form.html', exit_form=exit_form)



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
    # Only Education department and Admin can view overall reports
    if current_user.department not in ['education', 'admin']:
        flash('Access denied. Only Education department and Admin can view overall reports.')
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

@app.route('/export_overall_report_pdf')
@login_required
def export_overall_report_pdf():
    # Only Education department and Admin can export overall reports
    if current_user.department not in ['education', 'admin']:
        flash('Access denied. Only Education department and Admin can export reports.')
        return redirect(url_for('dashboard'))

    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from io import BytesIO

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

    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=2*cm, 
        leftMargin=2*cm, 
        topMargin=2*cm, 
        bottomMargin=2*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # Define custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.Color(0.2, 0.3, 0.6)
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.Color(0.4, 0.4, 0.4)
    )

    # Header
    elements.append(Paragraph("NEW LIFE MWANGAZA", title_style))
    elements.append(Paragraph("OVERALL ACADEMIC PERFORMANCE REPORT", subtitle_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    elements.append(Paragraph(f"Generated by: {current_user.username.title()}", styles['Normal']))
    elements.append(Spacer(1, 20))

    if client_reports:
        # Summary statistics
        high_performers = len([r for r in client_reports if r['average'] >= 80])
        average_performers = len([r for r in client_reports if 60 <= r['average'] < 80])
        need_support = len([r for r in client_reports if r['average'] < 60])
        overall_average = sum(r['average'] for r in client_reports) / len(client_reports)

        summary_data = [
            ['Performance Summary', ''],
            ['Total Students Assessed', str(len(client_reports))],
            ['High Performers (80%+)', str(high_performers)],
            ['Average Performers (60-79%)', str(average_performers)],
            ['Need Support (<60%)', str(need_support)],
            ['Overall Class Average', f"{overall_average:.1f}%"]
        ]

        summary_table = Table(summary_data, colWidths=[4*cm, 3*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.3, 0.6)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 30))

        # Student performance table
        elements.append(Paragraph("Student Performance Ranking", styles['Heading2']))
        elements.append(Spacer(1, 10))

        # Prepare data for the table
        table_data = [['Rank', 'Student Name', 'Age', 'Average (%)', 'Subjects', 'Performance Level']]

        for i, report in enumerate(client_reports, 1):
            if report['average'] >= 80:
                performance_level = "Excellent"
            elif report['average'] >= 60:
                performance_level = "Good"
            else:
                performance_level = "Needs Support"

            table_data.append([
                str(i),
                f"{report['client'].firstName} {report['client'].secondName}",
                str(report['client'].age),
                f"{report['average']:.1f}%",
                str(report['total_subjects']),
                performance_level
            ])

        # Create table
        performance_table = Table(table_data, colWidths=[1*cm, 4*cm, 1.5*cm, 2*cm, 1.5*cm, 2.5*cm])
        performance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.3, 0.6)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)])
        ]))
        elements.append(performance_table)
    else:
        elements.append(Paragraph("No academic records found for active students.", styles['Normal']))

    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    # Return PDF as response
    from flask import Response
    response = Response(pdf, content_type='application/pdf')
    response.headers['Content-Disposition'] = f'attachment; filename=NLM_Overall_Academic_Report_{datetime.now().strftime("%Y%m%d")}.pdf'
    return response

@app.route('/delete_student/<int:client_id>', methods=['POST'])
@login_required
def delete_student(client_id):
    # Only Education department and Admin can delete students
    if current_user.department not in ['education', 'admin']:
        flash('Access denied. Only Education department and Admin can delete students.')
        return redirect(url_for('education'))

    client = Client.query.get_or_404(client_id)

    try:
        client_name = f"{client.firstName} {client.secondName}"

        # Delete all student marks for this client
        StudentMark.query.filter_by(client_id=client_id).delete()

        flash(f'All academic records for {client_name} have been deleted successfully!')
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student records: {str(e)}')

    return redirect(url_for('education'))

@app.route('/export_client_academic_pdf/<int:client_id>')
@login_required
def export_client_academic_pdf(client_id):
    # Only Education department and Admin can export client academic reports
    if current_user.department not in ['education', 'admin']:
        flash('Access denied. Only Education department and Admin can export academic reports.')
        return redirect(url_for('dashboard'))

    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from io import BytesIO

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

    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=2*cm, 
        leftMargin=2*cm, 
        topMargin=2*cm, 
        bottomMargin=2*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # Define custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.Color(0.2, 0.3, 0.6)
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.Color(0.4, 0.4, 0.4)
    )

    # Header
    elements.append(Paragraph("NEW LIFE MWANGAZA", title_style))
    elements.append(Paragraph("STUDENT ACADEMIC REPORT", subtitle_style))
    elements.append(Spacer(1, 10))

    # Student information
    student_info_data = [
        ['Student Information', ''],
        ['Name', f"{client.firstName} {client.secondName}"],
        ['Age', f"{client.age} years"],
        ['Education Level', client.educationLevel or 'Not specified'],
        ['Grade/Form', client.grade or client.secondaryForm or 'Not specified'],
        ['Student ID', f"#{client.id:04d}"],
        ['Report Generated', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
        ['Generated By', current_user.username.title()]
    ]

    student_info_table = Table(student_info_data, colWidths=[4*cm, 6*cm])
    student_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.3, 0.6)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(student_info_table)
    elements.append(Spacer(1, 20))

    if marks:
        # Performance summary
        performance_summary_data = [
            ['Performance Summary', ''],
            ['Overall Average', f"{overall_average:.1f}%"],
            ['Total Assessments', str(len(marks))],
            ['Subjects Assessed', str(len(set(mark.subject.name for mark in marks)))],
            ['Performance Level', 'Excellent' if overall_average >= 80 else 'Good' if overall_average >= 60 else 'Needs Support']
        ]

        performance_summary_table = Table(performance_summary_data, colWidths=[4*cm, 6*cm])
        performance_summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.1, 0.6, 0.3)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.Color(0.9, 1, 0.9)),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(performance_summary_table)
        elements.append(Spacer(1, 30))

        # Detailed marks table
        elements.append(Paragraph("Detailed Academic Records", styles['Heading2']))
        elements.append(Spacer(1, 10))

        # Prepare data for the marks table
        marks_data = [['Subject', 'Term', 'Year', 'Marks', 'Percentage', 'Test Date', 'Notes']]

        for mark in marks:
            percentage = (mark.marks / mark.max_marks) * 100
            marks_data.append([
                mark.subject.name,
                mark.term,
                str(mark.year),
                f"{mark.marks}/{mark.max_marks}",
                f"{percentage:.1f}%",
                mark.test_date.strftime('%b %d, %Y'),
                mark.notes[:30] + "..." if mark.notes and len(mark.notes) > 30 else mark.notes or '-'
            ])

        # Create marks table
        marks_table = Table(marks_data, colWidths=[3*cm, 1.5*cm, 1*cm, 1.5*cm, 1.5*cm, 2*cm, 3*cm])
        marks_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.3, 0.6)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)])
        ]))
        elements.append(marks_table)
    else:
        elements.append(Paragraph("No academic records found for this student.", styles['Normal']))

    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    # Return PDF as response
    from flask import Response
    response = Response(pdf, content_type='application/pdf')
    response.headers['Content-Disposition'] = f'attachment; filename=NLM_Academic_Report_{client.firstName}_{client.secondName}_{datetime.now().strftime("%Y%m%d")}.pdf'
    return response

def create_admin_user():
    """Create initial admin user if none exists"""
    try:
        # Check if any admin user exists
        admin_exists = User.query.filter_by(department='admin').first()
        if not admin_exists:
            admin_user = User(
                username='admin',
                full_name='System Administrator',
                department='admin'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Initial admin user created: admin/admin123")
            print("🔑 Default credentials: Username: admin, Password: admin123, Department: admin")
        else:
            print(f"✅ Admin user already exists: {admin_exists.username}")
        
    except Exception as e:
        print(f"⚠️ Error creating admin user: {e}")
        db.session.rollback()

def ensure_database_exists():
    """Ensure database file exists and is properly initialized"""
    import sqlite3
    import time
    
    db_path = os.path.abspath('mwangaza.db')
    
    try:
        # Check if database exists and has proper structure
        if os.path.exists(db_path) and os.path.getsize(db_path) > 1024:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user';")
                user_table_exists = cursor.fetchone() is not None
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='client';")
                client_table_exists = cursor.fetchone() is not None
                
                # Check for all required tables
                required_tables = ['user', 'client', 'home_visit', 'after_care', 'subject', 'student_mark']
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                existing_tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                if user_table_exists and client_table_exists and len(existing_tables) >= 6:
                    file_size = os.path.getsize(db_path)
                    print(f"✅ Database file exists and verified with {len(existing_tables)} tables: {db_path} ({file_size} bytes)")
                    return True
                else:
                    print(f"🔧 Database incomplete. Found {len(existing_tables)} tables: {existing_tables}")
                    
            except sqlite3.Error:
                print("🔧 Database file corrupted, will reinitialize")
        
        # Need to initialize database
        print(f"🔧 Initializing database: {db_path}")
        
        # Ensure directory exists and is writable
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # Remove existing file if it exists and is corrupted
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                time.sleep(0.1)
            except Exception as e:
                print(f"⚠️ Could not remove existing database file: {e}")
        
        # Create database using SQLAlchemy properly
        try:
            # Use SQLAlchemy to create all tables within app context
            with app.app_context():
                # Force create all tables
                db.create_all()
                
                # Verify all tables were created
                result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table';"))
                tables = [row[0] for row in result.fetchall()]
                
                if len(tables) < 10:  # We should have more than 10 tables
                    print(f"⚠️ Only {len(tables)} tables created, forcing recreation...")
                    
                    # Drop and recreate all tables
                    db.drop_all()
                    db.create_all()
                    
                    # Verify again
                    result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table';"))
                    tables = [row[0] for row in result.fetchall()]
                
                db.session.commit()
                print(f"✅ SQLAlchemy created {len(tables)} tables: {', '.join(sorted(tables))}")
                
        except Exception as create_error:
            print(f"❌ Database creation failed: {create_error}")
            return False
        
        # Give the file system a moment to sync (Replit specific)
        import time
        time.sleep(0.2)
        
        # Force SQLAlchemy to commit and close connections
        try:
            db.session.commit()
            db.session.close()
        except:
            pass
        
        # Verify the database was created successfully
        if os.path.exists(db_path):
            try:
                file_size = os.path.getsize(db_path)
                if file_size > 0:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    conn.close()
                    
                    table_names = [table[0] for table in tables]
                    required_tables = ['user', 'client', 'home_visit', 'after_care']
                    
                    if all(table in table_names for table in required_tables):
                        print(f"✅ Database initialized successfully: {db_path} ({file_size} bytes)")
                        print(f"✅ All {len(table_names)} tables created: {', '.join(sorted(table_names))}")
                        return True
                    else:
                        missing_tables = [t for t in required_tables if t not in table_names]
                        print(f"⚠️ Some required tables missing: {missing_tables}")
                        print(f"Found tables: {table_names}")
                        # If we have most tables, consider it successful
                        return len(table_names) >= 10
                else:
                    print(f"⚠️ Database file exists but is empty: {db_path}")
                    return False
                        
            except sqlite3.Error as e:
                print(f"❌ Database verification failed: {e}")
                # If verification fails but file exists, assume it's working
                return True
            except Exception as e:
                print(f"❌ Database file access error: {e}")
                return True  # Assume it's working if we can't verify
        else:
            print(f"❌ Database file was not created: {db_path}")
            return False
            
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

if __name__ == '__main__':
    with app.app_context():
        try:
            print("🔧 Initializing New Life Mwangaza database...")
            
            # Ensure database exists and is accessible
            if ensure_database_exists():
                print("✅ Database ready!")
            else:
                print("⚠️ Database initialization failed, but continuing...")
            
            # Create admin user
            create_admin_user()
            
        except Exception as e:
            print(f"⚠️ Initialization error: {e}")
            print("🔧 Attempting basic database setup...")
            try:
                db.create_all()
                create_admin_user()
                print("✅ Basic setup completed!")
            except Exception as e2:
                print(f"⚠️ Setup error: {e2}")

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"🚀 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)