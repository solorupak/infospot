# Package Management for InfoSpot (using uv)

This project uses **uv** as the package manager, which is faster and more reliable than pip. All dependencies are managed through `pyproject.toml` and `uv.lock` files.

## Available Methods

### 1. Make Commands (Recommended for Docker)

#### Primary uv Commands
```bash
# Add a package
make add-package pkg="django-tenants"

# Add a specific version
make pkg-install pkg="django-tenants" ver="3.7.0"

# Remove a package
make remove-package pkg="package-name"

# Update a package to latest version
make update-package pkg="package-name"

# Sync all packages with pyproject.toml
make sync-packages

# Update lock file
make lock-packages

# Show installed packages
make show-packages

# Show outdated packages
make show-outdated
```

#### Development Dependencies
```bash
# Add a development package
make add-dev-package pkg="django-debug-toolbar"

# Remove a development package
make remove-dev-package pkg="package-name"
```

#### Quick Commands (aliases)
```bash
# Install with specific version
make pkg-install pkg="django-tenants" ver="3.7.0"

# Remove package
make pkg-remove pkg="package-name"

# Update package
make pkg-update pkg="package-name"

# List packages
make pkg-list

# Show outdated packages
make pkg-outdated
```

### 2. Direct uv Commands

If you're not using Docker, you can use `uv` directly:

```bash
# Add a package
uv add django-tenants

# Add specific version
uv add django-tenants==3.7.0

# Remove a package
uv remove package-name

# Add development dependency
uv add --group dev pytest

# Sync dependencies
uv sync

# Update lock file
uv lock

# List installed packages
uv pip list

# Show outdated packages
uv pip list --outdated
```

## Features

### Automatic Dependency Management
- **pyproject.toml**: Defines your project dependencies
- **uv.lock**: Locks exact versions for reproducible builds
- **Automatic resolution**: uv handles dependency conflicts intelligently
- **Fast installation**: Much faster than pip

### Docker Integration
- All Make commands work seamlessly with Docker containers
- No need to rebuild containers for package changes
- Packages are managed in the running Django container

### Development vs Production Dependencies
- **Production dependencies**: Added to `[project.dependencies]`
- **Development dependencies**: Added to `[dependency-groups.dev]`
- Clean separation of concerns

## Examples

### Adding django-tenants (already done)
```bash
# This was already added to pyproject.toml
make add-package pkg="django-tenants"
```

### Adding a development tool
```bash
make add-dev-package pkg="django-debug-toolbar"
```

### Adding a package with specific version
```bash
make pkg-install pkg="pillow" ver="10.0.0"
```

### Updating all dependencies
```bash
# Sync with latest compatible versions
make sync-packages

# Update lock file
make lock-packages
```

### Removing unused packages
```bash
make remove-package pkg="unused-package"
```

## File Structure

### pyproject.toml
Contains your project configuration and dependencies:
```toml
[project]
dependencies = [
    "django==4.2.17",
    "django-tenants==3.7.0",
    # ... other dependencies
]

[dependency-groups]
dev = [
    "pytest==9.0.2",
    "django-debug-toolbar==6.1.0",
    # ... dev dependencies
]
```

### uv.lock
Auto-generated file that locks exact versions for reproducible builds. **Never edit manually**.

### requirements.txt (Legacy)
Still maintained for compatibility with deployment systems that don't support uv yet.

## Best Practices

1. **Use uv commands** instead of pip for all package management
2. **Add production dependencies** to main dependencies
3. **Add development tools** to dev dependency group
4. **Sync regularly** using `make sync-packages`
5. **Commit both pyproject.toml and uv.lock** to version control
6. **Use specific versions** for critical dependencies

## Migration from pip

If you have old pip-based workflows:

### Old pip commands → New uv commands
```bash
# Old way
pip install django-tenants
pip freeze > requirements.txt

# New way
make add-package pkg="django-tenants"
```

### Legacy commands (deprecated but still work)
```bash
# These still work but show deprecation warnings
make install-package pkg="package-name"  # Use add-package instead
make install-requirements                 # Use sync-packages instead
make update-requirements                  # Use lock-packages instead
```

## Troubleshooting

### Package conflicts
uv handles conflicts automatically, but if issues arise:
```bash
# Remove conflicting package first
make remove-package pkg="conflicting-package"

# Add the new one
make add-package pkg="new-package"

# Sync to resolve dependencies
make sync-packages
```

### Lock file issues
If uv.lock gets corrupted:
```bash
# Regenerate lock file
make lock-packages
```

### Docker container issues
If packages aren't syncing in Docker:
```bash
# Rebuild containers
make rebuild

# Or sync packages
make sync-packages
```

### Performance
uv is much faster than pip:
- **Installation**: 10-100x faster
- **Dependency resolution**: Much more efficient
- **Lock file generation**: Near-instantaneous

## Why uv?

- **Speed**: 10-100x faster than pip
- **Better dependency resolution**: Handles conflicts more intelligently
- **Modern tooling**: Built for modern Python development
- **Reproducible builds**: Lock files ensure consistency
- **Active development**: Rapidly improving tool