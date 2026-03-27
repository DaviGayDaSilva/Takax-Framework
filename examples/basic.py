#!/usr/bin/env python3
"""
Basic SDK Example - Simple usage of Takax SDK
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sdk import TakaxClient


def main():
    print("🔧 Takax SDK - Basic Example\n")
    
    # Create client
    client = TakaxClient()
    
    # Example 1: Create OS from description
    print("=" * 50)
    print("Example 1: Create OS from description")
    print("=" * 50)
    
    result = client.create_os(
        description="Minimal Debian with Python and SSH",
        output_format="chroot"
    )
    
    print(f"Build ID: {result.build_id}")
    print(f"Status: {result.status.value}")
    print(f"Output: {result.output_path}")
    print(f"Duration: {result.duration:.2f}s")
    
    if result.logs:
        print("\nBuild Logs:")
        for log in result.logs[:5]:
            print(f"  {log}")
    
    # Example 2: Use template
    print("\n" + "=" * 50)
    print("Example 2: Use template")
    print("=" * 50)
    
    templates = client.list_templates()
    print("Available templates:")
    for t in templates:
        print(f"  - {t.name}: {t.description}")
    
    result = client.create_from_template(
        template_name="debian-python",
        output_dir="./takax-example-output"
    )
    
    print(f"\nBuild from template:")
    print(f"  Status: {result.status.value}")
    print(f"  Output: {result.output_path}")
    
    # Example 3: Create project
    print("\n" + "=" * 50)
    print("Example 3: Create project")
    print("=" * 50)
    
    project = client.create_project(
        name="my-custom-os",
        description="Custom Debian with Docker"
    )
    
    print(f"Project created:")
    print(f"  ID: {project.id}")
    print(f"  Name: {project.name}")
    print(f"  Created: {project.created_at}")
    
    print("\n✅ Examples completed!")


if __name__ == "__main__":
    main()