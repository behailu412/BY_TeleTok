import eventlet
eventlet.monkey_patch()

import os


from flask import Flask, request, jsonify, session, send_file, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import hashlib

import json
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from sqlalchemy.orm import relationship

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'teletok-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database Configuration
# First try DATABASE_URL from environment (Railway/Aiven)
database_url = os.environ.get('DATABASE_URL')

# Handle different database URL formats
if database_url:
    # For Railway-style URLs that start with postgresql:// or mysql://
    if database_url.startswith('postgres://'):
        # Convert to psycopg2 format
        database_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif database_url.startswith('mysql://'):
        # Ensure PyMySQL driver is used
        database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
    elif database_url.startswith('postgresql://'):
        # Convert to psycopg2 format
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
else:
    # Fallback to Aiven configuration
    database_url = 'mysql+pymysql://avnadmin:AVNS_2KHrBK5j1HOPu4hc21y@mysql-d0f4f89-yifrubehailu02-c524.l.aivencloud.com:10271/defaultdb'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,
    'pool_pre_ping': True,
    'connect_args': {
        'charset': 'utf8mb4',
        # Only use SSL if required by the hosting platform
    }
}

# Allowed file extensions for profile photos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', logger=True, engineio_logger=True)
CORS(app)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_photo = db.Column(db.String(255), default='default.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_online = db.Column(db.Boolean, default=False)
    
    # Relationships - ensure proper back_populates
    contacts = relationship("Contact", 
                           foreign_keys="Contact.user_id", 
                           back_populates="user",
                           cascade="all, delete-orphan")
    
    # Message relationships remain the same
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    contacts = relationship("Contact", foreign_keys="Contact.user_id", back_populates="user")

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    is_seen = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - fixed to properly reference the User model
    user = relationship("User", foreign_keys=[user_id], back_populates="contacts")
    contact_user = relationship("User", foreign_keys=[contact_id])
    
    __table_args__ = (db.UniqueConstraint('user_id', 'contact_id', name='unique_contact'),)

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/health')
def health_check():
    """Health check endpoint to verify app and database connectivity"""
    try:
        with app.app_context():
            from sqlalchemy import text
            result = db.session.execute(text("SELECT 1"))
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Store online users {user_id: socket_id}
online_users = {}

# Serve HTML pages
@app.route('/')
def serve_index():
    return send_file('login.html')

@app.route('/login.html')
def serve_login():
    return send_file('login.html')

@app.route('/register.html')
def serve_register():
    return send_file('register.html')

@app.route('/dashboard.html')
def serve_dashboard():
    return send_file('dashboard.html')

@app.route('/settings.html')
def serve_settings():
    return send_file('settings.html')

# API Routes
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        phone = data.get('phone')
        password = data.get('password')
        
        if not username or not phone or not password:
            return jsonify({'success': False, 'message': 'All fields are required'})
    except Exception as e:
        print(f"Error processing registration request: {e}")
        return jsonify({'success': False, 'message': 'Invalid request format'})
    
    # Validate Ethiopian phone format
    import re
    phone_patterns = [
        r'^09\d{8}$',
        r'^\+2519\d{8}$',
        r'^2519\d{8}$',
        r'^07\d{8}$'
    ]
    
    is_valid = any(re.match(pattern, phone) for pattern in phone_patterns)
    if not is_valid:
        return jsonify({'success': False, 'message': 'Invalid Ethiopian phone number format'})
    
    # Check if phone already exists
    try:
        existing_user = User.query.filter_by(phone=phone).first()
    except Exception as e:
        print(f"Database query error (phone check): {e}")
        return jsonify({'success': False, 'message': 'Database error occurred'})
    
    if existing_user:
        return jsonify({'success': False, 'message': 'Phone number already registered'})
    
    # Check username
    try:
        existing_username = User.query.filter_by(username=username).first()
    except Exception as e:
        print(f"Database query error (username check): {e}")
        return jsonify({'success': False, 'message': 'Database error occurred'})
    
    if existing_username:
        return jsonify({'success': False, 'message': 'Username already taken'})
    
    # Create new user
    try:
        hashed_password = hash_password(password)
        new_user = User(
            username=username,
            phone=phone,
            password_hash=hashed_password,
            profile_photo='default.jpg'
        )
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Database commit error: {e}")
            return jsonify({'success': False, 'message': 'Registration failed due to database error'})
        
        # Create session
        session['user_id'] = new_user.id
        session['username'] = username
        session['phone'] = phone
        session['profile_photo'] = 'default.jpg'
        
        return jsonify({
            'success': True,
            'user_id': new_user.id,
            'username': username,
            'phone': phone,
            'profile_photo': 'default.jpg',
            'message': 'Registration successful'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {e}")
        return jsonify({'success': False, 'message': 'Registration failed'})

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        phone = data.get('phone')
        password = data.get('password')
        
        if not phone or not password:
            return jsonify({'success': False, 'message': 'Phone and password are required'})
    except Exception as e:
        print(f"Error processing login request: {e}")
        return jsonify({'success': False, 'message': 'Invalid request format'})
    
    hashed_password = hash_password(password)
    
    try:
        try:
            user = User.query.filter_by(phone=phone, password_hash=hashed_password).first()
        except Exception as db_error:
            print(f"Database query error (login): {db_error}")
            return jsonify({'success': False, 'message': 'Database error occurred'})
        
        if user:
            # Update last seen and online status
            user.last_seen = datetime.utcnow()
            user.is_online = True
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Database commit error in login: {e}")
                return jsonify({'success': False, 'message': 'Login failed due to database error'})
            
            session['user_id'] = user.id
            session['username'] = user.username
            session['phone'] = user.phone
            session['profile_photo'] = user.profile_photo
            
            return jsonify({
                'success': True,
                'user_id': user.id,
                'username': user.username,
                'phone': user.phone,
                'profile_photo': user.profile_photo
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid phone or password'})
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Login failed'})

@app.route('/logout', methods=['POST'])
def logout():
    user_id = session.get('user_id')
    if user_id:
        try:
            user = User.query.get(user_id)
            if user:
                user.is_online = False
                user.last_seen = datetime.utcnow()
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"Database commit error in logout: {e}")
                
                # Remove from online users
                if user_id in online_users:
                    del online_users[user_id]
                    
                    # Notify all contacts
                    socketio.emit('user_status', {
                        'user_id': user_id,
                        'is_online': False,
                        'last_seen': datetime.utcnow().isoformat()
                    })
        except Exception as e:
            print(f"Logout error: {e}")

    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/get_profile', methods=['GET'])
def get_profile():
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        user = User.query.get(user_id)
        
        if user:
            return jsonify({
                'success': True,
                'username': user.username,
                'phone': user.phone,
                'profile_photo': user.profile_photo
            })
        else:
            return jsonify({'success': False, 'message': 'User not found'})
    except Exception as e:
        print(f"Get profile error: {e}")
        return jsonify({'success': False, 'message': 'Failed to get profile'})

@app.route('/search_users', methods=['GET'])
def search_users():
    query = request.args.get('q', '')
    current_user_id = session.get('user_id')
    
    if not current_user_id:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    if not query or len(query) < 2:
        return jsonify({'success': False, 'message': 'Query too short'})
    
    try:
        # Search by username or phone
        users = User.query.filter(
            (User.username.like(f'%{query}%')) | (User.phone.like(f'%{query}%')),
            User.id != current_user_id
        ).limit(20).all()
        
        users_data = []
        for user in users:
            # Check if already connected
            is_contact = Contact.query.filter(
                ((Contact.user_id == current_user_id) & (Contact.contact_id == user.id)) |
                ((Contact.user_id == user.id) & (Contact.contact_id == current_user_id))
            ).first() is not None
            
            users_data.append({
                'id': user.id,
                'username': user.username,
                'phone': user.phone,
                'profile_photo': user.profile_photo,
                'is_online': user.is_online,
                'last_seen': user.last_seen.isoformat() if user.last_seen else None,
                'is_contact': is_contact
            })
        
        return jsonify({'success': True, 'users': users_data})
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'success': False, 'message': 'Search failed'})

@app.route('/add_contact', methods=['POST'])
def add_contact():
    data = request.json
    contact_id = data.get('contact_id')
    current_user_id = session.get('user_id')
    
    if not current_user_id or not contact_id:
        return jsonify({'success': False, 'message': 'Invalid request'})
    
    try:
        # Check if already connected (check both directions)
        existing_contact = Contact.query.filter_by(
            user_id=current_user_id, 
            contact_id=contact_id
        ).first()
        
        if existing_contact:
            return jsonify({'success': False, 'message': 'Already connected'})
        
        # Create contact (both directions for mutual connection)
        contact1 = Contact(user_id=current_user_id, contact_id=contact_id)
        contact2 = Contact(user_id=contact_id, contact_id=current_user_id)
        
        db.session.add(contact1)
        db.session.add(contact2)
        db.session.commit()
        
        # Get contact info for response
        contact_user = User.query.get(contact_id)
        if not contact_user:
            return jsonify({'success': False, 'message': 'Contact user not found'})
        
        contact_data = {
            'id': contact_user.id,
            'username': contact_user.username,
            'phone': contact_user.phone,
            'profile_photo': contact_user.profile_photo,
            'is_online': contact_user.is_online,
            'last_seen': contact_user.last_seen.isoformat() if contact_user.last_seen else None,
            'unread_count': 0
        }
        
        return jsonify({'success': True, 'contact': contact_data})
    except Exception as e:
        db.session.rollback()
        print(f"Add contact error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to add contact'})

@app.route('/get_contacts', methods=['GET'])
def get_contacts():
    current_user_id = session.get('user_id')
    
    if not current_user_id:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        # Get all contacts for the current user
        contacts = Contact.query.filter_by(user_id=current_user_id).all()
        
        if not contacts:
            return jsonify({'success': True, 'contacts': []})
        
        contacts_data = []
        for contact in contacts:
            # Get the contact user details
            user = User.query.get(contact.contact_id)
            if not user:
                continue
            
            # Calculate unread message count
            unread_count = Message.query.filter(
                Message.sender_id == user.id,
                Message.receiver_id == current_user_id,
                Message.is_seen == False
            ).count()
            
            contacts_data.append({
                'id': user.id,
                'username': user.username,
                'phone': user.phone,
                'profile_photo': user.profile_photo,
                'is_online': user.is_online,
                'last_seen': user.last_seen.isoformat() if user.last_seen else None,
                'unread_count': unread_count
            })
        
        return jsonify({'success': True, 'contacts': contacts_data})
    except Exception as e:
        print(f"Get contacts error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to get contacts'})
        
@app.route('/get_messages', methods=['GET'])
def get_messages():
    current_user_id = session.get('user_id')
    other_user_id = request.args.get('user_id')
    
    if not current_user_id or not other_user_id:
        return jsonify({'success': False, 'message': 'Invalid request'})
    
    try:
        # Get messages between two users
        messages = Message.query.filter(
            ((Message.sender_id == current_user_id) & (Message.receiver_id == other_user_id)) |
            ((Message.sender_id == other_user_id) & (Message.receiver_id == current_user_id))
        ).join(User, Message.sender_id == User.id).add_columns(
            Message, User.username.label('sender_name'), User.profile_photo.label('sender_photo')
        ).order_by(Message.sent_at).all()
        
        messages_data = []
        for msg, message, sender_name, sender_photo in messages:
            messages_data.append({
                'id': message.id,
                'sender_id': message.sender_id,
                'receiver_id': message.receiver_id,
                'message_text': message.message_text,
                'is_seen': message.is_seen,
                'sent_at': message.sent_at.isoformat(),
                'sender_name': sender_name,
                'sender_photo': sender_photo
            })
        
        # Mark messages as seen
        Message.query.filter(
            Message.sender_id == other_user_id,
            Message.receiver_id == current_user_id,
            Message.is_seen == False
        ).update({'is_seen': True})
        db.session.commit()
        
        return jsonify({'success': True, 'messages': messages_data})
    except Exception as e:
        print(f"Get messages error: {e}")
        return jsonify({'success': False, 'message': 'Failed to get messages'})

@app.route('/update_profile', methods=['POST'])
def update_profile():
    current_user_id = session.get('user_id')
    
    if not current_user_id:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    username = request.form.get('username')
    profile_photo = request.files.get('profile_photo')
    
    try:
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        if username and username.strip():
            username = username.strip()
            # Check if username is available
            existing_user = User.query.filter(
                User.username == username,
                User.id != current_user_id
            ).first()
            if existing_user:
                return jsonify({'success': False, 'message': 'Username already taken'})
            
            user.username = username
            session['username'] = username
        
        if profile_photo and allowed_file(profile_photo.filename):
            filename = secure_filename(profile_photo.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            profile_photo.save(filepath)
            
            user.profile_photo = unique_filename
            session['profile_photo'] = unique_filename
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'username': user.username,
            'profile_photo': user.profile_photo
        })
    except Exception as e:
        db.session.rollback()
        print(f"Update profile error: {e}")
        return jsonify({'success': False, 'message': 'Failed to update profile'})

@app.route('/uploads/<filename>')
def serve_upload(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except:
        return send_file('default.jpg')

@app.route('/default.jpg')
def serve_default():
    return send_file('default.jpg')

@app.route('/delete_message', methods=['POST'])
def delete_message():
    data = request.json
    message_id = data.get('message_id')
    user_id = data.get('user_id')
    
    if message_id is None or user_id is None:
        return jsonify({'success': False, 'message': 'Missing message_id or user_id'})
    
    try:
        message_id = int(message_id)
        user_id = int(user_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid message_id or user_id format'})
    
    try:
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({'success': False, 'message': 'Message not found'})
        
        if message.sender_id != user_id:
            return jsonify({'success': False, 'message': 'Unauthorized to delete this message'})
        
        db.session.delete(message)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Message deleted successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"Delete message error: {e}")
        return jsonify({'success': False, 'message': 'Failed to delete message'})

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    user_id = None
    for uid, sid in online_users.items():
        if sid == request.sid:
            user_id = uid
            break
    
    if user_id:
        del online_users[user_id]
        
        try:
            user = User.query.get(user_id)
            if user:
                user.is_online = False
                user.last_seen = datetime.utcnow()
                db.session.commit()
        except Exception as e:
            print(f"Update online status error: {e}")
        
        # Notify all clients about status change
        emit('user_status', {
            'user_id': user_id,
            'is_online': False,
            'last_seen': datetime.utcnow().isoformat()
        }, broadcast=True, namespace='/')

@socketio.on('user_online')
def handle_user_online(data):
    user_id = data.get('user_id')
    if user_id:
        online_users[user_id] = request.sid
        
        try:
            user = User.query.get(user_id)
            if user:
                user.is_online = True
                user.last_seen = datetime.utcnow()
                db.session.commit()
        except Exception as e:
            print(f"Update online status error: {e}")
        
        # Notify all clients about status change
        emit('user_status', {
            'user_id': user_id,
            'is_online': True
        }, broadcast=True, namespace='/')

@socketio.on('join_user_room')
def handle_join_user_room(data):
    user_id = data.get('user_id')
    if user_id:
        join_room(str(user_id))

@socketio.on('send_message')
def handle_send_message(data):
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    message_text = data.get('message_text')
    
    if not sender_id or not receiver_id or not message_text:
        return
    
    try:
        # Save message to database
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_text=message_text
        )
        db.session.add(message)
        db.session.commit()
        
        # Get message details with sender info
        message_with_sender = db.session.query(
            Message, User.username, User.profile_photo
        ).join(
            User, Message.sender_id == User.id
        ).filter(
            Message.id == message.id
        ).first()
        
        if message_with_sender:
            msg, sender_name, sender_photo = message_with_sender
            message_data = {
                'id': msg.id,
                'sender_id': msg.sender_id,
                'receiver_id': msg.receiver_id,
                'message_text': msg.message_text,
                'is_seen': msg.is_seen,
                'sent_at': msg.sent_at.isoformat() if isinstance(msg.sent_at, datetime) else msg.sent_at,
                'sender_name': sender_name,
                'sender_photo': sender_photo
            }
            
            # Send to receiver if they have a room
            emit('new_message', message_data, room=str(receiver_id))
            
            # Send to sender as confirmation
            emit('message_sent', message_data, room=request.sid)
            
            # Update sender's own chat if they're viewing the conversation
            emit('new_message_self', message_data, room=str(sender_id))
            
            # If receiver is online, mark message as seen
            if receiver_id in online_users:
                msg.is_seen = True
                db.session.commit()
                # Notify sender that message was seen
                emit('message_status', {
                    'message_id': msg.id,
                    'is_seen': True
                }, room=str(sender_id))
                
    except Exception as e:
        db.session.rollback()
        print(f"Send message error: {e}")

@socketio.on('message_seen')
def handle_message_seen(data):
    message_id = data.get('message_id')
    user_id = data.get('user_id')
    
    if not message_id or not user_id:
        return
    
    try:
        message = Message.query.get(message_id)
        if not message:
            return
        
        sender_id = message.sender_id
        
        # Mark message as seen
        message.is_seen = True
        db.session.commit()
        
        # Notify sender
        emit('message_status', {
            'message_id': message_id,
            'is_seen': True
        }, room=str(sender_id))
            
    except Exception as e:
        print(f"Message seen error: {e}")

@socketio.on('typing')
def handle_typing(data):
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    is_typing = data.get('is_typing')
    
    if sender_id and receiver_id:
        emit('user_typing', {
            'sender_id': sender_id,
            'is_typing': is_typing
        }, room=str(receiver_id))

with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {e}")
            import traceback
            traceback.print_exc()
    # Use PORT environment variable for Render.com
    port = int(os.environ.get('PORT', 5000))

    socketio.run(app, debug=False, host='0.0.0.0', port=port)







