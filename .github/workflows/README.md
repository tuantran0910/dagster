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

A comprehensive workflow for building multiple Dagster packages with matrix strategy support.

**Features:**
- ✅ Build multiple packages in parallel
- ✅ Support for all 60+ Dagster packages
- ✅ Manual and automatic triggers
- ✅ PyPI publishing support
- ✅ GitHub releases creation
- ✅ Container registry publishing

**Usage:**
1. Manual: Go to Actions → "Build and Publish Python Packages" → Run workflow
2. Automatic: Push tags with `release-*` prefix
3. Automatic: Create GitHub releases

## Container Images

Built container images are published to GitHub Container Registry:

```bash
# Pull the latest dagster core
docker pull ghcr.io/YOUR_USERNAME/dagster:latest

# Pull a specific version
docker pull ghcr.io/YOUR_USERNAME/dagster:2024.01.15.123

# Run dagster
docker run --rm ghcr.io/YOUR_USERNAME/dagster:latest
```

## Setup Requirements

### 1. Repository Permissions

Ensure your repository has the following permissions enabled:
- **Settings** → **Actions** → **General** → **Workflow permissions**
  - ✅ Read and write permissions
  - ✅ Allow GitHub Actions to create and approve pull requests

### 2. Secrets (Optional)

For PyPI publishing, add these secrets:
- `PYPI_TOKEN` - Your PyPI API token

### 3. Package Registry

Container images will be published to:
- `ghcr.io/YOUR_USERNAME/PACKAGE_NAME:VERSION`
- `ghcr.io/YOUR_USERNAME/PACKAGE_NAME:latest`

## Version Strategy

### CalVer (Calendar Versioning)

The workflows use CalVer for automatic versioning:
- Format: `YYYY.MM.DD.BUILD`
- Example: `2024.01.15.123`

### Manual Versioning

You can specify custom versions when manually triggering workflows:
- SemVer: `1.2.3`
- Pre-release: `1.2.3-alpha.1`
- Development: `1.2.3.dev20240115`

## Package Discovery

The workflows automatically discover packages in:
- `python_modules/` - Core packages
- `python_modules/libraries/` - Extension packages

Each package must have a `setup.py` file to be built.

## Container Structure

Built containers include:
- **Base:** Python 3.11 slim
- **Package:** Installed wheel file
- **User:** Non-root `dagster` user
- **Labels:** OCI-compliant metadata
- **Command:** Package verification script

## Troubleshooting

### Common Issues

1. **Package not found**
   - Ensure the package directory exists
   - Check that `setup.py` is present
   - Verify package name spelling

2. **Build failures**
   - Check Python dependencies
   - Review setup.py configuration
   - Check for import errors

3. **Registry push failures**
   - Verify repository permissions
   - Check GitHub token permissions
   - Ensure package name is valid

### Logs and Debugging

- **Workflow runs:** GitHub Actions tab
- **Build artifacts:** Downloaded from workflow runs
- **Container images:** GitHub Packages tab
- **Job summaries:** Available in workflow run details

## Examples

### Building a Single Package

```bash
# Trigger via GitHub CLI
gh workflow run build-core-package.yml \
  -f package=dagster \
  -f version=1.0.0
```

### Building Multiple Packages

```bash
# Trigger via GitHub CLI
gh workflow run build-and-publish-packages.yml \
  -f packages="dagster,dagster-webserver" \
  -f publish_to_ghcr=true
```

### Using Built Images

```bash
# Run Dagster webserver
docker run -p 3000:3000 \
  -v $(pwd)/dagster.yaml:/opt/dagster/dagster_home/dagster.yaml \
  ghcr.io/YOUR_USERNAME/dagster-webserver:latest \
  dagster-webserver -h 0.0.0.0 -p 3000

# Run Dagster daemon
docker run -d \
  -v $(pwd)/dagster.yaml:/opt/dagster/dagster_home/dagster.yaml \
  ghcr.io/YOUR_USERNAME/dagster:latest \
  dagster-daemon run
```

## Contributing

When adding new packages or modifying workflows:

1. Test manually before merging
2. Update package lists in workflows
3. Ensure setup.py files are properly configured
4. Add appropriate documentation

## Support

For issues with these workflows:
1. Check the troubleshooting section
2. Review workflow run logs
3. Open an issue with relevant details 