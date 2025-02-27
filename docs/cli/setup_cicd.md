## ⚙️ CI/CD Setup (Experimental)

This starter pack provides an *experimental* command to automate the setup of a basic CI/CD pipeline.  This pipeline connects your agent to a GitHub repository and uses Google Cloud Build for automated testing and deployment.

**⚠️ Important Notes:**

*   **Experimental Feature:** The `setup-cicd` command is under active development.  Expect potential changes and report any issues you encounter.
*   **Production Readiness:**  For production deployments, we *strongly* recommend following the manual setup instructions in the `deployment/README.md` file.  The manual approach provides greater control over security, customization, and environment-specific configurations.  This automated setup is primarily for development and testing.
*   **Git Provider:** Currently, only GitHub is supported, but support for other Git providers is planned.

### Quick CI/CD Setup (Automated)

This command streamlines the CI/CD setup process.  It handles:

1.  **GitHub Repository:** Creates a new GitHub repository (or connects to an existing *empty* one).
2.  **Cloud Build Connection:** Establishes a connection between your GitHub repository and Google Cloud Build.
3.  **Development Environment:**  Sets up the infrastructure for your development environment using Terraform (optional).
4.  **CI/CD Triggers:** Configures basic Cloud Build triggers for pull request checks and deployments.
5.  **Terraform State:**  By default, configures remote Terraform state management using a Google Cloud Storage (GCS) bucket.  You can opt for local state management if needed.

**Command Usage:**
```bash
agent-starter-pack setup-cicd \
    --dev-project <YOUR_DEV_PROJECT_ID> \
    --staging-project <YOUR_STAGING_PROJECT_ID> \
    --prod-project <YOUR_PROD_PROJECT_ID> \
    --cicd-project <YOUR_CICD_PROJECT_ID> \
    [--region <GCP_REGION>] \
    [--repository-name <GITHUB_REPO_NAME>] \
    [--repository-owner <GITHUB_USERNAME>] \
    [--host-connection-name <CONNECTION_NAME>] \
    [--github-pat <YOUR_GITHUB_PAT>] \
    [--github-app-installation-id <YOUR_GITHUB_APP_INSTALLATION_ID>] \
    [--local-state] \
    [--debug] \
    [--auto-approve]
```

**Options:**

*   `--staging-project`:  **Required.** The Google Cloud project ID for your staging environment.
*   `--prod-project`:  **Required.** The Google Cloud project ID for your production environment.
*   `--cicd-project`:  **Required.** The Google Cloud project ID where your CI/CD resources (Cloud Build, etc.) will reside. This can be the same as your staging or production project.
*   `--dev-project`:  (Optional) The Google Cloud project ID for your development environment.  If provided, the setup will also configure a development environment.
*   `--region`:  The GCP region to use (default: `us-central1`).
*   `--repository-name`:  (Optional) The name of your GitHub repository.  If omitted, a name will be generated (e.g., `genai-app-1678886400`).
*   `--repository-owner`: (Optional) Your GitHub username or organization name.  If omitted, it defaults to your currently authenticated GitHub user.
*   `--host-connection-name`: (Optional) The name for the Cloud Build connection to GitHub (default: `github-connection`).
*   `--github-pat`:  (Optional) Your GitHub Personal Access Token.  This is used for programmatic access (e.g., in automated scripts).  If provided, you also need `--github-app-installation-id`.
*   `--github-app-installation-id`: (Optional) The installation ID of your GitHub App.  Required if using `--github-pat`.
*   `--local-state`:  Use local Terraform state instead of a remote GCS bucket.  This is generally *not* recommended for collaborative projects or production.
*   `--debug`:  Enable debug logging for more verbose output.
*   `--auto-approve`:  Skip interactive confirmation prompts.  Use with caution!

**Project Requirements:**

You need at least *two* Google Cloud projects: one for staging and one for production. The CI/CD project can be the same as either the staging or production project. A separate development project is optional.

**Interactive Mode vs. Programmatic Mode:**

The command operates in two modes:

*   **Interactive Mode:**  If you don't provide `--github-pat` and `--github-app-installation-id`, the command will guide you through an interactive setup process.  It will prompt you to authenticate with GitHub and create resources.
*   **Programmatic Mode:**  If you provide `--github-pat` and `--github-app-installation-id`, the command will run non-interactively, using the provided credentials.  This is suitable for automation.

**Authentication:**

*   **Interactive Mode:**  Uses OAuth to connect to GitHub.  You'll be prompted to authorize the connection.
*   **Programmatic Mode:**  Uses a GitHub Personal Access Token (PAT) and a GitHub App installation ID.  The PAT must have the necessary permissions to create/manage repositories and webhooks.  You can create/update this PAT as a secret in Google Cloud Secret Manager.

**Steps Performed (High-Level):**

1.  **API Enablement:**  Ensures that the required Google Cloud APIs (Secret Manager, Cloud Build) are enabled in your CI/CD project.
2.  **Git Setup:**  Initializes a Git repository (if one doesn't exist) and adds a remote pointing to your GitHub repository.
3.  **GitHub Connection (Interactive Mode):**  Creates a connection between Cloud Build and your GitHub repository, using OAuth for authentication.
4.  **GitHub Repository (Interactive Mode):** Creates a new, empty GitHub repository if you selected that option.
5.  **Secret Management (Programmatic Mode):**  Creates or updates a secret in Google Cloud Secret Manager to store your GitHub PAT.
6.  **Terraform Configuration:**
    *   Copies the necessary Terraform files for CI/CD.
    *   Sets up the Terraform backend (either GCS or local).
    *   Updates the `env.tfvars` file with your project IDs, region, repository details, and authentication information.
    * Updates the `build_triggers.tf` to link Cloud Build trigger with the Github repository.
    *   Applies the Terraform configuration to create the infrastructure (both dev, if specified, and prod/staging).
7.  **Git Remote:** Configures the Git remote to point to your GitHub repository.

**After Running the Command:**

*   **Commit and Push:**  You'll need to commit and push your code to the newly created (or connected) GitHub repository to trigger the CI/CD pipeline.  The command will remind you to do this.
*   **Cloud Build Triggers:**  Cloud Build triggers will be set up to automatically run on pull requests and pushes to the main branch.
*   **Terraform State:** Your Terraform state will be stored either locally (if `--local-state` was used) or in a GCS bucket named `<YOUR_CICD_PROJECT_ID>-terraform-state`.
*   **Manual Steps:** Remember that for full production readiness, you should consult the manual deployment instructions.

### Manual CI/CD Setup

For fine-grained control and production deployments, refer to the detailed instructions in `deployment/README.md`.  This manual approach allows for:

*   **Enhanced Security:**  Configure stricter IAM permissions and network policies.
*   **Custom Workflows:**  Implement custom build, test, and deployment steps.
*   **Environment-Specific Settings:**  Tailor configurations for each environment (dev, staging, prod).
*   **Advanced CI/CD:**  Integrate with other CI/CD tools and services.
