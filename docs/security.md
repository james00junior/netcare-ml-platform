# Security, Secrets, and IAM

## Authentication model

GitHub Actions deployments use Databricks workload identity federation (OIDC) rather than a Databricks personal access token. The workflows request only `id-token: write` and `contents: read`, then use:

- `DATABRICKS_AUTH_TYPE=github-oidc`
- `DATABRICKS_HOST`
- `DATABRICKS_CLIENT_ID`

The Databricks service principal is the deployment identity. Its federation policy must restrict the GitHub repository and environment subject, and the service principal must receive only the Databricks permissions required by the deployment target.

## GitHub environment configuration

Configure these as GitHub **Environment variables** for the `dev` and `prod` environments:

- `DATABRICKS_HOST`
- `DATABRICKS_CLIENT_ID`

Do not create `DATABRICKS_TOKEN` for these deployment workflows.

The Databricks federation policy should bind the service principal to the expected GitHub Actions subject, for example:

```text
repo:james00junior/netcare-ml-platform:environment:prod
```

Use the corresponding `dev` subject for the development environment.

## Application secrets

Local `.env` files remain supported for development and are ignored by Git. Credentials loaded by `src.config.settings.Settings` use Pydantic `SecretStr`, so application code must explicitly call `get_secret_value()` at the point where a credential is handed to an authentication client.

The repository must never contain:

- Databricks personal access tokens
- API keys
- passwords
- private keys
- patient records or production inference payloads

## Runtime serving credentials

If an existing application system needs to call Databricks Model Serving directly, use an approved workload/service identity and inject its credential through the hosting platform's secret manager. Do not put the credential in source code, notebooks, committed configuration, or logs.

The current `DatabricksServingClient` intentionally logs only request metadata such as request ID and batch size. It does not log authorization headers or feature payloads.

## IAM principles

The deployment service principal should have only the permissions necessary to:

1. validate and deploy the Databricks bundle in its target environment;
2. update the intended jobs/serving resources;
3. access the required Unity Catalog resources;
4. read/write only the required deployment artifacts.

Separate `dev`, `staging`, and `prod` identities/environments should be preferred over one broadly privileged identity.

## Rotation and incident response

OIDC federation is preferred because GitHub does not need to store a long-lived Databricks PAT. If a runtime secret is required for an external application integration, store it in the hosting platform's secret manager and rotate it according to the organisation's security policy.

If a credential is suspected to be exposed:

1. revoke/rotate it immediately;
2. inspect GitHub and Databricks audit logs;
3. determine the affected identity and resources;
4. replace the credential through the secret manager;
5. rerun the relevant CI/deployment validation.

## Verification

`tests/test_security.py` verifies that Databricks serving tokens and API keys are represented as `SecretStr` values and are not populated by default. CI remains the authoritative formatting, linting, and test gate.
