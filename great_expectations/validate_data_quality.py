#!/usr/bin/env python3
"""
Data Quality Validation Script for Tampa Rent Signals
Integrates Great Expectations with dbt pipeline for comprehensive validation
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
import great_expectations as gx
from great_expectations.checkpoint import SimpleCheckpoint
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.exceptions import CheckpointNotFoundError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data_quality_validation.log')
    ]
)
logger = logging.getLogger(__name__)

class RentSignalsDataValidator:
    """
    Manages data quality validation for the rent signals pipeline
    """
    
    def __init__(self, ge_root_dir: str = None):
        """Initialize the data validator"""
        if ge_root_dir is None:
            ge_root_dir = Path(__file__).parent
        
        self.ge_root_dir = Path(ge_root_dir)
        self.context = None
        self._initialize_context()
    
    def _initialize_context(self):
        """Initialize Great Expectations context"""
        try:
            self.context = gx.get_context(project_root_dir=str(self.ge_root_dir))
            logger.info(f"Initialized GE context from {self.ge_root_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize GE context: {e}")
            raise
    
    def validate_staging_models(self) -> Dict[str, bool]:
        """
        Validate all staging models (stg_aptlist, stg_zori, stg_fred)
        Returns: Dict mapping model names to validation success status
        """
        logger.info("Starting staging models validation...")
        
        checkpoint_name = "staging_data_quality_checkpoint"
        results = {}
        
        try:
            checkpoint = self.context.get_checkpoint(checkpoint_name)
            checkpoint_result = checkpoint.run()
            
            # Parse results
            for validation_result in checkpoint_result.list_validation_results():
                suite_name = validation_result.expectation_suite_name
                success = validation_result.success
                
                model_name = suite_name.replace('_suite', '')
                results[model_name] = success
                
                logger.info(f"Staging validation - {model_name}: {'PASSED' if success else 'FAILED'}")
                
                if not success:
                    failed_expectations = [
                        exp for exp in validation_result.results 
                        if not exp.success
                    ]
                    logger.warning(f"{model_name} had {len(failed_expectations)} failed expectations")
            
            return results
            
        except CheckpointNotFoundError:
            logger.error(f"Checkpoint {checkpoint_name} not found")
            return {}
        except Exception as e:
            logger.error(f"Error running staging validation: {e}")
            return {}
    
    def validate_core_models(self) -> Dict[str, bool]:
        """
        Validate core models (fact tables and dimensions)
        Returns: Dict mapping model names to validation success status
        """
        logger.info("Starting core models validation...")
        
        checkpoint_name = "core_data_quality_checkpoint"
        results = {}
        
        try:
            checkpoint = self.context.get_checkpoint(checkpoint_name)
            checkpoint_result = checkpoint.run()
            
            # Parse results
            for validation_result in checkpoint_result.list_validation_results():
                suite_name = validation_result.expectation_suite_name
                success = validation_result.success
                
                model_name = suite_name.replace('_suite', '')
                results[model_name] = success
                
                logger.info(f"Core validation - {model_name}: {'PASSED' if success else 'FAILED'}")
                
                if not success:
                    # Log specific failures for debugging
                    for result in validation_result.results:
                        if not result.success:
                            expectation_type = result.expectation_config.expectation_type
                            logger.warning(f"Failed expectation in {model_name}: {expectation_type}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error running core validation: {e}")
            return {}
    
    def validate_mart_models(self, mart_names: List[str] = None) -> Dict[str, bool]:
        """
        Validate specific mart models
        Args:
            mart_names: List of mart model names to validate
        Returns: Dict mapping model names to validation success status
        """
        if mart_names is None:
            mart_names = ['mart_rent_trends']
        
        logger.info(f"Starting mart models validation for: {mart_names}")
        results = {}
        
        for mart_name in mart_names:
            try:
                suite_name = f"{mart_name}_suite"
                
                # Create batch request for the mart table
                batch_request = RuntimeBatchRequest(
                    datasource_name="snowflake_db",
                    data_connector_name="default_inferred_data_connector",
                    data_asset_name=mart_name,
                    runtime_parameters={"query": f"SELECT * FROM {mart_name}"},
                    batch_identifiers={"default_identifier_name": "default_identifier"}
                )
                
                # Get the expectation suite
                suite = self.context.get_expectation_suite(suite_name)
                
                # Create and run validator
                validator = self.context.get_validator(
                    batch_request=batch_request,
                    expectation_suite=suite
                )
                
                validation_result = validator.validate()
                results[mart_name] = validation_result.success
                
                logger.info(f"Mart validation - {mart_name}: {'PASSED' if validation_result.success else 'FAILED'}")
                
            except Exception as e:
                logger.error(f"Error validating {mart_name}: {e}")
                results[mart_name] = False
        
        return results
    
    def run_full_validation_suite(self) -> Dict[str, Dict[str, bool]]:
        """
        Run complete validation across all layers
        Returns: Nested dict with validation results by layer
        """
        logger.info("Starting full validation suite...")
        
        results = {
            'staging': self.validate_staging_models(),
            'core': self.validate_core_models(),
            'marts': self.validate_mart_models()
        }
        
        # Summary logging
        total_models = sum(len(layer_results) for layer_results in results.values())
        total_passed = sum(
            sum(1 for success in layer_results.values() if success) 
            for layer_results in results.values()
        )
        
        logger.info(f"Validation complete: {total_passed}/{total_models} models passed")
        
        # Log any failures
        for layer, layer_results in results.items():
            failed_models = [model for model, success in layer_results.items() if not success]
            if failed_models:
                logger.warning(f"Failed models in {layer}: {failed_models}")
        
        return results
    
    def get_data_docs_url(self) -> str:
        """Get the URL for Great Expectations data docs"""
        docs_path = self.ge_root_dir / "uncommitted" / "data_docs" / "local_site" / "index.html"
        return f"file://{docs_path.absolute()}"

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run data quality validation")
    parser.add_argument(
        '--layer', 
        choices=['staging', 'core', 'marts', 'all'],
        default='all',
        help='Which layer to validate'
    )
    parser.add_argument(
        '--mart-names',
        nargs='+',
        help='Specific mart names to validate (only used with --layer marts)'
    )
    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Exit on first validation failure'
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = RentSignalsDataValidator()
    
    # Run requested validations
    if args.layer == 'staging':
        results = {'staging': validator.validate_staging_models()}
    elif args.layer == 'core':
        results = {'core': validator.validate_core_models()}
    elif args.layer == 'marts':
        results = {'marts': validator.validate_mart_models(args.mart_names)}
    else:  # all
        results = validator.run_full_validation_suite()
    
    # Check for failures and exit appropriately
    all_passed = all(
        all(layer_results.values()) 
        for layer_results in results.values()
    )
    
    if not all_passed:
        logger.error("Some validations failed!")
        if args.fail_fast:
            sys.exit(1)
    
    # Print data docs URL
    docs_url = validator.get_data_docs_url()
    logger.info(f"View detailed results at: {docs_url}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())