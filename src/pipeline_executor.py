"""
Pipeline executor for invoking Deepset Cloud pipelines.
Simplified: Just calls the Deepset pipeline, which handles all API calls internally.
"""

from abc import ABC, abstractmethod
from typing import Dict
import requests
import time
import json
import re

from .config import PipelineConfig, PipelineResult, TestCase


class PipelineExecutor(ABC):
    """Abstract base class for pipeline execution."""

    @abstractmethod
    def execute(self, test_case: TestCase) -> PipelineResult:
        """Execute pipeline for a single test case."""
        pass


class DeepsetPipelineExecutor(PipelineExecutor):
    """
    Executor for Deepset Cloud pipelines.

    Sends test case to Deepset pipeline, which internally handles:
    - Fetching sense definition from Solr/OED
    - Fetching quotations from Hero API
    - Embedding, ranking, and filtering
    """

    def __init__(self, config: PipelineConfig, credentials: Dict[str, str]):
        """
        Initialize executor.

        Args:
            config: Pipeline configuration
            credentials: Dictionary with API credentials (only deepset_api_key needed)
        """
        self.config = config
        self.credentials = credentials
        self.session = requests.Session()  # Reuse connection

    def execute(self, test_case: TestCase) -> PipelineResult:
        """
        Execute Deepset pipeline for a single test case.

        The pipeline internally handles all API calls (Solr, Hero API, etc.)

        Args:
            test_case: Test case to process

        Returns:
            PipelineResult with quotations and metadata
        """
        start_time = time.time()
        metadata = {
            'test_case': test_case.sense_id,
            'word': test_case.word,
            'pos': test_case.pos
        }

        try:
            # Call Deepset pipeline using configured endpoint (search or run)
            url = f"{self.config.workspace_url}/pipelines/{self.config.pipeline_name}/{self.config.endpoint}"
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }

            # Input format based on pipeline configuration
            if self.config.input_format == "simple_query":
                # Simple query format for newer pipelines with custom inputs
                # Still needs queries array for /search endpoint
                payload = {
                    "queries": [test_case.entry_ref],  # Required by /search endpoint
                    "params": {
                        "query": test_case.entry_ref,
                        "sense_id": test_case.sense_id,
                        "part_of_speech": test_case.pos
                    }
                }
            else:
                # Default Deepset search format
                # queries: array of query strings
                # params: nested parameters for pipeline components

                # Determine parameter format based on pipeline configuration
                param_format = self.config.param_format

                # Auto-detect format based on pipeline name if set to "auto"
                if param_format == "auto":
                    pipeline_lower = self.config.pipeline_name.lower()
                    if "oed-quotations" in pipeline_lower or "oed_quotations" in pipeline_lower:
                        param_format = "oed_quotations"
                    elif "hybrid_prod_ready" in pipeline_lower or "rare_senses_hybrid_prod_ready" in pipeline_lower:
                        param_format = "hybrid_prod_ready"
                    else:
                        param_format = "legacy"  # Default fallback

                # Build params based on format
                if param_format == "oed_quotations":
                    # OED Quotations pipeline format:
                    # - formatter.sense routes to both sense_extractor.sense_id AND formatter.sense
                    # - quotations.part_of_speech for filtering
                    params = {
                        "formatter": {
                            "sense": test_case.sense_id
                        },
                        "quotations": {
                            "part_of_speech": test_case.pos
                        }
                    }
                elif param_format == "hybrid_prod_ready":
                    # Hybrid Prod Ready pipeline format:
                    # - sense_extractor.sense_id explicitly
                    # - formatter.sense explicitly
                    # - quotations.part_of_speech for filtering
                    params = {
                        "sense_extractor": {
                            "sense_id": test_case.sense_id
                        },
                        "formatter": {
                            "sense": test_case.sense_id
                        },
                        "quotations": {
                            "part_of_speech": test_case.pos
                        }
                    }
                else:
                    # Legacy format (original implementation)
                    # - formatter.sense routes to both components
                    params = {
                        "formatter": {
                            "sense": test_case.sense_id
                        },
                        "quotations": {
                            "part_of_speech": test_case.pos
                        }
                    }

                payload = {
                    "queries": [test_case.entry_ref],
                    "params": params,
                    "debug": False,
                    "view_prompts": False
                }

            # Debug: print first request details
            if not hasattr(self, '_debug_printed'):
                print(f"\n{'='*80}")
                print(f"DEBUG: First API Request")
                print(f"{'='*80}")
                print(f"Pipeline: {self.config.pipeline_name}")
                print(f"Param Format: {param_format if self.config.input_format != 'simple_query' else 'simple_query'}")
                print(f"URL: {url}")
                print(f"Payload: {payload}")
                print(f"{'='*80}\n")
                self._debug_printed = True

            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.config.timeout
            )

            # If error, print response for debugging
            if response.status_code >= 400:
                print(f"\nERROR Response ({response.status_code}):")
                print(f"Response text: {response.text[:500]}")

            response.raise_for_status()

            result_data = response.json()

            # Check for formatter error in response
            is_formatter_error = False
            formatter_error_msg = None

            if 'errors' in result_data and result_data['errors']:
                error_text = str(result_data['errors'])
                # Check for specific formatter error patterns
                if 'number of selections in the JSON does not match' in error_text.lower():
                    is_formatter_error = True
                    formatter_error_msg = error_text
                elif 'int() argument must be a string' in error_text:
                    # This is also a formatter error (LLM didn't return all quotations)
                    is_formatter_error = True
                    formatter_error_msg = error_text

            # Extract results from pipeline output
            # The pipeline returns 1 "answer" object containing a JSON array of quotations
            # Format: {"results": [{"answers": [{"answer": "text with JSON array..."}]}]}
            quotations = []

            # Handle different response formats
            if 'results' in result_data:
                # Multi-query response format
                for query_result in result_data['results']:
                    answers = query_result.get('answers', [])
                    if answers:
                        # Each answer contains multiple quotations in a JSON array
                        for answer in answers:
                            if isinstance(answer, dict) and 'answer' in answer:
                                answer_text = answer['answer']

                                # Extract JSON array from answer text (authoritative source)
                                json_match = re.search(r'\[\s*\{.*\}\s*\]', answer_text, re.DOTALL)
                                if json_match:
                                    try:
                                        parsed_quotations = json.loads(json_match.group(0))
                                        quotations.extend(parsed_quotations)
                                    except Exception as e:
                                        # Fallback: count bullet points if JSON parse fails
                                        bullet_count = answer_text.count('* **')
                                        print(f"Warning: JSON parse failed for {test_case.sense_id}: {e}. Using bullet count: {bullet_count}")
                                        quotations.extend([{'index': i} for i in range(bullet_count)])
                                else:
                                    # No JSON found - use bullet count as last resort
                                    bullet_count = answer_text.count('* **')
                                    if bullet_count > 0:
                                        print(f"Warning: No JSON found for {test_case.sense_id}, using bullet count: {bullet_count}")
                                        quotations.extend([{'index': i} for i in range(bullet_count)])

                    # Also check documents (some pipelines might use this)
                    documents = query_result.get('documents', [])
                    if documents:
                        quotations.extend(documents)

            elif 'answers' in result_data:
                # Single result format with answers
                answers = result_data.get('answers', [])
                for answer in answers:
                    if isinstance(answer, dict) and 'answer' in answer:
                        answer_text = answer['answer']

                        # Extract JSON array (authoritative source)
                        json_match = re.search(r'\[\s*\{.*\}\s*\]', answer_text, re.DOTALL)
                        if json_match:
                            try:
                                quotations = json.loads(json_match.group(0))
                            except Exception as e:
                                # Fallback: bullet count
                                bullet_count = answer_text.count('* **')
                                print(f"Warning: JSON parse failed: {e}. Using bullet count: {bullet_count}")
                                quotations = [{'index': i} for i in range(bullet_count)]
                        else:
                            # No JSON - use bullet count
                            bullet_count = answer_text.count('* **')
                            if bullet_count > 0:
                                print(f"Warning: No JSON found, using bullet count: {bullet_count}")
                                quotations = [{'index': i} for i in range(bullet_count)]

            # Count matches: quotations where primary_sense == input sense_id
            # CRITICAL: Normalize to string to avoid type mismatch (LLM returns strings)
            input_sense_id = str(test_case.sense_id)
            matching_count = 0

            if quotations:
                for quot in quotations:
                    if isinstance(quot, dict):
                        primary_sense = quot.get('primary_sense')
                        selected_senses = quot.get('selected_senses', [])

                        # Normalize to string for comparison
                        if primary_sense is not None:
                            primary_sense = str(primary_sense)

                        # Check if primary sense matches
                        if primary_sense == input_sense_id:
                            matching_count += 1
                        # Or check if input sense is in selected_senses (normalize each)
                        elif input_sense_id in [str(s) for s in selected_senses]:
                            matching_count += 1

            elapsed_time = time.time() - start_time
            metadata['response_time'] = elapsed_time
            metadata['pipeline_name'] = self.config.pipeline_name
            # IMPORTANT: Always use len(quotations) as the total count
            # The JSON array is the authoritative source, not bullet count
            metadata['total_quotations'] = len(quotations)
            metadata['matching_quotations'] = matching_count
            metadata['num_results'] = matching_count  # Use matching count as the main metric

            # Mark formatter errors
            if is_formatter_error:
                metadata['error_type'] = 'formatter_error'

            # If formatter error detected, return error result instead
            if is_formatter_error:
                return PipelineResult(
                    test_case=test_case,
                    pipeline_name=self.config.name,
                    quotations=[],  # No valid quotations
                    metadata=metadata,
                    error=f"FORMATTER_ERROR: {formatter_error_msg[:200]}"
                )

            return PipelineResult(
                test_case=test_case,
                pipeline_name=self.config.name,
                quotations=quotations,  # Keep all quotations for detailed analysis
                metadata=metadata
            )

        except requests.exceptions.HTTPError as e:
            elapsed_time = time.time() - start_time
            metadata['response_time'] = elapsed_time
            metadata['error_type'] = 'http_error'
            metadata['status_code'] = e.response.status_code if hasattr(e, 'response') else None

            return PipelineResult(
                test_case=test_case,
                pipeline_name=self.config.name,
                quotations=[],
                metadata=metadata,
                error=f"HTTP_ERROR: {e.response.status_code if hasattr(e, 'response') else 'error'}: {str(e)}"
            )

        except Exception as e:
            elapsed_time = time.time() - start_time
            metadata['response_time'] = elapsed_time
            metadata['error_type'] = 'pipeline_error'

            return PipelineResult(
                test_case=test_case,
                pipeline_name=self.config.name,
                quotations=[],
                metadata=metadata,
                error=f"PIPELINE_ERROR: {str(e)}"
            )


# Example usage
if __name__ == "__main__":
    import os
    from config import PipelineConfig, TestCase

    # Create test config
    config = PipelineConfig(
        name="test_pipeline",
        pipeline_name="unified_simple",
        workspace_url=os.getenv("DEEPSET_WORKSPACE_URL", "https://ol-hero-lm.deepset.cloud"),
        api_key=os.getenv("DEEPSET_API_KEY", ""),
        top_k=20
    )

    credentials = {
        'deepset_api_key': config.api_key
    }

    # Create test case
    test_case = TestCase(
        entry_ref="fine_n",
        sense_id="fine_n01_1",
        word="fine",
        pos="noun"
    )

    # Execute
    executor = DeepsetPipelineExecutor(config, credentials)
    result = executor.execute(test_case)

    print(f"Pipeline: {result.pipeline_name}")
    print(f"Test Case: {result.test_case.sense_id}")
    print(f"Quotations Found: {len(result.quotations)}")
    print(f"Response Time: {result.metadata.get('response_time', 0):.2f}s")
    if result.error:
        print(f"Error: {result.error}")
