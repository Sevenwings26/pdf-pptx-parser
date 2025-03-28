# File Upload & Parsing Service

## Overview
This project provides a web application and api endpoints that allows users to upload PDF and PPTX files, extract their contents, and process them asynchronously using Celery. It includes a structured deployment with Docker Compose, featuring an API Gateway, Parsing Service, Database Service, and Redis/RabbitMQ for task queuing.

## Features
- Secure file upload (PDF & PPTX only)
- Asynchronous processing with Celery
- File parsing and content extraction
- Database storage for uploaded files and parsed content
- Dockerized deployment with API Gateway, Parsing Service, and Database
- Redis for caching and message brokering (optional RabbitMQ support)

## Tech Stack
- **Backend:** Flask
- **Task Queue:** Celery
- **Message Broker:** Redis (or RabbitMQ)
- **Database:** PostgreSQL
- **Containerization:** Docker & Docker Compose

## Installation
### Prerequisites
- Python 3.x
- Docker & Docker Compose
- Redis/RabbitMQ (if using Celery)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/Sevenwings26/pdf-pptx-parser.git
   cd pdf-pptx-parser
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```bash
   .env
   ```
   Configure your `.env` file accordingly.
4. Run the application:
   ```bash
   python run.py
   ```

## Running with Docker Compose
1. Build and start services:
   ```bash
   docker-compose up --build
   ```
2. The application should be available at `http://localhost:5000`

## API Endpoints
| Method | Endpoint | Description |
|--------|-------------|----------------|
| `GET` | `/` | Landing page |
| `POST` | `/upload` | Upload a PDF/PPTX file |
| `GET` | `/files` | List recent uploads |

## Celery & Background Processing
1. Start Redis:
   ```bash
   docker run -d -p 6379:6379 redis
   ```
2. Start the Celery worker:
   ```bash
   celery -A app.celery worker --loglevel=info
   ```
3. Submit a task:
   ```python
   from app.tasks import process_file
   process_file.delay("example.pdf")
   ```

## Deployment
For production deployment, you can use:
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

## Contributing
Feel free to open issues or submit PRs.

## License
This project is licensed under the MIT License.
