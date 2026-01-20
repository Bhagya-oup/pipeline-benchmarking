"""
Configuration dataclasses for pipeline comparison framework.
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class PipelineConfig:
    """Configuration for a single pipeline."""
    name: str                          # "new_pipeline" or "old_pipeline"
    pipeline_name: str                 # Deepset pipeline name (e.g., "unified_simple")
    workspace_url: str                 # Deepset workspace URL
    api_key: str                       # Deepset API key
    top_k: int = 20                    # Number of results to return
    timeout: int = 120                 # API timeout in seconds
    input_format: str = "deepset_search"  # "deepset_search" or "simple_query"
    endpoint: str = "search"           # "search" or "run"
    param_format: str = "auto"         # "auto", "oed_quotations", "hybrid_prod_ready", or "legacy"


@dataclass
class TestCase:
    """Single test case input."""
    entry_ref: str                     # e.g., "fine_n"
    sense_id: str                      # e.g., "fine_n01_1"
    word: str                          # e.g., "fine"
    pos: str                           # e.g., "n"
    gold_labels: Optional[List[str]] = None  # Optional: ground truth quotation IDs


@dataclass
class PipelineResult:
    """Result from a single pipeline execution."""
    test_case: TestCase
    pipeline_name: str
    quotations: List[dict]             # Ranked quotations with scores
    metadata: dict                     # Sense definition, response time, etc.
    error: Optional[str] = None        # Error message if failed


@dataclass
class ComparisonResult:
    """Result of comparing two pipelines on one test case."""
    test_case: TestCase
    new_result: PipelineResult
    old_result: PipelineResult


@dataclass
class ComparisonConfig:
    """Overall comparison configuration."""
    new_pipeline: PipelineConfig
    old_pipeline: PipelineConfig
    test_data_path: str
    output_dir: str
    parallel_workers: int = 4          # Number of parallel processes
    checkpoint_interval: int = 10      # Save checkpoint every N cases
    rate_limit_per_minute: int = 60    # API rate limit
    metrics_mode: str = 'heuristic'    # 'heuristic', 'llm', or 'gold_labels'
