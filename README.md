# Takax Framework

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.10+-yellow.svg" alt="Python">
</p>

**Takax** is an open-source framework that enables you to create custom Linux operating systems through natural language conversations. It provides a sandbox environment for building, with real-time terminal display.

## 🎯 Features

- **Chat-to-OS**: Create Linux systems using natural language descriptions
- **Multiple Interfaces**: CLI, Web (Cloud), and SDK
- **Real-time Terminal**: Live terminal output during builds
- **Sandbox Isolation**: Secure build environment using Docker
- **Template System**: Pre-built configurations for common use cases
- **Build Caching**: Faster rebuilds with intelligent caching

## 🚀 Quick Start

### CLI Version

```bash
# Start interactive mode
python -m cli.main

# Build from description
python -m cli.main -d "Create minimal Debian with Python and SSH"

# Use template
python -m cli.main -t debian-python
```

### Cloud/Web Version

```bash
# Install dependencies
pip install -r requirements.txt

# Run cloud server
python -m cloud.app

# Open browser
# http://localhost:8080
```

### SDK Usage

```python
from sdk import TakaxClient

# Create OS from description
client = TakaxClient()
result = client.create_os(
    description="Minimal Debian with Python and SSH",
    output_format="chroot"
)

print(f"Build complete: {result.output_path}")
```

## 📁 Project Structure

```
Takax-Framework/
├── cli/                 # CLI version
│   ├── main.py         # CLI entry point
│   ├── chat.py         # Chat handler
│   ├── terminal.py     # Terminal display
│   ├── config.py       # Configuration
│   └── templates.py    # OS templates
│
├── cloud/              # Cloud/Web version
│   ├── app.py         # FastAPI application
│   ├── routes.py      # API routes
│   ├── websocket.py   # WebSocket handler
│   ├── terminal.py    # Server terminal
│   └── templates/     # HTML templates
│
├── sdk/               # Python SDK
│   ├── client.py      # Main client
│   ├── sandbox.py     # Sandbox wrapper
│   ├── build.py       # Build manager
│   └── types.py       # Type definitions
│
├── sandbox/           # Sandbox system
│   ├── manager.py     # Container manager
│   ├── builder.py     # Build engine
│   ├── recipe.py      # Recipe parser
│   └── cache.py       # Build cache
│
└── examples/          # Usage examples
    ├── basic.py       # Basic examples
    └── advanced.py    # Advanced examples
```

## 🔧 Installation

```bash
# Clone repository
git clone https://github.com/takax/takax-framework.git
cd Takax-Framework

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## 💻 Usage Examples

### CLI

```bash
# Interactive mode
$ python -m cli.main
Takax Framework v1.0.0
Creating Linux OS via chat - Interactive Mode

🎯 Describe your OS (or 'quit' to exit):
> Create a minimal Debian with Python

🤖 I'll create a minimal Debian OS with Python. Starting build...
```

### Cloud

Open http://localhost:8080 in your browser to access the web interface.

### SDK

```python
# From description
from sdk import create_os

result = create_os("Ubuntu server with Docker and SSH")
print(result.output_path)

# From template
from sdk import TakaxClient

client = TakaxClient()
result = client.create_from_template("docker-host")
```

## 📦 Available Templates

| Template | Description |
|----------|-------------|
| debian-minimal | Minimal Debian base system |
| ubuntu-server | Ubuntu Server with common tools |
| debian-python | Debian with Python development |
| alpine-minimal | Ultra-minimal Alpine Linux |
| docker-host | System with Docker support |
| web-server | Nginx + PHP + MariaDB |

## 🔨 Build Output

After build completes, you'll get:
- `chroot/` - Root filesystem
- `metadata.json` - Build metadata
- `README.md` - Usage instructions

## 🛡️ Security

- Sandboxed build environment
- No network access during build (optional)
- Input sanitization
- Resource limits (CPU, memory, disk)

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit your changes
4. Push to branch
5. Create Pull Request

---

<p align="center">Built with ❤️ by Takax Team</p>