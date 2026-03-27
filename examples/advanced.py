#!/usr/bin/env python3
"""
Advanced SDK Example - Advanced usage of Takax SDK with callbacks and custom recipes
"""

import sys
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sdk import TakaxClient, OSRecipe
from sdk.types import BuildConfig


# Custom callback for build progress
def build_callback(event: str, *args, **kwargs):
    """Handle build events"""
    if event == "start":
        print(f"\n🚀 Build started!")
    elif event == "progress":
        progress, message = args
        print(f"  [{int(progress)}%] {message}")
    elif event == "complete":
        print(f"\n✅ Build completed!")
    elif event == "error":
        error = args[0] if args else "Unknown error"
        print(f"\n❌ Build failed: {error}")


def example_custom_recipe():
    """Example: Create OS from custom recipe"""
    print("\n" + "=" * 50)
    print("Custom Recipe Example")
    print("=" * 50)
    
    client = TakaxClient()
    
    # Create custom recipe
    recipe = OSRecipe(
        name="Custom Web Server",
        base_image="ubuntu:22.04",
        packages=[
            "nginx",
            "python3",
            "python3-pip",
            "openssh-server",
            "curl",
            "vim"
        ],
        config={
            "type": "server",
            "ssh": {"enabled": True},
            "nginx": {"enabled": True},
            "python": {"version": "3.10"}
        },
        output_format="chroot"
    )
    
    # Register callback
    client.on_build_progress(build_callback)
    
    # Build from recipe
    result = client.create_from_recipe(recipe, "./custom-output")
    
    print(f"\nResult:")
    print(f"  Build ID: {result.build_id}")
    print(f"  Status: {result.status.value}")
    print(f"  Output: {result.output_path}")
    print(f"  Duration: {result.duration:.2f}s")
    
    return result


def example_with_config():
    """Example: Build with custom configuration"""
    print("\n" + "=" * 50)
    print("Custom Configuration Example")
    print("=" * 50)
    
    # Create client with custom config
    from sdk.client import ClientConfig
    
    config = ClientConfig(
        output_dir="./my-builds",
        sandbox_image="debian:bookworm-slim",
        timeout=1800
    )
    
    client = TakaxClient(config)
    
    # Build with custom config
    result = client.create_os(
        description="Debian with Docker and Compose",
        output_format="tarball",
        packages=["docker.io", "docker-compose"],
        callback=build_callback
    )
    
    print(f"\nResult:")
    print(f"  Status: {result.status.value}")
    print(f"  Output: {result.output_path}")
    
    return result


def example_parallel_builds():
    """Example: Multiple parallel builds"""
    print("\n" + "=" * 50)
    print("Parallel Builds Example")
    print("=" * 50)
    
    from concurrent.futures import ThreadPoolExecutor
    import threading
    
    client = TakaxClient()
    results = []
    lock = threading.Lock()
    
    def build_task(name: str, description: str):
        result = client.create_os(description=description)
        with lock:
            results.append((name, result))
            
    # Define builds
    builds = [
        ("debian-python", "Debian with Python"),
        ("ubuntu-docker", "Ubuntu with Docker"),
        ("alpine-minimal", "Minimal Alpine"),
    ]
    
    # Run parallel builds
    print("Starting parallel builds...")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(build_task, name, desc)
            for name, desc in builds
        ]
        
        for future in futures:
            future.result()
    
    # Print results
    print("\nBuild Results:")
    for name, result in results:
        status = "✅" if result.is_success() else "❌"
        print(f"  {status} {name}: {result.status.value}")
    
    return results


def example_project_management():
    """Example: Project management"""
    print("\n" + "=" * 50)
    print("Project Management Example")
    print("=" * 50)
    
    client = TakaxClient()
    
    # Create project
    project = client.create_project(
        name="web-app-infrastructure",
        description="Custom OS for web application hosting",
        config={
            "packages": ["nginx", "python3", "postgresql"],
            "type": "server"
        }
    )
    
    print(f"Created project:")
    print(f"  ID: {project.id}")
    print(f"  Name: {project.name}")
    print(f"  Description: {project.description}")
    
    # Save project
    client.save_project(project, "./projects")
    print("\nProject saved to ./projects")
    
    # Load project
    loaded = client.load_project(f"./projects/{project.id}.json")
    print(f"Loaded project: {loaded.name}")


def example_template_usage():
    """Example: Advanced template usage"""
    print("\n" + "=" * 50)
    print("Template Usage Example")
    print("=" * 50)
    
    client = TakaxClient()
    
    # List all templates
    templates = client.list_templates()
    print("Available templates:")
    for t in templates:
        print(f"  - {t.name}")
        print(f"    {t.description}")
        print(f"    Base: {t.base_image}")
        if t.packages:
            print(f"    Packages: {', '.join(t.packages[:3])}...")
    
    # Use template with customization
    template = client.get_template("docker-host")
    if template:
        print(f"\nUsing '{template.name}' template with custom config:")
        
        result = client.create_from_template(
            template_name="docker-host",
            custom_config={
                "hostname": "custom-docker-host",
                "ssh": True
            }
        )
        
        print(f"  Status: {result.status.value}")
        print(f"  Output: {result.output_path}")


def main():
    print("🚀 Takax SDK - Advanced Examples")
    print("=" * 50)
    
    try:
        # Run examples
        example_custom_recipe()
        time.sleep(1)
        
        example_with_config()
        time.sleep(1)
        
        example_project_management()
        time.sleep(1)
        
        example_template_usage()
        
        print("\n" + "=" * 50)
        print("✅ All advanced examples completed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()