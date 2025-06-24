# Dagster GitHub Actions Workflows

This directory contains GitHub Actions workflows for building and publishing Dagster packages to GitHub Container Registry.

## Workflows

### 1. Build Dagster Core Package (`build-core-package.yml`)

A focused workflow for building core Dagster packages and publishing them as container images to GitHub Container Registry.

**Features:**
- ✅ Manual trigger with package selection
- ✅ Automatic builds on pushes to main/master
- ✅ CalVer versioning (YYYY.MM.DD.BUILD)
- ✅ Container image publishing to GHCR
- ✅ Build artifacts upload
- ✅ Comprehensive job summaries

**Supported Packages:**
- `dagster` - Core Dagster package
- `dagster-webserver` - Dagster web interface
- `dagster-graphql` - GraphQL API
- `dagster-pipes` - Pipes integration
- `dagster-test` - Testing utilities

**Usage:**
1. Go to the "Actions" tab in your GitHub repository
2. Select "Build Dagster Core Package"
3. Click "Run workflow"
4. Choose the package to build
5. Optionally specify a custom version

### 2. Build and Publish Python Packages (`build-and-publish-packages.yml`)

A comprehensive workflow for building multiple Dagster packages with matrix strategy support and proper dependency resolution.

**Key Features:**
- ✅ **Smart Dependency Resolution**: Builds all packages with consistent versions first
- ✅ **Local Wheel Repository**: Creates a local wheel cache to resolve interdependencies
- ✅ **Matrix Strategy**: Builds multiple packages in parallel
- ✅ **Development Versioning**: Uses `1.0.0.dev{BUILD}+{SHA}` format to avoid PyPI conflicts
- ✅ **Container Publishing**: Publishes to GitHub Container Registry
- ✅ **Automatic Discovery**: Finds all packages in the repository
- ✅ **Secure Containers**: Non-root user, proper labels

**Supported Packages:**
- **Core**: `dagster`, `dagster-webserver`, `dagster-graphql`, `dagster-pipes`, `dagster-test`, `dagit`
- **Libraries**: All 60+ packages in `python_modules/libraries/`

**Usage:**
1. **Manual Build**:
   - Go to GitHub Actions → "Build and Publish Python Packages"
   - Select packages to build (comma-separated or "all")
   - Optionally specify custom version
   - Choose whether to publish to GHCR

2. **Automatic Build**:
   - Push tags with `release-*` prefix
   - Create GitHub releases

## How It Works

### 1. Package Discovery
The workflow automatically discovers all buildable packages:
```bash
# Core packages (hardcoded list)
python_modules/dagster
python_modules/dagster-webserver
# ... etc

# Library packages (auto-discovered)
python_modules/libraries/*
```

### 2. Dependency Resolution Strategy
**Problem**: Dagster packages have interdependencies with custom development versions that don't exist on PyPI.

**Solution**: 
1. Build all core packages first with consistent development versions
2. Create a local wheel repository
3. Install packages using local wheels first, then fall back to PyPI

```dockerfile
# Install from local wheels first, then PyPI fallback
RUN pip install --find-links /tmp/local-wheels --no-index --only-binary=all /tmp/*.whl || \
    (echo "Local install failed, trying with PyPI fallback..." && \
     pip install --find-links /tmp/local-wheels /tmp/*.whl)
```

### 3. Version Strategy
- **Development Builds**: `1.0.0.dev{BUILD_NUMBER}+{SHA}`
- **Manual Builds**: Custom version from input
- **Consistent**: All packages use the same version to resolve dependencies

### 4. Container Structure
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Copy built package and local dependencies
COPY dist/*.whl /tmp/
COPY local-wheels/*.whl /tmp/local-wheels/

# Smart installation with fallback
RUN pip install --find-links /tmp/local-wheels ...

# Security: non-root user
RUN useradd --create-home --shell /bin/bash dagster
USER dagster

# Verification command with proper import handling
CMD ["python", "-c", "...import logic..."]
```

## Container Images

Built images are published to GitHub Container Registry:

```bash
# Pull any package
docker pull ghcr.io/YOUR_USERNAME/dagster-PACKAGE_NAME:VERSION

# Examples
docker pull ghcr.io/YOUR_USERNAME/dagster-dagster:latest
docker pull ghcr.io/YOUR_USERNAME/dagster-dagit:1.0.0.dev123+abc1234

# Run a container
docker run --rm ghcr.io/YOUR_USERNAME/dagster-dagster:latest
```

## Setup Requirements

### 1. Repository Permissions
- **Settings** → **Actions** → **General** → **Workflow permissions**
  - ✅ Read and write permissions
  - ✅ Allow GitHub Actions to create and approve pull requests

### 2. Secrets (Optional)
- No secrets required for GitHub Container Registry (uses `GITHUB_TOKEN`)
- For PyPI: Add `PYPI_TOKEN` secret (currently disabled in workflow)

### 3. Package Registry Access
Images are published to:
- `ghcr.io/YOUR_USERNAME/dagster-PACKAGE_NAME:VERSION`
- `ghcr.io/YOUR_USERNAME/dagster-PACKAGE_NAME:latest`

## Troubleshooting

### Common Issues

1. **Dependency Resolution Errors**
   - ✅ **Fixed**: Local wheel repository resolves interdependencies
   - The workflow now builds all packages first with consistent versions

2. **Import Errors in Containers**
   - ✅ **Handled**: Smart import logic with package name conversion
   - Converts `dagster-webserver` → `dagster_webserver` for imports

3. **Version Conflicts**
   - ✅ **Solved**: Development versioning avoids PyPI conflicts
   - Format: `1.0.0.dev{BUILD}+{SHA}` is PEP 440 compliant

4. **Build Failures**
   - Check if `setup.py` exists in package directory
   - Review build logs for missing dependencies
   - Verify package name spelling

### Debugging Tips

1. **Check Local Wheels**:
   ```bash
   # Look for "Available local wheels" in build logs
   # Should show all built .whl files
   ```

2. **Container Verification**:
   ```bash
   # Test import manually
   docker run -it ghcr.io/YOUR_USERNAME/dagster-PACKAGE:latest bash
   python -c "import package_name"
   ```

3. **Version Consistency**:
   ```bash
   # All packages should use same version
   grep "Using build version" build-logs
   ```

## Examples

### Build Single Package
```bash
# Via GitHub CLI
gh workflow run build-and-publish-packages.yml \
  -f packages="dagster" \
  -f version="1.2.3" \
  -f publish_to_ghcr=true
```

### Build Multiple Packages
```bash
gh workflow run build-and-publish-packages.yml \
  -f packages="dagster,dagster-webserver,dagit" \
  -f publish_to_ghcr=true
```

### Build All Packages
```bash
gh workflow run build-and-publish-packages.yml \
  -f packages="all" \
  -f publish_to_ghcr=true
```

### Use Built Images

```bash
# Run Dagster webserver
docker run -p 3000:3000 \
  -v $(pwd)/dagster.yaml:/opt/dagster/dagster_home/dagster.yaml \
  ghcr.io/YOUR_USERNAME/dagster-dagster-webserver:latest \
  dagster-webserver -h 0.0.0.0 -p 3000

# Run Dagster with custom code
docker run -v $(pwd):/workspace \
  ghcr.io/YOUR_USERNAME/dagster-dagster:latest \
  python /workspace/my_dagster_code.py
```

## Advanced Configuration

### Custom Docker Labels
All containers include OCI-compliant labels:
- `org.opencontainers.image.title`
- `org.opencontainers.image.description` 
- `org.opencontainers.image.version`
- `org.opencontainers.image.source`
- `org.opencontainers.image.revision`
- `org.opencontainers.image.created`

### Build Artifacts
- **Retention**: 30 days
- **Contents**: Built wheels (.whl files)
- **Access**: Download from GitHub Actions runs

### Matrix Strategy
- **Parallelism**: Builds packages simultaneously
- **Fail-fast**: Disabled (continues if one package fails)
- **Individual Logs**: Each package has separate build logs

## Contributing

When adding new packages:

1. **Ensure Setup**: Package must have `setup.py`
2. **Test Locally**: Verify the package builds with `python -m build`
3. **Dependencies**: Add to core packages list if it's a common dependency
4. **Documentation**: Update package lists in this README

For workflow modifications:
1. Test with small package sets first
2. Check dependency resolution carefully
3. Verify container functionality
4. Update documentation

## Support

For issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review workflow run logs in GitHub Actions
3. Test package builds locally first
4. Open an issue with build logs and error details

## Recent Improvements

- **v2024.01**: Fixed dependency resolution with local wheel repository
- **v2024.01**: Added development versioning to avoid PyPI conflicts  
- **v2024.01**: Improved container security with non-root users
- **v2024.01**: Enhanced error handling and logging 