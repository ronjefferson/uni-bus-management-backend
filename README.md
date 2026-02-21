# University Bus Pass & Attendance Management System

A comprehensive Django REST API for managing university student transportation, bus pass requests, and attendance tracking. Students, parents, and administrators can monitor and manage access to university shuttle services.

## Features

### Student Features
- **User Registration & Authentication**: JWT-based authentication with secure token management
- **Schedule Management**: View assigned bus routes and schedules
- **Attendance Tracking**: Automatic logging of bus boarding with inbound/outbound tracking
- **Bus Pass Requests**: Submit requests for temporary or emergency bus pass access
- **Parent Linking**: Allow parents to monitor transportation activity
- **Push Notifications**: Receive real-time updates via Firebase Cloud Messaging (FCM)

### Parent Portal
- **Child Monitoring**: Link and view registered students (children)
- **Attendance History**: Access attendance logs for linked students
- **Schedule Viewing**: View bus schedules for each child
- **Notifications**: Receive alerts about child activities

### Admin Dashboard
- **Student Management**: View, search, and manage all student accounts
- **Bus Pass Management**: Approve/reject student requests or create emergency passes
- **Attendance Reports**: Generate and analyze attendance data
- **Scan Log Monitoring**: Review all bus boarding records
- **Parent Management**: Oversee parent accounts and child-parent relationships
- **Override Capability**: Create emergency passes for students without automatic requests

## Technology Stack

* [![Django][Django-badge]][Django-url]
* [![Django REST Framework][DRF-badge]][DRF-url]
* [![PostgreSQL][PostgreSQL-badge]][PostgreSQL-url]
* [![JWT][JWT-badge]][JWT-url]
* [![Firebase][Firebase-badge]][Firebase-url]
* [![Pandas][Pandas-badge]][Pandas-url]
* [![Docker][Docker-badge]][Docker-url]
* [![Docker Compose][DockerCompose-badge]][DockerCompose-url]
* [![Django CORS Headers][CORS-badge]][CORS-url]
* [![Django Filters][Filters-badge]][Filters-url]

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Docker & Docker Compose (for containerized deployment)
- Git

## Installation

### Local Development Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd SWE6202_Project
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r myproject/requirements.txt
   ```

4. **Environment Configuration**
   
   Create a `.env` file in the root directory:
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=1
   DATABASE_URL=postgresql://user:password@localhost:5432/bus_management
   DJANGO_SUPERUSER_USERNAME=admin
   DJANGO_SUPERUSER_PASSWORD=admin
   DJANGO_SUPERUSER_EMAIL=admin@example.com
   ```

5. **Database Setup**
   ```bash
   cd myproject
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser  # Create admin account
   ```

6. **Load Sample Data** (Optional)
   ```bash
   python manage.py shell
   >>> from django.contrib.auth.models import User
   >>> # Import students/parents from CSV files
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```
   The API will be available at `http://localhost:8000/api/`

### Docker Deployment

1. **Configure Environment**
   
   Create a `.env.docker` file with your configuration

2. **Build and Run**
   ```bash
   docker-compose up --build
   ```

3. **Run Migrations in Docker**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

4. **Access the Application**
   - API: `http://localhost:8000/api/`
   - Admin Panel: `http://localhost:8000/admin/`

## Firebase Setup

1. **Generate Firebase Credentials**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a service account
   - Download the JSON credentials file

2. **Place Credentials File**
   ```bash
   cp /path/to/firebase_credentials.json myproject/firebase_credentials.json
   ```

3. **Enable Firebase Services**
   - Enable Cloud Messaging (for push notifications)
   - Configure your FCM settings in Firebase Console

## API Authentication

The API uses **JWT (JSON Web Tokens)** for authentication.

### Obtain Token
```bash
POST /api/token/
Content-Type: application/json

{
  "username": "student_username",
  "password": "password"
}

# Response
{
  "user": {
    "id": 1,
    "username": "student_username",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
  }
}
```

### Use Token in Requests
```bash
Authorization: Bearer <access_token>
```

### Refresh Token
```bash
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "refresh_token"
}
```

### Logout
```bash
POST /api/token/logout/
Authorization: Bearer <access_token>
```

## API Endpoints

### Authentication
- `POST /api/token/` - Obtain access and refresh tokens
- `POST /api/token/refresh/` - Refresh access token
- `POST /api/token/logout/` - Logout and blacklist token

### Student Endpoints
- `GET /api/students/me/` - Get student profile
- `GET /api/students/schedule/` - Get student's bus schedule
- `GET /api/students/me/logs/` - Get attendance history
- `GET /api/students/me/parents/` - List linked parents
- `GET/POST /api/students/requests/` - Manage bus pass requests

### Parent Endpoints
- `POST /api/parents/register/` - Register new parent account
- `GET /api/parents/me/` - Get parent profile
- `GET /api/parents/me/children/` - List linked children
- `POST /api/parents/me/link-child/` - Link child to parent
- `GET /api/parents/me/children/<university_id>/logs/` - Get child's attendance logs

### Admin Endpoints
- `GET /api/admin/students/` - List all students (paginated)
- `GET /api/admin/parents/` - List all parents (paginated)
- `GET /api/admin/students/<university_id>/` - Get student details
- `GET /api/admin/parents/<id>/` - Get parent details
- `POST /api/admin/bus-pass/create/` - Create emergency bus pass
- `GET /api/admin/scan-logs/` - View all attendance logs
- `GET /api/admin/requests/` - View all pass requests
- `POST /api/admin/requests/<id>/approve/` - Approve pass request
- `POST /api/admin/requests/<id>/reject/` - Reject pass request
- `GET /api/admin/student-report/` - Generate attendance reports

### Notifications
- `POST /api/notifications/register-device/` - Register FCM token for push notifications

### Scan Logger
- `POST /api/logs/scan/` - Log a bus scan event (used by bus hardware)

## Usage Examples

### Student Login and View Schedule
```bash
# 1. Login
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "student1", "password": "pass123"}'

# 2. View Schedule
curl -X GET http://localhost:8000/api/students/schedule/ \
  -H "Authorization: Bearer <access_token>"
```

### Submit Bus Pass Request
```bash
curl -X POST http://localhost:8000/api/students/requests/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "requested_valid_from": "2026-02-22T08:00:00Z",
    "requested_valid_until": "2026-02-28T17:00:00Z",
    "reason": "Special event attendance"
  }'
```

### Admin Approve Bus Pass Request
```bash
curl -X POST http://localhost:8000/api/admin/requests/1/approve/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "approved_valid_from": "2026-02-22T08:00:00Z",
    "approved_valid_until": "2026-02-28T17:00:00Z",
    "admin_notes": "Approved for event"
  }'
```

### Register Device for Push Notifications
```bash
curl -X POST http://localhost:8000/api/notifications/register-device/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"token": "fcm_device_token_here"}'
```

## Project Structure

```
SWE6202_Project/
├── myproject/                    # Django project root
│   ├── api/                     # Main API application
│   │   ├── migrations/          # Database migrations
│   │   ├── models.py            # Database models
│   │   ├── views.py             # API views and endpoints
│   │   ├── serializers.py       # DRF serializers
│   │   ├── urls.py              # API routing
│   │   ├── permissions.py       # Custom permissions
│   │   ├── authentication.py    # Auth backends
│   │   ├── schedule_utils.py    # Schedule utility functions
│   │   └── tests.py             # Unit tests
│   ├── myproject/               # Django settings
│   │   ├── settings.py          # Project configuration
│   │   ├── urls.py              # Main URL routing
│   │   ├── wsgi.py              # WSGI application
│   │   └── asgi.py              # ASGI application
│   ├── manage.py                # Django CLI
│   └── requirements.txt         # Python dependencies
├── docker-compose.yml           # Docker Compose configuration
├── Dockerfile                   # Docker image definition
├── docker-entrypoint.sh         # Docker startup script
├── firebase_credentials.json    # Firebase credentials (Not currently used)
├── students.csv                 # Sample student data
├── schedules.csv                # Bus schedules
└── README.md                    # This file
```

## Sample Data Files (CSV)

### students.csv
This CSV file is used for **quick testing and development purposes** to simulate a university's student database. Instead of manually creating student accounts one by one, the system can bulk-import student records from this file, mimicking how real universities provision student accounts from their existing enrollment systems.

**Purpose:**
- **Development & Testing**: Quickly populate the database with test student records without manual entry
- **School Integration Simulation**: Simulates how student records would be imported from a school's student information system (SIS)
- **Demo Data**: Provides sample data for demonstration, screenshots, and testing features

**Format:**
The CSV should contain columns like:
```
university_id,first_name,last_name,university_email,personal_email,schedule_id
S001,John,Doe,john.doe@university.edu,john@example.com,BUS_ROUTE_1
S002,Jane,Smith,jane.smith@university.edu,jane@example.com,BUS_ROUTE_2
```

**How to Use:**
1. Place student records in `students.csv`
2. Run a management command or import script to bulk-create Student objects in the database
3. Each student gets a unique registration code automatically generated

### schedules.csv
This file contains bus route schedules and timing information that students need to view.

**Purpose:**
- Store predefined bus routes and their schedules
- Link schedules to students for consistent timetable information
- Enable schedule queries and reporting

**Format:**
```
schedule_id,route_name,departure_time,arrival_time,stops,frequency
BUS_ROUTE_1,Downtown Route,08:00,17:00,"Stop A, Stop B, Stop C",Weekdays
BUS_ROUTE_2,Campus Loop,08:30,17:30,"Stop A, Stop D, Stop E",Daily
```

**Note:** In a production environment, these CSV files would be replaced with automated imports from the university's official student information system (SIS) and transportation system, but for development and testing, they serve as convenient sample data sources.

## Database Models

### Student
- `university_id` - Unique university identifier
- `user` - Link to Django User account
- `university_email` - Official email
- `personal_email` - Personal contact email
- `registration_code` - Unique registration code for linking
- `schedule_id` - Link to bus schedule

### Parent
- `user` - Link to Django User account
- `phone_number` - Contact number
- `children` - Many-to-many relationship with Students

### AttendanceLog
- `student` - Link to Student
- `timestamp` - Scan time
- `direction` - INBOUND or OUTBOUND
- `bus_number` - Bus identifier
- `status` - VALID, INVALID, or OVERRIDE

### StudentBusPass
- `student` - Link to Student
- `valid_from` - Start of validity period
- `valid_until` - End of validity period
- `used_at` - When the pass was used
- `admin_who_granted` - Admin who created the pass
- `reason` - Reason for granting pass

### BusPassRequest
- `student` - Link to Student
- `status` - PENDING, APPROVED, or REJECTED
- `requested_valid_from` - Student's requested start date
- `requested_valid_until` - Student's requested end date
- `approved_valid_from` - Admin's approved start date (if different)
- `approved_valid_until` - Admin's approved end date (if different)
- `admin_notes` - Notes from admin review

## Configuration

### Settings File (`myproject/settings.py`)

Key settings to configure:

```python
# Security
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', '0') == '1'
ALLOWED_HOSTS = ['*']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bus_management',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ALGORITHM': 'HS256',
}
```

## Testing

Run the test suite:
```bash
python manage.py test api
```

Run with coverage:
```bash
coverage run --source='.' manage.py test api
coverage report
```

## Troubleshooting

### Firebase Connection Issues
- Verify `firebase_credentials.json` is in the correct location
- Check Firebase service account has Cloud Messaging enabled
- Review Django logs for initialization messages

### Database Connection Errors
- Ensure PostgreSQL is running
- Verify DATABASE_URL in environment
- Check database user has proper permissions

### Migration Issues
```bash
# Reset migrations (development only)
python manage.py migrate api zero
python manage.py migrate
```

### Port Already in Use
```bash
# Change port
python manage.py runserver 8001
```

## Security Considerations

- Store `firebase_credentials.json` securely (not in version control)
- Use environment variables for sensitive configuration
- Enable HTTPS in production
- Set `DEBUG=False` in production
- Use strong SECRET_KEY value
- Implement rate limiting for API endpoints
- Regularly update dependencies

## Performance Optimization

- Database indexes on frequently queried fields (university_id, timestamp)
- Pagination for list endpoints (default: 10 items per page)
- Django ORM query optimization with `select_related()` and `prefetch_related()`
- Redis caching for schedule data (optional)

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Submit pull request

## License

This project is part of the SWE6202 course at [Your University].



[Django-badge]: https://img.shields.io/badge/Django-4.x-092E20?style=for-the-badge&logo=django&logoColor=white
[Django-url]: https://www.djangoproject.com/

[DRF-badge]: https://img.shields.io/badge/Django%20REST%20Framework-DRF-red?style=for-the-badge&logo=django&logoColor=white
[DRF-url]: https://www.django-rest-framework.org/

[PostgreSQL-badge]: https://img.shields.io/badge/PostgreSQL-Database-316192?style=for-the-badge&logo=postgresql&logoColor=white
[PostgreSQL-url]: https://www.postgresql.org/

[JWT-badge]: https://img.shields.io/badge/JWT-Authentication-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white
[JWT-url]: https://jwt.io/

[Firebase-badge]: https://img.shields.io/badge/Firebase-Admin%20SDK-FFCA28?style=for-the-badge&logo=firebase&logoColor=black
[Firebase-url]: https://firebase.google.com/

[Pandas-badge]: https://img.shields.io/badge/Pandas-Data%20Processing-150458?style=for-the-badge&logo=pandas&logoColor=white
[Pandas-url]: https://pandas.pydata.org/

[Docker-badge]: https://img.shields.io/badge/Docker-Containerization-2496ED?style=for-the-badge&logo=docker&logoColor=white
[Docker-url]: https://www.docker.com/

[DockerCompose-badge]: https://img.shields.io/badge/Docker%20Compose-Orchestration-2496ED?style=for-the-badge&logo=docker&logoColor=white
[DockerCompose-url]: https://docs.docker.com/compose/

[CORS-badge]: https://img.shields.io/badge/Django%20CORS-Headers-092E20?style=for-the-badge&logo=django&logoColor=white
[CORS-url]: https://github.com/adamchainz/django-cors-headers

[Filters-badge]: https://img.shields.io/badge/Django%20Filters-092E20?style=for-the-badge&logo=django&logoColor=white
[Filters-url]: https://django-filter.readthedocs.io/