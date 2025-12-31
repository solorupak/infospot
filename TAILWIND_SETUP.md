# TailAdmin Integration Setup

This document explains how to set up and use TailAdmin with the InfoSpot Django project.

## Why This Approach?

We're using **Tailwind CSS directly** (not django-tailwind) because:
- ✅ **Simpler**: Standard Node.js tooling, no Django wrapper complexity
- ✅ **Faster**: Direct Tailwind CLI is more efficient
- ✅ **Standard**: Uses the same approach as most modern web projects
- ✅ **Flexible**: Easy to customize and extend

## Quick Start

### Option 1: Use Pre-built CSS (Immediate)
The project includes a minimal pre-built CSS file at `static/css/tailwind.min.css` that you can use immediately without installing Node.js.

### Option 2: Full Build Setup (Recommended for Development)

1. **Install Node.js** (if not already installed):
   ```bash
   # macOS with Homebrew
   brew install node
   
   # Or download from https://nodejs.org/
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Build CSS**:
   ```bash
   # One-time build
   npm run build-css
   
   # Or watch for changes during development
   npm run watch-css
   ```

4. **Use the build script** (alternative):
   ```bash
   ./build.sh
   ```

## File Structure

```
├── tailwind.config.js          # TailAdmin configuration
├── package.json                # Node.js dependencies
├── static/css/
│   ├── tailwind.css            # Input file (Tailwind directives)
│   └── tailwind.min.css        # Output file (compiled CSS)
├── static/js/
│   └── tailadmin.js            # TailAdmin JavaScript components
└── build.sh                    # Build script
```

## Development Workflow

1. **Start CSS watcher**:
   ```bash
   npm run watch-css
   ```

2. **Make changes** to templates or CSS

3. **CSS automatically rebuilds** when you save files

## Production Build

For production, run:
```bash
npm run build-css
```

This creates an optimized, minified CSS file with only the classes you actually use.

## Integration Status

- ✅ Tailwind CSS configuration (TailAdmin colors, spacing, etc.)
- ✅ Build pipeline setup
- ✅ Basic component styles
- ✅ HTMX integration JavaScript
- ✅ Theme toggle functionality
- ✅ Alpine.js integration for sidebar
- 🔄 Component library (in progress)
- 🔄 Template migration (in progress)

## Next Steps

1. Create TailAdmin component library
2. Convert existing Bootstrap templates
3. Implement tenant branding
4. Add Chart.js integration
5. Performance optimization

## Troubleshooting

**CSS not updating?**
- Make sure `npm run watch-css` is running
- Check that your HTML templates are in the `content` paths in `tailwind.config.js`

**Node.js not installed?**
- Use the pre-built CSS file for now
- Install Node.js when ready for full development setup

**Build errors?**
- Run `npm install` to ensure dependencies are installed
- Check that `tailwind.config.js` syntax is correct