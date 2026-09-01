# Infrastructure

Archer runs as a single container on IBM Code Engine, in `eu-gb`. There is no
infrastructure-as-code here by choice: the whole deployment is four resources
and one workflow, and a Terraform layer over that would be more to maintain
than it removes. This file is the description instead.

## What exists

| Resource | Name | Plan | Purpose |
|---|---|---|---|
| Code Engine project | `archer` | standard | Hosts the application |
| Code Engine application | `archer` | - | The running service |
| Container Registry namespace | `archer` | free | Stores the image |
| watsonx.ai Runtime | `archer-watsonx-runtime` | lite | The model |
| watsonx.ai Studio | `archer-watsonx-studio` | free-v1 | Required for the watsonx project |
| Cloud Object Storage | `archer-watsonx-storage` | lite | Required as watsonx project storage |

Everything except Code Engine is on a free plan. **Object Storage is a
prerequisite of a watsonx project, not a dependency of the application** - the
container reads its database from local disk and makes no object storage calls.
That was a deliberate change; see `backend/Dockerfile` and
`scripts/generate_dataset.py`.

## Application configuration

```text
CPU              0.5 vCPU
Memory           1G
Port             8080
Minimum scale    0     (scales to zero when idle)
Maximum scale    2
Image            private.uk.icr.io/archer/archer-backend:<commit sha>
Registry secret  icr-pull
Runtime secret   archer-runtime  (env-from-secret)
```

**Minimum scale is zero deliberately.** The demo is idle almost all of the
time, so an always-warm instance would be paying for nothing. The cost is a
cold start on the first request after a quiet period. That trade is what makes
image size worth caring about, and it is why the dataset is generated into a
cached layer rather than downloaded at startup or copied in after the
application source.

Maximum scale is capped at 2 so that a burst of traffic - or someone pointing a
load generator at a public demo - cannot scale the bill.

## Secrets

Two Code Engine secrets, neither of which is in this repository:

- **`archer-runtime`** (generic) - the eight runtime environment variables. See
  `.env.example` for the names.
- **`icr-pull`** (registry) - lets Code Engine pull the private image.

The application receives the runtime secret via `--env-from-secret`, so no
secret value appears in the application definition, the workflow, or the image.

## Deployment

`.github/workflows/deploy-code-engine.yml`, triggered manually
(`workflow_dispatch`). It builds the image, pushes it to IBM Container
Registry, and updates the Code Engine application to the new tag.

Required GitHub secret: `IBM_CLOUD_API_KEY`.

Required GitHub variables: `IBM_CLOUD_REGION`, `IBM_CLOUD_RESOURCE_GROUP`,
`IBM_CODE_ENGINE_PROJECT`, `IBM_CODE_ENGINE_APP`,
`IBM_CONTAINER_REGISTRY_NAMESPACE`, `IBM_CONTAINER_REGISTRY_HOSTNAME`,
`IBM_CODE_ENGINE_IMAGE_HOSTNAME`, `IBM_CODE_ENGINE_REGISTRY_SECRET`.

## Not IBM-locked

Nothing about the application requires Code Engine. It is a single container
listening on `$PORT`, with no persistent state and no cloud SDK in the runtime
path, so it runs unchanged on Fly.io, Render, Cloud Run or any container host.
The only genuine IBM dependency is watsonx.ai, which is the point of the
project rather than an accident of hosting.

## Free-tier limits worth knowing

- **Container Registry:** 512MB storage, 5GB pull traffic per month. The image
  is roughly 209MB stored. Deploys that change only application code add a few
  megabytes, because the dataset and dependency layers are cached.
- **watsonx.ai Lite:** a monthly token allowance. It stops rather than bills
  when exhausted, which is the right failure mode for a public demo.
