#!/usr/bin/env python3
"""Tests for site generator."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "bin"))

from site_generator import generate_html_template, generate_product_page, generate_site


def test_html_template_generation():
    """Test HTML template generation."""
    metadata = {
        "page_title": "Test Page",
        "meta_description": "Test Description",
        "keywords": ["test", "page"],
        "og_title": "Test OG",
        "og_description": "Test OG Description",
        "canonical_url": "https://example.com/test",
        "robots": "index, follow",
        "tracking_id": "G-TEST",
    }

    html = generate_html_template("Test Title", "<p>Test content</p>", metadata)

    # Verify HTML structure
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "Test Page" in html  # Title
    assert "Test Description" in html  # Meta description
    assert "Test content" in html  # Content
    assert "G-TEST" in html  # Analytics

    print("✓ test_html_template_generation passed")


def test_product_page_generation():
    """Test product page generation."""
    edition = {
        "id": "edition-test-macos-v1",
        "name": "Test Edition",
        "target_platform": "macos",
        "description": "Test edition description",
        "feature_set": ["core-device-control", "api-access"],
    }

    packaging = {
        "deployment_instructions": [
            "Step 1: Download",
            "Step 2: Install",
        ],
        "prerequisites": [
            "macOS 10.15+",
            "2GB RAM",
        ],
    }

    content, metadata = generate_product_page(edition, packaging)

    assert "core-device-control" in content
    assert "api-access" in content
    assert "Step 1: Download" in content
    assert "macOS 10.15+" in content

    # Verify metadata
    assert metadata["page_title"]
    assert metadata["meta_description"]
    assert "keywords" in metadata
    assert len(metadata["keywords"]) > 0

    print("✓ test_product_page_generation passed")


def test_site_generation():
    """Test complete site generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        editions_data = {
            "editions": [
                {
                    "edition": {
                        "id": "edition-test-macos-v1",
                        "name": "macOS Edition",
                        "target_platform": "macos",
                        "description": "Test macOS edition",
                        "feature_set": ["core-device-control"],
                    },
                    "packaging": {
                        "deployment_instructions": ["Step 1"],
                        "prerequisites": ["macOS 10.15+"],
                    },
                },
                {
                    "edition": {
                        "id": "edition-test-windows-v1",
                        "name": "Windows Edition",
                        "target_platform": "windows",
                        "description": "Test Windows edition",
                        "feature_set": ["core-device-control"],
                    },
                    "packaging": {
                        "deployment_instructions": ["Step 1"],
                        "prerequisites": ["Windows 10+"],
                    },
                },
            ]
        }

        result = generate_site(editions_data, tmpdir)

        # Verify result structure
        assert "output_directory" in result
        assert "generated_pages" in result
        assert "sitemap" in result

        # Verify files were created
        output_path = Path(tmpdir)
        assert (output_path / "index.html").exists()
        assert (output_path / "edition-test-macos-v1.html").exists()
        assert (output_path / "edition-test-windows-v1.html").exists()
        assert (output_path / "sitemap.xml").exists()

        # Verify page count
        assert len(result["generated_pages"]) >= 2

        print("✓ test_site_generation passed")


def test_html_content_structure():
    """Test that generated HTML has proper structure."""
    metadata = {
        "page_title": "Test",
        "meta_description": "Test",
        "keywords": ["test"],
        "canonical_url": "https://example.com/test",
        "tracking_id": "G-TEST",
    }

    html = generate_html_template("Test", "<p>Content</p>", metadata)

    # Verify critical HTML elements
    assert "<head>" in html
    assert "</head>" in html
    assert "<body>" in html
    assert "</body>" in html
    assert "<meta" in html
    assert "<title>" in html

    # Verify SEO elements
    assert "charset" in html
    assert "viewport" in html
    assert "og:title" in html
    assert "canonical" in html

    print("✓ test_html_content_structure passed")


def test_sitemap_generation():
    """Test that sitemap is valid XML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        editions_data = {
            "editions": [
                {
                    "edition": {
                        "id": "edition-test-v1",
                        "name": "Test Edition",
                        "target_platform": "web",
                        "description": "Test",
                        "feature_set": [],
                    },
                    "packaging": {
                        "deployment_instructions": [],
                        "prerequisites": [],
                    },
                }
            ]
        }

        result = generate_site(editions_data, tmpdir)

        # Read and verify sitemap
        sitemap_path = Path(result["sitemap"])
        sitemap_content = sitemap_path.read_text()

        assert '<?xml version="1.0"' in sitemap_content
        assert "<urlset" in sitemap_content
        assert "<url>" in sitemap_content
        assert "<loc>" in sitemap_content
        assert "</urlset>" in sitemap_content

        print("✓ test_sitemap_generation passed")


if __name__ == "__main__":
    test_html_template_generation()
    test_product_page_generation()
    test_site_generation()
    test_html_content_structure()
    test_sitemap_generation()

    print("\n✅ All site generator tests passed!")
