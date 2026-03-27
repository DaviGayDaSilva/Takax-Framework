#!/usr/bin/env python3
"""
SDK Tests - Test SDK functionality
"""

import sys
import unittest
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSDKImports(unittest.TestCase):
    """Test SDK module imports"""
    
    def test_import_client(self):
        """Test client module import"""
        from sdk import TakaxClient
        self.assertIsNotNone(TakaxClient)
        
    def test_import_sandbox(self):
        """Test sandbox module import"""
        from sdk import Sandbox
        self.assertIsNotNone(Sandbox)
        
    def test_import_build(self):
        """Test build module import"""
        from sdk import BuildManager
        self.assertIsNotNone(BuildManager)
        
    def test_import_types(self):
        """Test types module import"""
        from sdk import OSRecipe, BuildConfig, BuildResult
        self.assertIsNotNone(OSRecipe)
        self.assertIsNotNone(BuildConfig)
        self.assertIsNotNone(BuildResult)


class TestTakaxClient(unittest.TestCase):
    """Test TakaxClient"""
    
    def test_client_creation(self):
        """Test client can be created"""
        from sdk import TakaxClient
        client = TakaxClient()
        self.assertIsNotNone(client)
        
    def test_list_templates(self):
        """Test listing templates"""
        from sdk import TakaxClient
        client = TakaxClient()
        templates = client.list_templates()
        self.assertGreater(len(templates), 0)
        
    def test_get_template(self):
        """Test getting template"""
        from sdk import TakaxClient
        client = TakaxClient()
        template = client.get_template('debian-minimal')
        self.assertIsNotNone(template)
        
    def test_create_project(self):
        """Test project creation"""
        from sdk import TakaxClient
        client = TakaxClient()
        project = client.create_project(
            name="test-project",
            description="Test project"
        )
        self.assertIsNotNone(project)
        self.assertEqual(project.name, "test-project")


class TestTypes(unittest.TestCase):
    """Test type definitions"""
    
    def test_os_recipe(self):
        """Test OSRecipe"""
        from sdk.types import OSRecipe
        
        recipe = OSRecipe(
            name="Test OS",
            base_image="debian:latest",
            packages=["python3"]
        )
        
        self.assertEqual(recipe.name, "Test OS")
        self.assertEqual(recipe.base_image, "debian:latest")
        self.assertIn("python3", recipe.packages)
        
    def test_build_result(self):
        """Test BuildResult"""
        from sdk.types import BuildResult, BuildStatus
        
        result = BuildResult(
            build_id="test-123",
            status=BuildStatus.COMPLETED,
            output_path="/tmp/output"
        )
        
        self.assertEqual(result.build_id, "test-123")
        self.assertEqual(result.status, BuildStatus.COMPLETED)
        self.assertTrue(result.is_success())
        
    def test_template(self):
        """Test Template"""
        from sdk.types import Template
        
        template = Template(
            name="test-template",
            description="Test template",
            base_image="debian:latest"
        )
        
        self.assertEqual(template.name, "test-template")


class TestSandbox(unittest.TestCase):
    """Test Sandbox wrapper"""
    
    def test_sandbox_creation(self):
        """Test sandbox can be created"""
        from sdk.sandbox import Sandbox
        sandbox = Sandbox("docker", "debian:latest")
        self.assertIsNotNone(sandbox)
        
    def test_get_info(self):
        """Test getting sandbox info"""
        from sdk.sandbox import Sandbox
        sandbox = Sandbox("docker", "debian:latest")
        info = sandbox.get_info()
        self.assertIn('type', info)
        self.assertEqual(info['type'], 'docker')


class TestBuildManager(unittest.TestCase):
    """Test BuildManager"""
    
    def test_build_manager_creation(self):
        """Test build manager can be created"""
        from sdk.sandbox import Sandbox
        from sdk.build import BuildManager
        
        sandbox = Sandbox()
        manager = BuildManager(sandbox)
        self.assertIsNotNone(manager)


if __name__ == '__main__':
    unittest.main()