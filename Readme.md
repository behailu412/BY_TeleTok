# TeleTok - Modern Real-Time Chat Platform


TeleTok is a feature-rich, real-time chat application built with modern web technologies. Designed for seamless communication with a focus on Ethiopian phone number support and an intuitive user interface.

## ✨ Features

### 🔐 **Authentication & Security**
- **Secure Registration** with Ethiopian phone validation (09, +2519, 07 formats)
- **Phone Number Uniqueness** - Each number can only register once
- **Password Hashing** using SHA-256 for secure storage
- **Session-based Authentication** with proper logout handling

### 💬 **Real-Time Chat**
- **Instant Messaging** via WebSocket (Socket.IO)
- **Online/Offline Status** with real-time updates
- **Message Status Indicators** (✓ Sent, ✓✓ Seen)
- **Typing Indicators** when contacts are typing
- **Unread Message Count** badges

### 👥 **Contacts & Search**
- **Contact Management** - Add and manage contacts
- **Smart Search** by username or phone number
- **Mutual Connections** - Contacts work both ways
- **Profile Visibility** - See contact profile photos and status

### 🎨 **User Interface**
- **Modern Design** with gradient aesthetics
- **Fully Responsive** - Works on desktop, tablet, and mobile
- **Mobile Hamburger Menu** for easy navigation
- **Professional Toast Notifications** for user feedback
- **Animated Confirmation Modals**

### 😊 **Enhanced Emoji System**
- **60+ Emojis** organized into 8 categories (Faces, Hands, Hearts, Flowers, Animals, Food, Objects, Symbols)
- **Large Emoji Display** in messages (2x normal size)
- **Modern Emoji Picker** with category tabs
- **Emoji-Only Messages** display extra large for emphasis

### 📋 **Message Features**
- **Copy Messages** with one click
- **Large, Bold Text** for better readability
- **Clean Copy Functionality** - No HTML formatting in copied text
- **Professional Toast Feedback** when copying

### ⚙️ **Profile Management**
- **Update Profile Photo** with file upload support
- **Change Username** with real-time validation
- **Professional Logout Confirmation** modal

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- MySQL 8.0 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd TeleTok
```

2. **Set up Python environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

3. **Configure Database**
```bash
# Update database credentials in app.py (if needed)
# Default credentials:
# Host: localhost
# User: root
# Password: password12
# Database: teletok_db

# Run database setup
python db_setup.py
```

4. **Run the Application**
```bash
python app.py
```

5. **Access the Application**
- Open your browser and go to: `http://localhost:5000`
- The application will automatically serve the login page

## 📁 Project Structure

```
TeleTok/
│
├── app.py                 # Main Flask application (backend)
├── db_setup.py            # Database initializer
├── schema.sql             # Database schema definition
├── requirements.txt       # Python dependencies
├── default.jpg           # Default profile photo
│
├── login.html            # Login page (with Ethiopian phone validation)
├── register.html         # Registration page
├── dashboard.html        # Main chat interface (real-time features)
└── settings.html         # Profile settings page
```

## 🗄️ Database Schema

The application uses three main tables:

### **Users Table**
- `id` - Primary key
- `username` - Unique username
- `phone` - Unique Ethiopian phone number
- `password_hash` - Hashed password
- `profile_photo` - Profile image filename
- `is_online` - Online status
- `last_seen` - Last activity timestamp

### **Messages Table**
- `id` - Primary key
- `sender_id` - Foreign key to users
- `receiver_id` - Foreign key to users
- `message_text` - Message content
- `is_seen` - Read status
- `sent_at` - Timestamp

### **Contacts Table**
- `id` - Primary key
- `user_id` - User ID
- `contact_id` - Contact's user ID
- Mutual relationship tracking

## 🔧 Configuration

### Database Configuration
Edit `app.py` to modify database credentials:
```python
def get_db_connection():
    return pymysql.connect(
        host='localhost',      # Database host
        user='root',           # Database username
        password='password12', # Database password
        database='teletok_db', # Database name
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
```

### Server Configuration
The application runs on:
- **Host:** 0.0.0.0 (accessible from network)
- **Port:** 5000
- **Debug Mode:** Enabled (for development)

To change these settings, modify the bottom of `app.py`:
```python
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
```

## 📱 Mobile Features

### Responsive Design
- **Sidebar Navigation** - Collapses to hamburger menu on mobile
- **Touch-Friendly** - Large buttons and interactive elements
- **Adaptive Layout** - Messages adjust width based on screen size

### Mobile-Specific Features
- **Hamburger Menu** - Access contacts from chat view
- **Optimized Emoji Picker** - Responsive grid layout
- **Touch Gestures** - Easy message copying

## 🎯 Ethiopian Phone Validation

TeleTok supports multiple Ethiopian phone formats:
- **09XXXXXXXX** (10 digits)
- **+2519XXXXXXXX** (13 digits)
- **2519XXXXXXXX** (12 digits)
- **07XXXXXXXX** (10 digits)

The system automatically validates and formats phone numbers during registration.

## 🛠️ Development

### Running in Development Mode
```bash
# With auto-reload for development
python app.py
# The server will restart on code changes
```

### Testing Features
1. **Register two users** with different Ethiopian phone numbers
2. **Search and add contacts** between users
3. **Test real-time messaging** between different browser windows
4. **Verify online/offline status** updates
5. **Test mobile responsiveness** using browser developer tools

### Common Development Tasks

#### Adding New Emojis
Edit the `emojiData` object in `dashboard.html`:
```javascript
const emojiData = {
    'category_name': [
        '😀', '😃', '😄'  // Add emojis here
    ]
    // Add more categories as needed
};
```

#### Modifying Styling
All CSS is internal in each HTML file. Look for:
- `dashboard.html` - Main chat interface styling
- `login.html` & `register.html` - Authentication pages styling
- `settings.html` - Profile settings styling

#### Extending Features
The modular structure makes it easy to add:
- New API endpoints in `app.py`
- Additional database tables in `schema.sql`
- New frontend features in respective HTML files

## 🔒 Security Features

### Implemented Security Measures
1. **Password Hashing** - Passwords never stored in plain text
2. **Session Management** - Secure session handling
3. **Input Validation** - Server-side validation of all inputs
4. **SQL Injection Prevention** - Parameterized queries
5. **File Upload Restrictions** - Image type and size validation

### Security Best Practices
- Never commit sensitive credentials to version control
- Use environment variables for production credentials
- Implement rate limiting in production
- Add CSRF protection for production deployment

## 📊 Performance Optimizations

### Frontend Optimizations
- **Debounced Search** - Reduces API calls during typing
- **WebSocket Connection** - Real-time updates without polling
- **Efficient DOM Updates** - Minimal re-renders

### Backend Optimizations
- **Database Connection Pooling** - Reusable connections
- **Indexed Queries** - Fast message and contact retrieval
- **Efficient Socket.IO** - Room-based broadcasting

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection Error
```
Error: Can't connect to MySQL server
```
**Solution:** 
- Verify MySQL is running: `sudo systemctl status mysql`
- Check credentials in `app.py`
- Ensure database exists: `teletok_db`

#### 2. Port Already in Use
```
Error: Address already in use
```
**Solution:**
```bash
# Kill process on port 5000
sudo lsof -ti:5000 | xargs kill -9
# Or change port in app.py
```

#### 3. Module Not Found
```
Error: No module named 'flask_socketio'
```
**Solution:**
```bash
pip install -r requirements.txt
```

#### 4. Emoji Picker Not Showing
**Solution:**
- Check browser console for JavaScript errors
- Ensure all dependencies are loaded
- Verify emoji button click handler is attached

### Debug Mode
Enable Flask debug mode in `app.py`:
```python
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
```

## 📈 Future Enhancements

### Planned Features
1. **Group Chats** - Multi-user conversations
2. **File Sharing** - Image and document uploads
3. **Voice Messages** - Audio recording and sending
4. **Video Calls** - WebRTC integration
5. **Message Reactions** - Like/love reactions to messages
6. **Message Editing** - Edit sent messages
7. **Dark Mode** - Theme switching
8. **Message Search** - Search within conversations
9. **Chat Backup** - Export conversation history
10. **Admin Panel** - User management interface

### Performance Improvements
1. **Message Pagination** - Load messages in chunks
2. **Image Compression** - Optimize profile photo uploads
3. **CDN Integration** - Faster static file delivery
4. **Database Caching** - Redis integration for frequent queries

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

### Contribution Guidelines
- Follow existing code style
- Add comments for complex logic
- Update documentation as needed
- Test changes thoroughly
- Ensure no breaking changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Flask Community** for the excellent web framework
- **Socket.IO** for real-time communication capabilities
- **Font Awesome** for beautiful icons
- **All Contributors** who help improve TeleTok

## 📞 Support

For support, feature requests, or bug reports:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review existing issues
3. Create a new issue with detailed information

---

**TeleTok** - Connecting people through seamless, real-time communication. Built with ❤️ for the Ethiopian community and beyond.

Last Updated: November 2018 E.C