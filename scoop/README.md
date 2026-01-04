# Trifecta Scoop Manifest

This directory contains the Scoop manifest for installing Trifecta on Windows systems.

## What is Scoop?

[Scoop](https://scoop.sh/) is a command-line installer for Windows that makes installing and managing applications easy.

## Installation

### Prerequisites

1. Install Scoop (if not already installed):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

2. Install dependencies:
```powershell
scoop install python uv
```

### Installing Trifecta

#### Option 1: From This Repository (Development)

```powershell
# Add this repository as a Scoop bucket
scoop bucket add trifecta https://github.com/fegome90-cmd/trifecta_dope

# Install trifecta
scoop install trifecta
```

#### Option 2: From Local Manifest

```powershell
# Clone the repository
git clone https://github.com/fegome90-cmd/trifecta_dope.git
cd trifecta_dope

# Install from local manifest
scoop install .\scoop\trifecta.json
```

## Usage

After installation, you can use `trifecta` from any command prompt or PowerShell:

```powershell
# Check installation
trifecta --help

# Create a new trifecta context
trifecta create --segment my-project --path ./my-project

# Build context pack
trifecta ctx build --segment ./my-project
```

## Updating

To update Trifecta to the latest version:

```powershell
scoop update trifecta
```

## Uninstalling

To uninstall Trifecta:

```powershell
scoop uninstall trifecta
```

## Manifest Structure

The `trifecta.json` manifest includes:

- **version**: Current version of Trifecta
- **description**: Brief description of the tool
- **homepage**: Project homepage URL
- **license**: Software license
- **architecture**: Download URLs for different architectures
- **depends**: Required dependencies (Python, uv)
- **installer**: Installation scripts
- **bin**: Executable binaries and shims
- **checkver**: Version checking configuration
- **autoupdate**: Automatic update configuration

## Troubleshooting

### Issue: `uv not found`

Install uv first:
```powershell
scoop install uv
```

### Issue: `python not found`

Install Python first:
```powershell
scoop install python
```

### Issue: Installation fails

1. Check that all dependencies are installed
2. Ensure you have internet connection
3. Try running PowerShell as Administrator
4. Check Scoop logs: `scoop status`

## Contributing

To update the manifest:

1. Edit `trifecta.json`
2. Update the version number
3. Update the hash (leave empty for auto-calculation)
4. Test locally: `scoop install .\scoop\trifecta.json`
5. Submit a pull request

## Support

For issues related to:
- **Scoop manifest**: Open an issue on this repository
- **Trifecta usage**: See main [README.md](../README.md)
- **Scoop itself**: Visit [scoop.sh](https://scoop.sh/)
