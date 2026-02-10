"""Tests for TaskDecomposer — playbook loading and step generation."""

import tempfile
from pathlib import Path

import pytest
import yaml

from modules.orchestrator.decomposer import Playbook, Step, TaskDecomposer


def _write_playbook(tmp_dir: Path, name: str, content: dict) -> None:
    (tmp_dir / f"{name}.yaml").write_text(yaml.dump(content))


class TestTaskDecomposer:
    def setup_method(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.decomposer = TaskDecomposer(playbooks_dir=str(self.tmp))

    # ------------------------------------------------------------------
    # list_playbooks
    # ------------------------------------------------------------------

    def test_list_empty(self):
        assert self.decomposer.list_playbooks() == []

    def test_list_finds_yaml_files(self):
        _write_playbook(self.tmp, "alpha", {"name": "alpha", "steps": []})
        _write_playbook(self.tmp, "beta", {"name": "beta", "steps": []})
        names = self.decomposer.list_playbooks()
        assert "alpha" in names
        assert "beta" in names

    # ------------------------------------------------------------------
    # load_playbook
    # ------------------------------------------------------------------

    def test_load_missing_returns_none(self):
        assert self.decomposer.load_playbook("nonexistent") is None

    def test_load_basic_playbook(self):
        _write_playbook(self.tmp, "simple", {
            "name": "simple",
            "description": "A simple test playbook",
            "steps": [
                {"name": "step1", "tool_type": "llm", "capability": "general", "prompt": "Do X"},
            ],
        })
        pb = self.decomposer.load_playbook("simple")
        assert pb is not None
        assert pb.name == "simple"
        assert pb.description == "A simple test playbook"
        assert len(pb.steps) == 1
        assert pb.steps[0].name == "step1"

    def test_load_playbook_caches(self):
        _write_playbook(self.tmp, "cached", {"name": "cached", "steps": []})
        pb1 = self.decomposer.load_playbook("cached")
        pb2 = self.decomposer.load_playbook("cached")
        assert pb1 is pb2  # Same object from cache

    def test_load_playbook_with_synthesis(self):
        _write_playbook(self.tmp, "with_synth", {
            "name": "with_synth",
            "steps": [],
            "synthesis": {"tool_type": "llm", "prompt": "Review everything"},
        })
        pb = self.decomposer.load_playbook("with_synth")
        assert pb.synthesis is not None
        assert pb.synthesis["prompt"] == "Review everything"

    def test_load_step_depends_on(self):
        _write_playbook(self.tmp, "deps", {
            "name": "deps",
            "steps": [
                {"name": "a", "tool_type": "llm", "capability": "general", "prompt": "A"},
                {"name": "b", "tool_type": "llm", "capability": "general", "prompt": "B",
                 "depends_on": ["a"]},
            ],
        })
        pb = self.decomposer.load_playbook("deps")
        assert pb.steps[1].depends_on == ["a"]

    # ------------------------------------------------------------------
    # find_playbook
    # ------------------------------------------------------------------

    def test_find_no_match_returns_none(self):
        _write_playbook(self.tmp, "rest_api", {
            "name": "rest_api",
            "description": "Build REST API with database",
            "steps": [],
        })
        assert self.decomposer.find_playbook("totally unrelated gibberish xyz") is None

    def test_find_matches_by_name(self):
        _write_playbook(self.tmp, "cli_tool", {
            "name": "cli_tool",
            "description": "Build a command-line tool",
            "steps": [],
        })
        pb = self.decomposer.find_playbook("build cli tool")
        assert pb is not None
        assert pb.name == "cli_tool"

    def test_find_matches_by_description(self):
        _write_playbook(self.tmp, "rest_api", {
            "name": "rest_api",
            "description": "REST API with PostgreSQL backend",
            "steps": [],
        })
        pb = self.decomposer.find_playbook("create a REST API")
        assert pb is not None

    # ------------------------------------------------------------------
    # decompose
    # ------------------------------------------------------------------

    def test_decompose_none_gives_fallback(self):
        steps = self.decomposer.decompose(None, user_requirements="Do something")
        assert len(steps) == 1
        assert steps[0].name == "execute"
        assert steps[0].tool_type == "llm"

    def test_decompose_substitutes_user_requirements(self):
        _write_playbook(self.tmp, "subst", {
            "name": "subst",
            "steps": [
                {"name": "s1", "tool_type": "llm", "capability": "general",
                 "prompt": "Build: {user_requirements}"},
            ],
        })
        pb = self.decomposer.load_playbook("subst")
        steps = self.decomposer.decompose(pb, user_requirements="a calculator")
        assert "a calculator" in steps[0].prompt

    def test_decompose_substitutes_extra_variables(self):
        _write_playbook(self.tmp, "vars", {
            "name": "vars",
            "steps": [
                {"name": "s1", "tool_type": "llm", "capability": "general",
                 "prompt": "Model: {model_name}"},
            ],
        })
        pb = self.decomposer.load_playbook("vars")
        steps = self.decomposer.decompose(pb, variables={"model_name": "GPT-4"})
        assert "GPT-4" in steps[0].prompt

    def test_decompose_does_not_mutate_original(self):
        _write_playbook(self.tmp, "immut", {
            "name": "immut",
            "steps": [
                {"name": "s1", "tool_type": "llm", "capability": "general",
                 "prompt": "Original: {user_requirements}"},
            ],
        })
        pb = self.decomposer.load_playbook("immut")
        original_prompt = pb.steps[0].prompt
        self.decomposer.decompose(pb, user_requirements="changed")
        assert pb.steps[0].prompt == original_prompt  # Original untouched

    # ------------------------------------------------------------------
    # build_synthesis_step
    # ------------------------------------------------------------------

    def test_synthesis_step_none_when_no_synthesis(self):
        _write_playbook(self.tmp, "no_synth", {"name": "no_synth", "steps": []})
        pb = self.decomposer.load_playbook("no_synth")
        assert self.decomposer.build_synthesis_step(pb) is None

    def test_synthesis_step_built_correctly(self):
        _write_playbook(self.tmp, "has_synth", {
            "name": "has_synth",
            "steps": [],
            "synthesis": {
                "tool_type": "llm",
                "capability": "synthesis",
                "prompt": "Synthesize: {user_requirements}",
            },
        })
        pb = self.decomposer.load_playbook("has_synth")
        step = self.decomposer.build_synthesis_step(pb, user_requirements="widgets")
        assert step is not None
        assert step.name == "_synthesis"
        assert "widgets" in step.prompt

    # ------------------------------------------------------------------
    # Step.to_task_dict
    # ------------------------------------------------------------------

    def test_step_to_task_dict(self):
        step = Step(
            name="my_step",
            tool_type="llm",
            capability="code_generation",
            prompt="write code",
            output="code_out",
        )
        d = step.to_task_dict()
        assert d["name"] == "my_step"
        assert d["tool_type"] == "llm"
        assert d["capability"] == "code_generation"
        assert d["output"] == "code_out"

    def test_step_output_defaults_to_name(self):
        step = Step(name="gen_models", tool_type="llm", capability="general", prompt="x", output="")
        d = step.to_task_dict()
        assert d["output"] == "gen_models"
