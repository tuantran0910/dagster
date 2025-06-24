<div align="center">
  <!-- Note: Do not try adding the dark mode version here with the `picture` element, it will break formatting in PyPI -->
  <a target="_blank" href="https://dagster.io" style="background:none">
    <img alt="dagster logo" src="https://raw.githubusercontent.com/dagster-io/dagster/master/.github/dagster-readme-header.svg" width="auto" height="100%">
  </a>
  <a target="_blank" href="https://github.com/dagster-io/dagster" style="background:none">
    <img src="https://img.shields.io/github/stars/dagster-io/dagster?labelColor=4F43DD&color=163B36&logo=github">
  </a>
  <a target="_blank" href="https://github.com/dagster-io/dagster/blob/master/LICENSE" style="background:none">
    <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg?label=license&labelColor=4F43DD&color=163B36">
  </a>
  <a target="_blank" href="https://pypi.org/project/dagster/" style="background:none">
    <img src="https://img.shields.io/pypi/v/dagster?labelColor=4F43DD&color=163B36">
  </a>
  <a target="_blank" href="https://pypi.org/project/dagster/" style="background:none">
    <img src="https://img.shields.io/pypi/pyversions/dagster?labelColor=4F43DD&color=163B36">
  </a>
  <a target="_blank" href="https://twitter.com/dagster" style="background:none">
    <img src="https://img.shields.io/badge/twitter-dagster-blue.svg?labelColor=4F43DD&color=163B36&logo=twitter" />
  </a>
  <a target="_blank" href="https://dagster.io/slack" style="background:none">
    <img src="https://img.shields.io/badge/slack-dagster-blue.svg?labelColor=4F43DD&color=163B36&logo=slack" />
  </a>
  <a target="_blank" href="https://linkedin.com/showcase/dagster" style="background:none">
    <img src="https://img.shields.io/badge/linkedin-dagster-blue.svg?labelColor=4F43DD&color=163B36&logo=linkedin" />
  </a>
</div>

**Dagster is a cloud-native data pipeline orchestrator for the whole development lifecycle, with integrated lineage and observability, a declarative programming model, and best-in-class testability.**

It is designed for **developing and maintaining data assets**, such as tables, data sets, machine learning models, and reports.

With Dagster, you declare—as Python functions—the data assets that you want to build. Dagster then helps you run your functions at the right time and keep your assets up-to-date.

Here is an example of a graph of three assets defined in Python:

```python
from dagster import asset
from pandas import DataFrame, read_html, get_dummies
from sklearn.linear_model import LinearRegression

@asset
def country_populations() -> DataFrame:
    df = read_html("https://tinyurl.com/mry64ebh")[0]
    df.columns = ["country", "pop2022", "pop2023", "change", "continent", "region"]
    df["change"] = df["change"].str.rstrip("%").str.replace("−", "-").astype("float")
    return df

@asset
def continent_change_model(country_populations: DataFrame) -> LinearRegression:
    data = country_populations.dropna(subset=["change"])
    return LinearRegression().fit(get_dummies(data[["continent"]]), data["change"])

@asset
def continent_stats(country_populations: DataFrame, continent_change_model: LinearRegression) -> DataFrame:
    result = country_populations.groupby("continent").sum()
    result["pop_change_factor"] = continent_change_model.coef_
    return result
```

The graph loaded into Dagster's web UI:

<p align="center">
  <img width="100%" alt="An example asset graph as rendered in the Dagster UI" src="https://raw.githubusercontent.com/dagster-io/dagster/master/.github/example-lineage.png">
</p>

Dagster is built to be used at every stage of the data development lifecycle - local development, unit tests, integration tests, staging environments, all the way up to production.

## Quick Start

If you're new to Dagster, we recommend checking out the [docs](https://docs.dagster.io) or following the hands-on [tutorial](https://docs.dagster.io/etl-pipeline-tutorial/).

Dagster is available on PyPI and officially supports Python 3.9 through Python 3.12.

```bash
pip install dagster dagster-webserver
```

This installs two packages:

- `dagster`: The core programming model.
- `dagster-webserver`: The server that hosts Dagster's web UI for developing and operating Dagster jobs and assets.

## Documentation

You can find the full Dagster documentation [here](https://docs.dagster.io), including the [Quickstart guide](https://docs.dagster.io/getting-started/quickstart).

<hr/>

## Key Features

  <p align="center">
    <img width="100%" alt="image" src="https://raw.githubusercontent.com/dagster-io/dagster/master/.github/key-features-cards.svg">
  </p>

### Dagster as a productivity platform

Identify the key assets you need to create using a declarative approach, or you can focus on running basic tasks. Embrace CI/CD best practices from the get-go: build reusable components, spot data quality issues, and flag bugs early.

### Dagster as a robust orchestration engine

Put your pipelines into production with a robust multi-tenant, multi-tool engine that scales technically and organizationally.

### Dagster as a unified control plane

Maintain control over your data as the complexity scales. Centralize your metadata in one tool with built-in observability, diagnostics, cataloging, and lineage. Spot any issues and identify performance improvement opportunities.

<hr />

## Master the Modern Data Stack with integrations

Dagster provides a growing library of integrations for today's most popular data tools. Integrate with the tools you already use, and deploy to your infrastructure.

<br/>
<p align="center">
    <a target="_blank" href="https://dagster.io/integrations" style="background:none">
        <img width="100%" alt="image" src="https://raw.githubusercontent.com/dagster-io/dagster/master/.github/integrations-bar-for-readme.png">
    </a>
</p>

## Community

Connect with thousands of other data practitioners building with Dagster. Share knowledge, get help,
and contribute to the open-source project. To see featured material and upcoming events, check out
our [Dagster Community](https://dagster.io/community) page.

Join our community here:

- 🌟 [Star us on GitHub](https://github.com/dagster-io/dagster)
- 📥 [Subscribe to our Newsletter](https://dagster.io/newsletter-signup)
- 🐦 [Follow us on Twitter](https://twitter.com/dagster)
- 🕴️ [Follow us on LinkedIn](https://linkedin.com/showcase/dagster)
- 📺 [Subscribe to our YouTube channel](https://www.youtube.com/@dagsterio)
- 📚 [Read our blog posts](https://dagster.io/blog)
- 👋 [Join us on Slack](https://dagster.io/slack)
- 🗃 [Browse Slack archives](https://discuss.dagster.io)
- ✏️ [Start a GitHub Discussion](https://github.com/dagster-io/dagster/discussions)

## Contributing

For details on contributing or running the project for development, check out our [contributing
guide](https://docs.dagster.io/about/contributing).

## License

Dagster is [Apache 2.0 licensed](https://github.com/dagster-io/dagster/blob/master/LICENSE).

# Dagster Core with RBAC Authentication

This repository contains a custom Dagster Core implementation with Role-Based Access Control (RBAC) authentication.

## Features

- **Role-Based Access Control (RBAC)** - 4 hierarchical roles (Admin, Editor, Launcher, Viewer)
- **GitHub OAuth Integration** - Secure authentication with GitHub
- **Granular Permissions** - Fine-grained control over operations
- **Secure Sessions** - HTTP-only cookies with CSRF protection

## Docker Image

The Docker image is built and published to GitHub Container Registry with CalVer tags (YYYY.MM.DD.BUILD).

### Using the Docker Image

```bash
docker pull ghcr.io/YOUR_USERNAME/dagster-core:latest
```

Replace `YOUR_USERNAME` with your GitHub username.

## Releasing a New Version

To release a new version of the Dagster Core image:

1. Make your changes to the codebase
2. Create and push a tag named `release-dagster-core`:

```bash
git tag release-dagster-core
git push origin release-dagster-core
```

3. The GitHub Actions workflow will:
   - Generate a CalVer tag (YYYY.MM.DD.BUILD)
   - Build and push the Docker image to GitHub Container Registry
   - Create a GitHub release
   - Delete the trigger tag

## Configuration

### Authentication Configuration

Add to your `dagster.yaml`:

```yaml
authentication:
  enabled: true
  provider: github
  default_role: viewer
  session_timeout: 86400  # 24 hours in seconds
  
  github:
    client_id: "your-github-client-id"
    client_secret: "your-github-client-secret"
    redirect_uri: "http://localhost:3000/auth/callback"
  
  role_assignments:
    # Assign roles by GitHub username or email
    "admin-user": admin
    "editor@company.com": editor
    "launcher-user": launcher
    # Users not listed get default_role
```

## Development

### Local Build

To build the Docker image locally:

```bash
docker build -t dagster-core:local .
```

### Running Locally

```bash
docker run -p 3000:3000 \
  -v /path/to/dagster.yaml:/opt/dagster/dagster_home/dagster.yaml \
  -v /path/to/workspace.yaml:/opt/dagster/dagster_home/workspace.yaml \
  dagster-core:local \
  dagster-webserver -h 0.0.0.0 -p 3000
```
