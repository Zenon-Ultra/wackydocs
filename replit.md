# WackyDocs

## Overview

This is an educational platform called "WackyDocs" built with Flask that provides comprehensive study materials and tools for Korean students preparing for college entrance exams (수능) and school tests (내신). The platform features PDF resource management, vocabulary learning tools, quiz systems, and user management with role-based access control. The design uses a yellow theme color and responsive mobile-first design.

## User Preferences

Preferred communication style: Simple, everyday language.
Project name: "WackyDocs"
Theme color: Yellow
Admin access: Direct URL access at /admin (no navigation link)
Mobile app version: Progressive Web App (PWA) implementation for better accessibility

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM
- **Database**: SQLite/PostgreSQL (configurable via DATABASE_URL environment variable)
- **Authentication**: Flask-Login with session-based authentication
- **Forms**: Flask-WTF for form handling and validation
- **File Uploads**: Werkzeug for secure file handling with 16MB size limit

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 for responsive UI
- **Styling**: Custom CSS with Bootstrap components and Font Awesome icons
- **JavaScript**: Vanilla JavaScript for interactive features and AJAX functionality
- **Layout**: Mobile-first responsive design with Korean language support

### Security Features
- Password hashing using Werkzeug security utilities
- CSRF protection via Flask-WTF
- File upload validation and secure filename handling
- Session management with configurable secret key
- ProxyFix middleware for deployment behind reverse proxies

## Key Components

### User Management
- **User Model**: Stores user credentials, admin status, and relationships
- **Authentication**: Login/logout functionality with session persistence
- **Registration**: New user registration with email and username validation
- **Role-based Access**: Admin users have additional privileges for content management

### PDF Resource System
- **Request System**: Users can request specific study materials
- **Upload Management**: Admins can upload PDF files with metadata
- **Download Tracking**: Monitor resource usage and popularity
- **Categorization**: Resources organized by subject and type (수능/내신)

### Vocabulary Learning
- **Korean Vocabulary**: Classical Korean literature vocabulary with admin-managed categories
- **English Dictionary**: Real-time API integration with Free Dictionary API for complete word definitions
- **Audio Pronunciation**: Play button for English word pronunciation using API audio or Web Speech API fallback
- **Personal Word Lists**: Users can save words for later study with automatic API definitions
- **Quiz System**: Interactive quizzes for vocabulary reinforcement with JSON-serialized data

### Quiz Engine
- **Multiple Choice**: Randomized quiz questions with four options
- **Progress Tracking**: Score recording and performance analytics
- **Adaptive Content**: Quizzes based on user's vocabulary collection

### Admin Panel
- **Content Management**: Upload and organize PDF resources
- **User Management**: View and manage user accounts  
- **Request Processing**: Handle student resource requests
- **Korean Vocabulary Management**: Add/delete vocabulary by categories
- **Admin Account**: username=admin, password=admin123
- **Access Method**: Direct URL at /admin (no navigation menu item)

## Data Flow

### User Registration/Authentication Flow
1. User submits registration form with validation
2. Password is hashed and user record created
3. Login creates session and redirects to dashboard
4. Session persistence maintains authentication state

### Resource Request Flow
1. Student submits PDF resource request with subject/topic
2. Request stored in database with pending status
3. Admin reviews requests in admin panel
4. Admin uploads matching resources or rejects requests
5. Students notified of status changes

### Vocabulary Learning Flow
1. User searches for words in dictionary
2. Words can be added to personal vocabulary
3. Quiz system generates questions from user's word list
4. Scores are recorded and progress tracked

### File Upload Flow
1. Admin selects PDF file and enters metadata
2. File validation checks size and type
3. Secure filename generated and file stored
4. Database record created with file information
5. Resource becomes available for download

## External Dependencies

### Python Packages
- **Flask**: Web framework and core functionality
- **Flask-SQLAlchemy**: Database ORM and connection management
- **Flask-Login**: User session and authentication management
- **Flask-WTF**: Form handling, validation, and CSRF protection
- **Werkzeug**: Security utilities and file handling
- **Requests**: HTTP library for external API calls (Dictionary API)

### Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome 6**: Icon library for UI enhancement
- **Vanilla JavaScript**: Client-side interactivity without heavy dependencies

### Environment Configuration
- **DATABASE_URL**: Database connection string (defaults to SQLite)
- **SESSION_SECRET**: Secret key for session encryption
- **Upload directory**: File storage location for PDF resources

## Deployment Strategy

### Development Environment
- Flask development server with debug mode enabled
- SQLite database for local development and testing
- File uploads stored in local `uploads` directory
- Environment variables loaded from local configuration

### Production Considerations
- **Database**: PostgreSQL recommended for production deployment
- **File Storage**: Consider cloud storage for uploaded files
- **Reverse Proxy**: ProxyFix middleware configured for nginx/Apache
- **Session Security**: Strong secret key and secure session configuration
- **Database Connection**: Connection pooling and automatic reconnection configured

### Scalability Features
- Database connection pooling with automatic ping checks
- Modular route organization for maintainability
- Separated concerns with dedicated forms and models modules
- Static file serving optimized for production deployment

The application follows Flask best practices with clear separation of concerns, making it maintainable and scalable for educational use cases. The Korean language interface and education-focused features make it specifically tailored for Korean students' learning needs.