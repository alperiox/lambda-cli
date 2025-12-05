# Lambda Labs Cloud CLI

A simple command-line interface for managing Lambda Labs Cloud GPU instances.

## Installation

1. Clone this repository and navigate to the directory:
```bash
cd lambda-cli
```

2. Install the package:
```bash
pip install -e .
```

3. (Optional) If the `lambda` command is not in your PATH, add this to your shell configuration:
```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/Library/Python/3.11/bin:$PATH"
```

Or use the full path: `/Users/<username>/Library/Python/3.11/bin/lambda`

## Quick Start

1. **Configure your API key:**
```bash
lambda config set-key YOUR_API_KEY
```

You can get your API key from the [Lambda Cloud Console](https://cloud.lambdalabs.com/api-keys).

2. **List available instance types:**
```bash
lambda instances look
```

3. **List your running instances:**
```bash
lambda instances ls
```

## Commands

### Configuration

#### Set API Key
```bash
lambda config set-key <api-key>
```
Save your Lambda Labs Cloud API key to `~/.lambda/config.json`.

#### Show Configuration
```bash
lambda config show
```
Display your current configuration (API key will be masked).

#### Clear Configuration
```bash
lambda config clear
```
Remove the configuration file.

### Instances

#### List Instances (`ls`)
```bash
lambda instances ls
```
List all your running instances with their details (ID, name, instance type, region, status, IP).

#### Look at Instance Types (`look`)
```bash
lambda instances look
```
Display all available instance types with specs and available regions.

**Options:**
- `--available` / `-a`: Show only instance types with available capacity

Example:
```bash
lambda instances look --available
```

#### Get Instance Details (`get`)
```bash
lambda instances get <instance-id>
```
Get detailed information about a specific instance.

Example:
```bash
lambda instances get 0920582c7ff041399e34823a0be62549
```

#### Launch Instances (`launch`)
```bash
lambda instances launch \
  --type <instance-type> \
  --region <region> \
  --ssh-key <ssh-key-name> \
  [--file-system <fs-name>] \
  [--quantity <number>] \
  [--name <instance-name>]
```

Launch new GPU instances.

**Required Options:**
- `--type` / `-t`: Instance type (e.g., `gpu_1x_a10`)
- `--region` / `-r`: Region (e.g., `us-west-1`)
- `--ssh-key` / `-k`: SSH key name (can be specified multiple times)

**Optional Options:**
- `--file-system` / `-f`: File system name to attach (can be specified multiple times)
- `--quantity` / `-q`: Number of instances to launch (default: 1)
- `--name` / `-n`: Name for the instance

Example:
```bash
lambda instances launch \
  --type gpu_1x_a10 \
  --region us-west-1 \
  --ssh-key my-ssh-key \
  --quantity 1 \
  --name my-gpu-instance
```

#### Terminate Instances (`terminate`)
```bash
lambda instances terminate <instance-id> [<instance-id> ...]
```

Terminate one or more instances. You'll be prompted for confirmation unless you use `--yes`.

**Options:**
- `--yes` / `-y`: Skip confirmation prompt

Example:
```bash
lambda instances terminate 0920582c7ff041399e34823a0be62549 --yes
```

#### Restart Instances (`restart`)
```bash
lambda instances restart <instance-id> [<instance-id> ...]
```

Restart one or more instances.

Example:
```bash
lambda instances restart 0920582c7ff041399e34823a0be62549
```

## API Documentation

This CLI uses the Lambda Labs Cloud API. For more information, see:
- [Lambda Cloud API Documentation](https://docs-api.lambda.ai/api/cloud)
- [Creating and managing instances](https://docs.lambda.ai/public-cloud/on-demand/creating-managing-instances/)

## Configuration File

The CLI stores your API key in `~/.lambda/config.json`. This file has restricted permissions (600) for security.

## Requirements

- Python >= 3.11
- httpx >= 0.27.0
- typer >= 0.12.0
- rich >= 13.7.0

## License

MIT
