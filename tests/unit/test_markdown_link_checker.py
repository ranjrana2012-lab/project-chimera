import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_checker_module():
    script_path = REPO_ROOT / "scripts" / "check_markdown_links.py"
    spec = importlib.util.spec_from_file_location("check_markdown_links", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_markdown_checker_resolves_links_relative_to_source_file(tmp_path):
    checker = load_checker_module()
    docs = tmp_path / "docs"
    guides = docs / "guides"
    guides.mkdir(parents=True)
    (tmp_path / "README.md").write_text("# Root\n", encoding="utf-8")
    (guides / "STUDENT_LAPTOP_SETUP.md").write_text("# Student\n", encoding="utf-8")
    (guides / "DEPLOYMENT.md").write_text(
        "\n".join(
            [
                "[Student](STUDENT_LAPTOP_SETUP.md)",
                "[Root](../../README.md)",
                "[External](https://example.com/project)",
                "[Anchor](#local-section)",
            ]
        ),
        encoding="utf-8",
    )

    broken = checker.find_broken_links([docs], repo_root=tmp_path)

    assert broken == []


def test_markdown_checker_reports_missing_local_links(tmp_path):
    checker = load_checker_module()
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "README.md").write_text("[Missing](missing.md)", encoding="utf-8")

    broken = checker.find_broken_links([docs], repo_root=tmp_path)

    assert [item.target for item in broken] == ["missing.md"]
