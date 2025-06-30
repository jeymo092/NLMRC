
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mwangaza.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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
    return render_template('dashboard.html', clients=clients, user=current_user)

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
    return render_template('client_detail.html', client=client)

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
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from io import BytesIO
    import os
    
    client = Client.query.get_or_404(client_id)
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Add logo and header
    elements.append(Paragraph("NEW LIFE MWANGAZA", title_style))
    elements.append(Paragraph("Client Information Report", styles['Heading2']))
    elements.append(Spacer(1, 20))
    
    # Client basic information
    elements.append(Paragraph("Personal Information", heading_style))
    personal_data = [
        ['Full Name:', f"{client.firstName} {client.secondName}"],
        ['Nickname:', client.nickname or 'N/A'],
        ['Date of Birth:', str(client.dateOfBirth)],
        ['Age:', f"{client.age} years"],
        ['Status:', client.status],
        ['Registration Date:', client.createdAt.strftime('%Y-%m-%d %H:%M') if client.createdAt else 'N/A']
    ]
    
    personal_table = Table(personal_data, colWidths=[2*inch, 3*inch])
    personal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(personal_table)
    elements.append(Spacer(1, 20))
    
    # Admission information
    elements.append(Paragraph("Admission Information", heading_style))
    admission_data = [
        ['Admission Type:', client.admissionType],
        ['Intake Number:', str(client.intake)]
    ]
    
    if client.admissionType == 'REFERRAL':
        admission_data.extend([
            ['Referral Institution:', client.referralInstitution or 'N/A'],
            ['Referral Contact:', client.referralContact or 'N/A']
        ])
    else:
        admission_data.append(['Street Name:', client.streetName or 'N/A'])
    
    admission_table = Table(admission_data, colWidths=[2*inch, 3*inch])
    admission_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(admission_table)
    elements.append(Spacer(1, 20))
    
    # Education information
    if client.educationLevel or client.grade or client.secondaryForm:
        elements.append(Paragraph("Education Information", heading_style))
        education_data = []
        if client.educationLevel:
            education_data.append(['Education Level:', client.educationLevel])
        if client.grade:
            education_data.append(['Grade:', client.grade])
        if client.secondaryForm:
            education_data.append(['Secondary Form:', client.secondaryForm])
        
        education_table = Table(education_data, colWidths=[2*inch, 3*inch])
        education_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(education_table)
        elements.append(Spacer(1, 20))
    
    # Parent/Guardian information
    if client.parentGuardianName or client.parentGuardianLocation or client.parentGuardianContact:
        elements.append(Paragraph("Parent/Guardian Information", heading_style))
        parent_data = []
        if client.parentGuardianName:
            parent_data.append(['Name:', client.parentGuardianName])
        if client.parentGuardianLocation:
            parent_data.append(['Location:', client.parentGuardianLocation])
        if client.parentGuardianContact:
            parent_data.append(['Contact:', client.parentGuardianContact])
        
        parent_table = Table(parent_data, colWidths=[2*inch, 3*inch])
        parent_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(parent_table)
    
    # Add footer
    elements.append(Spacer(1, 40))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by {current_user.username}", footer_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF data
    pdf = buffer.getvalue()
    buffer.close()
    
    # Return PDF as response
    from flask import Response
    response = Response(pdf, content_type='application/pdf')
    response.headers['Content-Disposition'] = f'attachment; filename=client_{client.firstName}_{client.secondName}_report.pdf'
    return response

@app.route('/aftercare')
@login_required
def aftercare():
    # Only Social Workers can access aftercare
    if current_user.department != 'socialworkers':
        flash('Access denied. Only Social Workers can access aftercare records.')
        return redirect(url_for('dashboard'))
    
    aftercare_records = AfterCare.query.join(Client).all()
    return render_template('aftercare.html', aftercare_records=aftercare_records)

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

def create_default_users():
    """Create default users for each department"""
    departments = ['admin', 'socialworkers', 'counselling', 'education', 'empowerment']
    
    for dept in departments:
        if not User.query.filter_by(username=dept).first():
            user = User(username=dept, department=dept)
            user.set_password('password123')  # Change this in production!
            db.session.add(user)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_users()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
