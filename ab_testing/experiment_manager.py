"""
A/B Testing Experiment Manager

Manages A/B tests for Nordic news content optimization including:
- Test design and setup
- Traffic splitting and variant assignment
- Statistical analysis and significance testing
- Results tracking and reporting
"""

import logging
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy import stats
import pandas as pd
import yaml
import os

logger = logging.getLogger(__name__)


class ExperimentManager:
    """
    Manages A/B testing experiments for content optimization.
    
    Features:
    - Test design and configuration
    - Traffic splitting algorithms
    - Statistical significance testing
    - Results analysis and reporting
    - GDPR-compliant user assignment
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the experiment manager."""
        self.config = self._load_config(config_path)
        self.active_experiments = {}
        self.experiment_results = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            return {}
    
    def create_experiment(self, name: str, description: str, 
                         traffic_split: float = 0.5,
                         test_type: str = 'content_optimization',
                         target_metric: str = 'ctr',
                         minimum_sample_size: int = 1000,
                         significance_level: float = 0.05) -> str:
        """
        Create a new A/B test experiment.
        
        Args:
            name: Experiment name
            description: Experiment description
            traffic_split: Traffic split ratio (0.0 to 1.0)
            test_type: Type of test ('content_optimization', 'layout_test', 'personalization')
            target_metric: Primary metric to optimize
            minimum_sample_size: Minimum sample size for statistical power
            significance_level: Statistical significance level (alpha)
        
        Returns:
            Experiment ID
        """
        experiment_id = str(uuid.uuid4())
        
        experiment = {
            'id': experiment_id,
            'name': name,
            'description': description,
            'traffic_split': traffic_split,
            'test_type': test_type,
            'target_metric': target_metric,
            'minimum_sample_size': minimum_sample_size,
            'significance_level': significance_level,
            'status': 'draft',
            'created_at': datetime.now().isoformat(),
            'start_date': None,
            'end_date': None,
            'variants': {},
            'results': {}
        }
        
        self.active_experiments[experiment_id] = experiment
        logger.info(f"Created experiment: {name} (ID: {experiment_id})")
        
        return experiment_id
    
    def add_variant(self, experiment_id: str, variant_name: str, 
                   variant_config: Dict) -> bool:
        """
        Add a variant to an experiment.
        
        Args:
            experiment_id: Experiment identifier
            variant_name: Name of the variant
            variant_config: Configuration for the variant
        
        Returns:
            True if variant was added successfully
        """
        if experiment_id not in self.active_experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        experiment = self.active_experiments[experiment_id]
        
        if len(experiment['variants']) >= 2:
            logger.warning("Only 2 variants supported per experiment")
            return False
        
        variant = {
            'name': variant_name,
            'config': variant_config,
            'assigned_users': set(),
            'metrics': {},
            'created_at': datetime.now().isoformat()
        }
        
        experiment['variants'][variant_name] = variant
        logger.info(f"Added variant {variant_name} to experiment {experiment_id}")
        
        return True
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Start an A/B test experiment."""
        if experiment_id not in self.active_experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        experiment = self.active_experiments[experiment_id]
        
        if len(experiment['variants']) < 2:
            logger.error("Experiment must have at least 2 variants")
            return False
        
        experiment['status'] = 'running'
        experiment['start_date'] = datetime.now().isoformat()
        
        logger.info(f"Started experiment: {experiment['name']}")
        return True
    
    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop an A/B test experiment."""
        if experiment_id not in self.active_experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        experiment = self.active_experiments[experiment_id]
        experiment['status'] = 'completed'
        experiment['end_date'] = datetime.now().isoformat()
        
        # Analyze results
        self._analyze_experiment_results(experiment_id)
        
        logger.info(f"Stopped experiment: {experiment['name']}")
        return True
    
    def assign_user_to_variant(self, experiment_id: str, user_id: str) -> Optional[str]:
        """
        Assign a user to a variant using consistent hashing.
        
        Args:
            experiment_id: Experiment identifier
            user_id: User identifier
        
        Returns:
            Variant name or None if not assigned
        """
        if experiment_id not in self.active_experiments:
            return None
        
        experiment = self.active_experiments[experiment_id]
        
        if experiment['status'] != 'running':
            return None
        
        variants = list(experiment['variants'].keys())
        if len(variants) < 2:
            return None
        
        # Use consistent hashing for user assignment
        hash_input = f"{experiment_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # Assign based on traffic split
        traffic_split = experiment['traffic_split']
        if (hash_value % 100) < (traffic_split * 100):
            variant_name = variants[0]  # Control group
        else:
            variant_name = variants[1]  # Treatment group
        
        # Track assignment
        experiment['variants'][variant_name]['assigned_users'].add(user_id)
        
        return variant_name
    
    def record_metric(self, experiment_id: str, user_id: str, 
                     metric_name: str, metric_value: float) -> bool:
        """
        Record a metric for a user in an experiment.
        
        Args:
            experiment_id: Experiment identifier
            user_id: User identifier
            metric_name: Name of the metric
            metric_value: Value of the metric
        
        Returns:
            True if metric was recorded successfully
        """
        if experiment_id not in self.active_experiments:
            return False
        
        experiment = self.active_experiments[experiment_id]
        
        # Find which variant the user is assigned to
        variant_name = None
        for vname, variant in experiment['variants'].items():
            if user_id in variant['assigned_users']:
                variant_name = vname
                break
        
        if not variant_name:
            return False
        
        # Record metric
        if metric_name not in experiment['variants'][variant_name]['metrics']:
            experiment['variants'][variant_name]['metrics'][metric_name] = []
        
        experiment['variants'][variant_name]['metrics'][metric_name].append({
            'user_id': user_id,
            'value': metric_value,
            'timestamp': datetime.now().isoformat()
        })
        
        return True
    
    def _analyze_experiment_results(self, experiment_id: str):
        """Analyze experiment results and calculate statistical significance."""
        experiment = self.active_experiments[experiment_id]
        target_metric = experiment['target_metric']
        significance_level = experiment['significance_level']
        
        results = {}
        
        for variant_name, variant in experiment['variants'].items():
            if target_metric not in variant['metrics']:
                continue
            
            metric_values = [m['value'] for m in variant['metrics'][target_metric]]
            
            if not metric_values:
                continue
            
            # Calculate basic statistics
            mean_value = np.mean(metric_values)
            std_value = np.std(metric_values, ddof=1)
            sample_size = len(metric_values)
            
            results[variant_name] = {
                'mean': mean_value,
                'std': std_value,
                'sample_size': sample_size,
                'values': metric_values
            }
        
        # Perform statistical tests if we have data for both variants
        if len(results) == 2:
            variant_names = list(results.keys())
            control_data = results[variant_names[0]]['values']
            treatment_data = results[variant_names[1]]['values']
            
            # Perform t-test
            t_stat, p_value = stats.ttest_ind(control_data, treatment_data)
            
            # Calculate effect size (Cohen's d)
            pooled_std = np.sqrt(
                ((len(control_data) - 1) * results[variant_names[0]]['std']**2 +
                 (len(treatment_data) - 1) * results[variant_names[1]]['std']**2) /
                (len(control_data) + len(treatment_data) - 2)
            )
            cohens_d = (results[variant_names[1]]['mean'] - results[variant_names[0]]['mean']) / pooled_std
            
            # Determine significance
            is_significant = p_value < significance_level
            
            # Calculate confidence interval
            control_mean = results[variant_names[0]]['mean']
            treatment_mean = results[variant_names[1]]['mean']
            mean_diff = treatment_mean - control_mean
            
            # Standard error of the difference
            se_diff = pooled_std * np.sqrt(1/len(control_data) + 1/len(treatment_data))
            
            # 95% confidence interval
            ci_lower = mean_diff - 1.96 * se_diff
            ci_upper = mean_diff + 1.96 * se_diff
            
            experiment['results'] = {
                'control_variant': variant_names[0],
                'treatment_variant': variant_names[1],
                'control_mean': control_mean,
                'treatment_mean': treatment_mean,
                'mean_difference': mean_diff,
                'p_value': p_value,
                'is_significant': is_significant,
                'effect_size': cohens_d,
                'confidence_interval': (ci_lower, ci_upper),
                'sample_sizes': {
                    variant_names[0]: len(control_data),
                    variant_names[1]: len(treatment_data)
                }
            }
            
            logger.info(f"Experiment {experiment_id} analysis complete. "
                       f"Significant: {is_significant}, p-value: {p_value:.4f}")
    
    def get_experiment_results(self, experiment_id: str) -> Optional[Dict]:
        """Get results for a specific experiment."""
        if experiment_id not in self.active_experiments:
            return None
        
        experiment = self.active_experiments[experiment_id]
        return experiment.get('results', {})
    
    def get_all_experiments(self) -> List[Dict]:
        """Get all experiments with their status."""
        experiments = []
        for experiment_id, experiment in self.active_experiments.items():
            experiments.append({
                'id': experiment_id,
                'name': experiment['name'],
                'status': experiment['status'],
                'created_at': experiment['created_at'],
                'start_date': experiment['start_date'],
                'end_date': experiment['end_date'],
                'variants': list(experiment['variants'].keys()),
                'has_results': 'results' in experiment and bool(experiment['results'])
            })
        
        return experiments
    
    def get_experiment_summary(self, experiment_id: str) -> Optional[Dict]:
        """Get a summary of experiment results."""
        if experiment_id not in self.active_experiments:
            return None
        
        experiment = self.active_experiments[experiment_id]
        results = experiment.get('results', {})
        
        if not results:
            return {
                'status': experiment['status'],
                'message': 'No results available yet'
            }
        
        # Calculate improvement percentage
        control_mean = results['control_mean']
        treatment_mean = results['treatment_mean']
        improvement = ((treatment_mean - control_mean) / control_mean) * 100
        
        return {
            'experiment_name': experiment['name'],
            'status': experiment['status'],
            'control_mean': round(control_mean, 4),
            'treatment_mean': round(treatment_mean, 4),
            'improvement_percentage': round(improvement, 2),
            'is_significant': results['is_significant'],
            'p_value': round(results['p_value'], 4),
            'effect_size': round(results['effect_size'], 4),
            'confidence_interval': [
                round(results['confidence_interval'][0], 4),
                round(results['confidence_interval'][1], 4)
            ],
            'sample_sizes': results['sample_sizes']
        }
    
    def export_experiment_data(self, experiment_id: str, format: str = 'json') -> str:
        """Export experiment data in the specified format."""
        if experiment_id not in self.active_experiments:
            return ""
        
        experiment = self.active_experiments[experiment_id]
        
        if format == 'json':
            import json
            return json.dumps(experiment, indent=2, default=str)
        elif format == 'csv':
            # Export metrics data as CSV
            data = []
            for variant_name, variant in experiment['variants'].items():
                for metric_name, metric_values in variant['metrics'].items():
                    for metric in metric_values:
                        data.append({
                            'variant': variant_name,
                            'metric': metric_name,
                            'value': metric['value'],
                            'user_id': metric['user_id'],
                            'timestamp': metric['timestamp']
                        })
            
            df = pd.DataFrame(data)
            return df.to_csv(index=False)
        else:
            return ""


def main():
    """Main function for testing the experiment manager."""
    manager = ExperimentManager()
    
    # Create a test experiment
    experiment_id = manager.create_experiment(
        name="Headline Optimization Test",
        description="Test different headline styles for engagement",
        traffic_split=0.5,
        target_metric="ctr"
    )
    
    # Add variants
    manager.add_variant(experiment_id, "control", {
        "headline_style": "traditional",
        "font_size": "large"
    })
    
    manager.add_variant(experiment_id, "treatment", {
        "headline_style": "clickbait",
        "font_size": "extra_large"
    })
    
    # Start experiment
    manager.start_experiment(experiment_id)
    
    # Simulate user assignments and metrics
    for i in range(1000):
        user_id = f"user_{i}"
        variant = manager.assign_user_to_variant(experiment_id, user_id)
        
        if variant:
            # Simulate CTR metric
            if variant == "control":
                ctr = np.random.normal(0.15, 0.05)  # 15% CTR with 5% std
            else:
                ctr = np.random.normal(0.18, 0.05)  # 18% CTR with 5% std
            
            manager.record_metric(experiment_id, user_id, "ctr", ctr)
    
    # Stop experiment and analyze
    manager.stop_experiment(experiment_id)
    
    # Get results
    results = manager.get_experiment_summary(experiment_id)
    print("Experiment Results:")
    print(f"Improvement: {results['improvement_percentage']}%")
    print(f"Significant: {results['is_significant']}")
    print(f"P-value: {results['p_value']}")
    print(f"Effect size: {results['effect_size']}")


if __name__ == "__main__":
    main()