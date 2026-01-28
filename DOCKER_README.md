# Looks Lab - Docker Setup

## Quick Start

### Development

```bash
# Build and start services
make build
make up

# View logs
make logs

# Access app shell
make shell

# Access database
make db-shell

# Stop services
make down
```

### Production

```bash
# Build production images
make prod-build

# Start production services
make prod-up

# Stop production services
make prod-down
```

## Services

### Development Stack
- **App**: FastAPI on port 8000
- **Database**: PostgreSQL 15 on port 5432
- **Redis**: Redis 7 on port 6379

### Production Stack
- **App**: FastAPI (behind Nginx)
- **Database**: PostgreSQL 15
- **Redis**: Redis 7 (with password)
- **Nginx**: Reverse proxy on ports 80/443

## Configuration

### Environment Files

**Development**: `.env`
```env
ENV=development
DATABASE_URI=postgresql+asyncpg://looks_lab:lab3344@db:5432/looks_lab
REDIS_URL=redis://redis:6379/0
```

**Production**: `.env.production`
```env
ENV=production
DB_USER=looks_lab
DB_PASSWORD=your_secure_password
DB_NAME=looks_lab
REDIS_PASSWORD=your_redis_password
DATABASE_URI=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
```

## Database Migrations

```bash
# Create new migration
docker-compose exec app alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec app alembic upgrade head

# Rollback migration
docker-compose exec app alembic downgrade -1
```

## Useful Commands

```bash
# Rebuild single service
docker-compose build app

# Restart single service
docker-compose restart app

# View specific service logs
docker-compose logs -f app

# Execute command in container
docker-compose exec app python -c "print('Hello')"

# Remove everything (including volumes)
make clean
```

## Health Checks

- **App**: `http://localhost:8000/health`
- **API Docs**: `http://localhost:8000/docs`
- **Database**: Automatic health check via Docker
- **Redis**: Automatic health check via Docker

## Troubleshooting

### Container won't start

```bash
# Check logs
make logs

# Rebuild from scratch
make clean
make build
make up
```

### Database connection issues

```bash
# Check database is ready
docker-compose exec db pg_isready -U looks_lab

# Restart database
docker-compose restart db
```

### Port already in use

```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use different host port
```

## Security Notes

### Production Checklist

- [ ] Change default passwords in `.env.production`
- [ ] Set strong `JWT_SECRET` and `GEMINI_API_KEY`
- [ ] Configure SSL certificates for Nginx
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Set up monitoring and logging
- [ ] Review and update `CORS_ORIGINS`
- [ ] Set `ENV=production`

### SSL Setup (Production)

```bash
# Place SSL certificates in nginx/ssl/
nginx/ssl/
├── cert.pem
└── key.pem

# Update nginx.conf to enable HTTPS
```

## Monitoring

### View Resource Usage

```bash
docker stats

# Or specific container
docker stats lookslab_app
```

### Database Backups

```bash
# Backup
docker-compose exec db pg_dump -U looks_lab looks_lab > backup.sql

# Restore
docker-compose exec -T db psql -U looks_lab looks_lab < backup.sql
```

## Development Workflow

1. **Start services**: `make up`
2. **Make code changes** (auto-reload enabled in dev)
3. **Create migration**: `docker-compose exec app alembic revision --autogenerate -m "changes"`
4. **Apply migration**: `docker-compose exec app alembic upgrade head`
5. **Test**: `make test`
6. **View logs**: `make logs`
7. **Stop services**: `make down`

## Production Deployment

1. **Prepare environment**: Copy `.env.production` and update values
2. **Build images**: `make prod-build`
3. **Start services**: `make prod-up`
4. **Apply migrations**: `docker-compose -f docker-compose.prod.yml exec app alembic upgrade head`
5. **Verify health**: Check `http://your-domain/health`
6. **Monitor logs**: `docker-compose -f docker-compose.prod.yml logs -f`

## Support

For issues, check:
- Application logs: `make logs`
- Database logs: `docker-compose logs db`
- Redis logs: `docker-compose logs redis`
- Nginx logs: `docker-compose logs nginx` (production only)

