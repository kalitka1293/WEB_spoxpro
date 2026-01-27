# spoXpro E-commerce Backend

A comprehensive sports clothing e-commerce platform backend built with FastAPI, SQLAlchemy, and SQLite.

## Features

- 🏪 **Product Management**: Complete product catalog with filtering and search
- 🔐 **Authentication**: JWT-based authentication with guest cookie support
- 🛒 **Shopping Cart**: Full cart management for authenticated and guest users
- 📦 **Order Processing**: Complete checkout workflow with inventory management
- 👤 **User Management**: User profiles, registration, and verification
- 📊 **Admin Panel**: Administrative functionality for platform management
- 📝 **Comprehensive Logging**: Structured logging with file rotation
- 🔧 **Configuration Management**: Environment-based configuration
- 📚 **API Documentation**: Auto-generated OpenAPI documentation

## Architecture

The backend follows a layered architecture:

```
├── db/                     # Database layer
│   ├── main.py            # DB initialization and session management
│   ├── models/            # SQLAlchemy ORM models
│   └── services/          # Database service layer
├── routes/                # API endpoint handlers
├── service/              # Business logic layer
├── DTO/                  # Pydantic models for API
├── config/              # Configuration management
├── logs/             # Logging system
├── admin/               # Admin panel structure
├── main.py              # Application entry point
└── docs.py              # API documentation
```

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository and navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Run the setup script**
   ```bash
   python setup.py
   ```

3. **Activate the virtual environment**
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

4. **Review and update configuration**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Run the application**
   ```bash
   python -m backend.main
   ```

6. **Access the API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Manual Installation

If you prefer manual setup:

1. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

2. **Activate virtual environment**
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**
   ```bash
   cp .env.example .env
   ```

5. **Run the application**
   ```bash
   python -m backend.main
   ```

## Configuration

The application uses environment variables for configuration. Key settings:

### Database
- `DATABASE_URL`: SQLite database path (default: `sqlite:///./spoxpro.db`)
- `DATABASE_ECHO`: Enable SQL query logging (default: `false`)

### JWT Authentication
- `JWT_SECRET_KEY`: Secret key for JWT tokens (**MUST change in production**)
- `JWT_ALGORITHM`: JWT algorithm (default: `HS256`)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: `30`)

### Server
- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)
- `RELOAD`: Enable auto-reload in development (default: `true`)

### Logging
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `LOG_FILE_PATH`: Log file path (default: `./logs/log_file/spoxpro.log`)
- `LOG_MAX_FILE_SIZE`: Max log file size in bytes (default: `10485760`)
- `LOG_BACKUP_COUNT`: Number of backup log files (default: `5`)

## API Endpoints

### Authentication (`/auth`)
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/verify` - Email verification
- `POST /auth/guest-cookie` - Generate guest cookie
- `GET /auth/validate` - Validate JWT token

### Store (`/store`)
- `GET /store/products` - Get products with filtering
- `GET /store/products/{id}` - Get specific product
- `GET /store/categories` - Get all categories
- `GET /store/product-types` - Get all product types
- `GET /store/sport-types` - Get all sport types
- `GET /store/materials` - Get all materials

### User (`/user`)
- `GET /user/profile` - Get user profile
- `PUT /user/profile` - Update user profile
- `GET /user/cart` - Get cart contents
- `POST /user/cart/add` - Add item to cart
- `PUT /user/cart/update` - Update cart item quantity
- `DELETE /user/cart/remove` - Remove item from cart
- `GET /user/orders` - Get order history
- `POST /user/orders/create` - Create new order

### System
- `GET /` - Root endpoint with app information
- `GET /health` - Health check endpoint

## Development

### Project Structure

The project follows a modular architecture with clear separation of concerns:

- **Database Layer** (`db/`): SQLAlchemy models and database services
- **API Layer** (`routes/`): FastAPI route handlers
- **Business Logic** (`service/`): Core business logic and validation
- **Data Transfer Objects** (`DTO/`): Pydantic models for API serialization
- **Configuration** (`config/`): Application settings and database configuration
- **Logging** (`logs/`): Structured logging with file rotation

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend

# Run specific test file
pytest tests/test_auth.py
```

### Code Quality

The project includes:
- Type hints throughout the codebase
- Comprehensive error handling
- Structured logging
- Input validation with Pydantic
- Database transaction management
- Security best practices

## Security Features

- JWT token-based authentication
- Password hashing with bcrypt
- Input validation and sanitization
- SQL injection prevention with SQLAlchemy ORM
- CORS configuration
- Secure cookie handling for guest users
- Environment-based configuration for secrets

## Logging

The application provides comprehensive logging:

- **Structured JSON logging** for file output
- **Console logging** with readable format
- **Request/response logging** with timing
- **Database operation logging**
- **Authentication attempt logging**
- **Error logging** with stack traces
- **Log rotation** to prevent disk space issues

Log files are stored in `logs/log_file/` directory.

## Database

The application uses SQLite with SQLAlchemy ORM:

- **Automatic schema creation** on first run
- **Foreign key constraints** for data integrity
- **Transaction management** for consistency
- **Connection pooling** for performance
- **Database health checks**

## Deployment

### Production Checklist

1. **Update environment variables**:
   - Set `ENVIRONMENT=production`
   - Change `JWT_SECRET_KEY` to a secure random value
   - Set `DEBUG=false`
   - Configure appropriate `CORS_ORIGINS`

2. **Database**:
   - Consider using PostgreSQL for production
   - Set up database backups
   - Configure connection pooling

3. **Security**:
   - Use HTTPS in production
   - Set `COOKIE_SECURE=true`
   - Configure firewall rules
   - Set up rate limiting

4. **Monitoring**:
   - Set up log aggregation
   - Configure health check monitoring
   - Set up error alerting

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "backend.main"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Check the API documentation at `/docs`
- Review the logs in `logs/log_file/`
- Check the health endpoint at `/health`