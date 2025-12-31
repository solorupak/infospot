# Docker Compose Troubleshooting

## Common Docker Compose Issues

### Issue: "docker compose" command not found

This happens when your system uses the older `docker-compose` (with hyphen) instead of the newer `docker compose` (with space).

#### Solution
The Makefile now automatically detects which version you have and uses the correct command. You can check which version is being used:

```bash
make check-docker
```

This will show:
- Your Docker version
- Which Docker Compose command is being used
- Your Docker Compose version

### Manual Commands

If you need to run Docker Compose commands manually:

#### For older systems (docker-compose with hyphen):
```bash
docker-compose -f docker-compose.local.yml up -d
docker-compose -f docker-compose.local.yml exec django python manage.py shell
```

#### For newer systems (docker compose with space):
```bash
docker compose -f docker-compose.local.yml up -d
docker compose -f docker-compose.local.yml exec django python manage.py shell
```

### Other Common Issues

#### 1. Permission Denied
```bash
# Fix Docker permissions (Linux/macOS)
sudo usermod -aG docker $USER
# Then logout and login again
```

#### 2. Port Already in Use
```bash
# Check what's using the port
lsof -i :8000
# Or kill all containers and restart
make down
make up
```

#### 3. Container Build Issues
```bash
# Rebuild containers from scratch
make rebuild
# Or build without cache
docker-compose -f docker-compose.local.yml build --no-cache
```

#### 4. Volume Issues
```bash
# Reset database (DESTRUCTIVE)
make reset-db
# Or remove all volumes
make prune
```

### Verification Commands

```bash
# Check if containers are running
make ps

# Check container logs
make logs
make logs-django
make logs-postgres

# Check Docker system info
docker system info
docker system df
```

### Environment Variables

Make sure you have the required environment variables:
```bash
# Check if .env file exists
ls -la .env

# Copy from example if needed
cp .env.example .env
```

### Getting Help

1. **Check Docker status**: `make check-docker`
2. **View container status**: `make ps`
3. **Check logs**: `make logs-django`
4. **Restart everything**: `make restart`
5. **Clean rebuild**: `make rebuild`

If issues persist, the problem might be with your Docker installation or system configuration.