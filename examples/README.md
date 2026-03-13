# Example Configurations

This directory contains example configuration files for various S3-compatible providers.

## Usage

1. Copy the appropriate example file for your provider
2. Update the values with your actual credentials
3. **Remove the secret key** from the file (it will be prompted interactively)
4. Run s3check with the config file:

```bash
s3check --config examples/aws-config.json
```

## Available Examples

- [`aws-config.json`](aws-config.json) - AWS S3 configuration
- [`minio-config.json`](minio-config.json) - MinIO configuration

## Security Note

⚠️ **Never commit files containing your actual secret keys to version control!**

The examples provided here contain placeholder values only. When using config files:

- Always add your actual config files to `.gitignore`
- Use environment variables for sensitive data when possible
- Consider using secret management tools for production environments

## Creating Your Own Config

You can generate a config file by running s3check in interactive mode and choosing to save the configuration when prompted:

```bash
s3check
# Follow the prompts
# Choose "Yes" when asked to save config
```

The generated config file will exclude the secret key automatically.
