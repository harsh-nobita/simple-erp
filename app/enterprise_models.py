from app import db
from datetime import datetime

# Enterprise models: Company, Department, User-Department association

class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    domain = db.Column(db.String(150), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    departments = db.relationship('Department', backref='company', cascade='all, delete-orphan', lazy='select')

    def __repr__(self):
        return f'<Company {self.name}>'


class Department(db.Model):
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('UserDepartment', backref='department', cascade='all, delete-orphan', lazy='select')

    def __repr__(self):
        return f'<Department {self.name} of Company {self.company_id}>'


class UserDepartment(db.Model):
    __tablename__ = 'user_department'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    role = db.Column(db.String(50))  # e.g., 'Lead', 'Member'
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserDepartment user={self.user_id} dept={self.department_id} role={self.role}>'
