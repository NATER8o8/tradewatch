
# DigitalOcean Terraform

## Usage
```bash
cd ops/terraform
export TF_VAR_do_token=your_do_api_token
terraform init
terraform apply -var='domain=your-domain.com'
```
This provisions a Docker droplet and starts the production stack.
