#!/usr/bin/env python3
"""
Vertex AI Deployment Helper
============================

User-friendly deployment script with:
- Pre-flight validation
- Interactive configuration
- Cost estimation
- Deployment monitoring
- Rollback support

Usage:
    python deploy_helper.py --agent-path healthcare_agent_deploy
    python deploy_helper.py --validate-only
    python deploy_helper.py --list-deployments
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


# ============================================================================
# DEPLOYMENT VALIDATION
# ============================================================================

@dataclass
class ValidationResult:
    """Result of validation checks."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]


class DeploymentValidator:
    """Validates deployment configuration and environment."""

    def validate_all(self, agent_path: str) -> ValidationResult:
        """Run all validation checks."""
        errors = []
        warnings = []
        info = []

        # Check agent path exists
        if not os.path.exists(agent_path):
            errors.append(f"Agent path does not exist: {agent_path}")
            return ValidationResult(False, errors, warnings, info)

        # Validate required files
        result = self._validate_required_files(agent_path)
        errors.extend(result[0])
        warnings.extend(result[1])
        info.extend(result[2])

        # Validate configuration
        config_result = self._validate_config(agent_path)
        errors.extend(config_result[0])
        warnings.extend(config_result[1])
        info.extend(config_result[2])

        # Validate agent code
        agent_result = self._validate_agent_code(agent_path)
        errors.extend(agent_result[0])
        warnings.extend(agent_result[1])
        info.extend(agent_result[2])

        # Check environment
        env_result = self._check_environment()
        errors.extend(env_result[0])
        warnings.extend(env_result[1])
        info.extend(env_result[2])

        is_valid = len(errors) == 0

        return ValidationResult(is_valid, errors, warnings, info)

    def _validate_required_files(self, agent_path: str) -> Tuple[List, List, List]:
        """Check for required files."""
        errors, warnings, info = [], [], []

        required = {
            'agent.py': 'Main agent code',
            '.agent_engine_config.json': 'Configuration file',
            'requirements.txt': 'Python dependencies'
        }

        recommended = {
            'README.md': 'Documentation',
            '.gcloudignore': 'Deployment ignore patterns'
        }

        for file, desc in required.items():
            path = os.path.join(agent_path, file)
            if not os.path.exists(path):
                errors.append(f"Missing required file: {file} ({desc})")
            else:
                info.append(f"✓ Found {file}")

        for file, desc in recommended.items():
            path = os.path.join(agent_path, file)
            if not os.path.exists(path):
                warnings.append(f"Recommended file missing: {file} ({desc})")

        return errors, warnings, info

    def _validate_config(self, agent_path: str) -> Tuple[List, List, List]:
        """Validate configuration file."""
        errors, warnings, info = [], [], []

        config_path = os.path.join(agent_path, '.agent_engine_config.json')

        if not os.path.exists(config_path):
            return errors, warnings, info

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Validate min_instances
            min_inst = config.get('min_instances')
            if min_inst is None:
                errors.append("Config missing 'min_instances'")
            elif not isinstance(min_inst, int) or min_inst < 0:
                errors.append(f"Invalid min_instances: {min_inst} (must be >= 0)")
            elif min_inst == 0:
                info.append("✓ Auto-scaling enabled (min_instances=0, cost-optimized)")
            elif min_inst == 1:
                warnings.append("1 always-on instance (24/7 costs apply)")
            else:
                warnings.append(f"{min_inst} always-on instances (high 24/7 costs)")

            # Validate max_instances
            max_inst = config.get('max_instances')
            if max_inst is None:
                errors.append("Config missing 'max_instances'")
            elif not isinstance(max_inst, int) or max_inst < 1:
                errors.append(f"Invalid max_instances: {max_inst} (must be >= 1)")
            elif min_inst is not None and max_inst < min_inst:
                errors.append(f"max_instances ({max_inst}) < min_instances ({min_inst})")
            elif max_inst > 10:
                warnings.append(f"High max_instances ({max_inst}) may cause cost spikes")
            else:
                info.append(f"✓ Max instances: {max_inst}")

            # Validate resources
            if 'resource_limits' in config:
                res = config['resource_limits']

                # CPU validation
                cpu = res.get('cpu', '0')
                try:
                    cpu_float = float(cpu)
                    if cpu_float < 1:
                        warnings.append("CPU < 1 may cause slow performance")
                    elif cpu_float > 8:
                        warnings.append(f"High CPU ({cpu_float}) increases costs significantly")
                    else:
                        info.append(f"✓ CPU: {cpu_float} vCPUs")
                except ValueError:
                    errors.append(f"Invalid CPU value: {cpu}")

                # Memory validation
                memory = res.get('memory', '0')
                if memory.endswith('Gi'):
                    try:
                        mem_gb = float(memory[:-2])
                        if mem_gb < 2:
                            warnings.append("Memory < 2Gi may cause out-of-memory errors")
                        elif mem_gb > 32:
                            warnings.append(f"High memory ({mem_gb}Gi) increases costs significantly")
                        else:
                            info.append(f"✓ Memory: {mem_gb}Gi")
                    except ValueError:
                        errors.append(f"Invalid memory value: {memory}")
                else:
                    errors.append(f"Memory must end with 'Gi': {memory}")
            else:
                warnings.append("No resource_limits specified (will use defaults)")

            # Timeout validation
            timeout = config.get('timeout_seconds', 300)
            if not isinstance(timeout, int) or timeout < 1:
                errors.append(f"Invalid timeout_seconds: {timeout}")
            elif timeout < 60:
                warnings.append("Timeout < 60s may cause incomplete operations")
            elif timeout > 600:
                warnings.append("Timeout > 600s (10min) may cause long waits")
            else:
                info.append(f"✓ Timeout: {timeout}s")

        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in config file: {e}")
        except Exception as e:
            errors.append(f"Error reading config: {e}")

        return errors, warnings, info

    def _validate_agent_code(self, agent_path: str) -> Tuple[List, List, List]:
        """Validate agent.py code."""
        errors, warnings, info = [], [], []

        agent_file = os.path.join(agent_path, 'agent.py')

        if not os.path.exists(agent_file):
            return errors, warnings, info

        try:
            with open(agent_file, 'r') as f:
                content = f.read()

            # Check for root_agent
            if 'root_agent' not in content:
                errors.append("Missing 'root_agent' variable (deployment will fail)")
            else:
                info.append("✓ Found root_agent definition")

            # Check for ADK imports
            if 'from google.adk' not in content and 'import google.adk' not in content:
                warnings.append("Missing Google ADK imports")

            # Check for hardcoded secrets
            secret_patterns = [
                ('api_key', 'API keys'),
                ('password', 'passwords'),
                ('secret', 'secrets'),
                ('token', 'tokens')
            ]

            for pattern, name in secret_patterns:
                if pattern in content.lower() and '=' in content:
                    # Check if it's just in a comment or string
                    lines_with_pattern = [line for line in content.split('\n') if pattern in line.lower() and '=' in line]
                    if any(not line.strip().startswith('#') for line in lines_with_pattern):
                        warnings.append(f"Possible hardcoded {name} detected - use environment variables")
                        break

            # Check file size
            file_size = len(content)
            if file_size > 100000:  # 100KB
                warnings.append(f"Large agent.py ({file_size} bytes) - consider splitting into modules")

        except Exception as e:
            errors.append(f"Error reading agent.py: {e}")

        return errors, warnings, info

    def _check_environment(self) -> Tuple[List, List, List]:
        """Check environment setup."""
        errors, warnings, info = [], [], []

        # Check required env vars
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('PROJECT_ID')
        if not project_id:
            errors.append("Missing environment variable: GOOGLE_CLOUD_PROJECT or PROJECT_ID")
        else:
            info.append(f"✓ Project ID: {project_id}")

        region = os.environ.get('GOOGLE_CLOUD_LOCATION') or os.environ.get('REGION')
        if not region:
            warnings.append("Missing GOOGLE_CLOUD_LOCATION or REGION (will use default)")
        else:
            info.append(f"✓ Region: {region}")

        # Check gcloud CLI
        try:
            result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                info.append(f"✓ gcloud CLI: {version}")
            else:
                warnings.append("gcloud CLI found but may not be configured correctly")
        except FileNotFoundError:
            errors.append("gcloud CLI not found - install Google Cloud SDK")

        # Check ADK CLI
        try:
            result = subprocess.run(['adk', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                info.append("✓ ADK CLI installed")
            else:
                warnings.append("ADK CLI found but may not be working")
        except FileNotFoundError:
            errors.append("adk CLI not found - install with: pip install google-genai-adk")

        return errors, warnings, info


# ============================================================================
# COST ESTIMATOR
# ============================================================================

class CostEstimator:
    """Estimate deployment costs."""

    # Approximate costs (as of 2024, subject to change)
    COST_PER_VCPU_HOUR = 0.0526  # USD
    COST_PER_GB_HOUR = 0.0058     # USD
    HOURS_PER_MONTH = 730

    def estimate_monthly_cost(self, config: Dict) -> Dict[str, float]:
        """Estimate monthly cost based on configuration."""
        min_instances = config.get('min_instances', 0)
        max_instances = config.get('max_instances', 1)
        resources = config.get('resource_limits', {})

        cpu = float(resources.get('cpu', '2'))
        memory_str = resources.get('memory', '4Gi')
        memory_gb = float(memory_str.replace('Gi', ''))

        # Always-on costs (min instances)
        always_on_cpu_cost = min_instances * cpu * self.COST_PER_VCPU_HOUR * self.HOURS_PER_MONTH
        always_on_mem_cost = min_instances * memory_gb * self.COST_PER_GB_HOUR * self.HOURS_PER_MONTH
        always_on_total = always_on_cpu_cost + always_on_mem_cost

        # Per-hour costs for scaling
        per_instance_hour = cpu * self.COST_PER_VCPU_HOUR + memory_gb * self.COST_PER_GB_HOUR

        # Estimate max cost (if all instances run 24/7)
        max_cpu_cost = max_instances * cpu * self.COST_PER_VCPU_HOUR * self.HOURS_PER_MONTH
        max_mem_cost = max_instances * memory_gb * self.COST_PER_GB_HOUR * self.HOURS_PER_MONTH
        max_total = max_cpu_cost + max_mem_cost

        return {
            'always_on_monthly': round(always_on_total, 2),
            'per_instance_hour': round(per_instance_hour, 4),
            'max_monthly': round(max_total, 2),
            'currency': 'USD'
        }


# ============================================================================
# DEPLOYMENT MANAGER
# ============================================================================

class DeploymentManager:
    """Manages deployment process."""

    def __init__(self, agent_path: str, verbose: bool = True):
        self.agent_path = agent_path
        self.verbose = verbose
        self.validator = DeploymentValidator()
        self.cost_estimator = CostEstimator()

    def print_header(self, text: str):
        """Print formatted header."""
        print(f"\n{'=' * 70}")
        print(f"  {text}")
        print(f"{'=' * 70}\n")

    def print_result(self, result: ValidationResult):
        """Print validation results."""
        if result.errors:
            print(f"\n❌ ERRORS ({len(result.errors)}):")
            for error in result.errors:
                print(f"  • {error}")

        if result.warnings:
            print(f"\n⚠️  WARNINGS ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"  • {warning}")

        if result.info:
            print(f"\n✓ CHECKS PASSED ({len(result.info)}):")
            for info in result.info:
                print(f"  • {info}")

    def validate(self) -> bool:
        """Run validation checks."""
        self.print_header("🔍 Pre-Flight Validation")

        result = self.validator.validate_all(self.agent_path)
        self.print_result(result)

        if result.is_valid:
            print("\n✓ All checks passed! Ready to deploy.\n")

            # Show cost estimate
            try:
                config_path = os.path.join(self.agent_path, '.agent_engine_config.json')
                with open(config_path, 'r') as f:
                    config = json.load(f)

                costs = self.cost_estimator.estimate_monthly_cost(config)

                print("\n💰 COST ESTIMATE:")
                print(f"  • Always-on cost: ${costs['always_on_monthly']:.2f}/month")
                print(f"  • Per instance-hour: ${costs['per_instance_hour']:.4f}")
                print(f"  • Max cost (all instances 24/7): ${costs['max_monthly']:.2f}/month")
                print(f"\n  Note: Actual costs depend on usage patterns.")
                print(f"  With auto-scaling (min_instances=0), you only pay when active.\n")

            except Exception as e:
                print(f"\n⚠️  Could not estimate costs: {e}\n")

            return True
        else:
            print("\n❌ Validation failed. Fix errors above before deploying.\n")
            return False

    def deploy(self, dry_run: bool = False) -> bool:
        """Deploy agent to Vertex AI."""
        # First validate
        if not self.validate():
            return False

        # Confirm deployment
        if not dry_run:
            print("\n" + "=" * 70)
            response = input("  Proceed with deployment? [y/N]: ").strip().lower()
            print("=" * 70 + "\n")

            if response != 'y':
                print("Deployment cancelled.\n")
                return False

        # Get environment variables
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('PROJECT_ID')
        region = os.environ.get('GOOGLE_CLOUD_LOCATION') or os.environ.get('REGION', 'us-central1')

        # Build deployment command
        config_file = os.path.join(self.agent_path, '.agent_engine_config.json')

        cmd = [
            'adk', 'deploy', 'agent_engine',
            '--project', project_id,
            '--region', region,
            self.agent_path,
            '--agent_engine_config_file', config_file
        ]

        print(f"🚀 Deployment Command:")
        print(f"  {' '.join(cmd)}\n")

        if dry_run:
            print("DRY RUN - Command not executed.\n")
            return True

        # Execute deployment
        self.print_header("🚀 Deploying to Vertex AI")

        try:
            print("Starting deployment... (this may take 2-5 minutes)\n")

            result = subprocess.run(cmd, capture_output=not self.verbose, text=True)

            if result.returncode == 0:
                print("\n✓ Deployment successful!")
                print("\nNext steps:")
                print("  1. Test your agent with a simple query")
                print("  2. Monitor logs: gcloud logging read")
                print("  3. Set up alerts for errors")
                print("  4. Document your deployment\n")
                return True
            else:
                print(f"\n❌ Deployment failed with code {result.returncode}")
                if not self.verbose:
                    print(f"\nError: {result.stderr}")
                return False

        except FileNotFoundError:
            print("❌ 'adk' command not found. Install with: pip install google-genai-adk\n")
            return False
        except Exception as e:
            print(f"❌ Deployment failed: {e}\n")
            return False

    def list_deployments(self):
        """List existing deployments."""
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('PROJECT_ID')
        region = os.environ.get('GOOGLE_CLOUD_LOCATION') or os.environ.get('REGION', 'us-central1')

        if not project_id:
            print("❌ PROJECT_ID not set\n")
            return

        self.print_header(f"📋 Deployments in {project_id} ({region})")

        try:
            # This is a placeholder - actual command depends on ADK CLI
            cmd = ['adk', 'list', 'agent_engines', '--project', project_id, '--region', region]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(result.stdout)
            else:
                print("No deployments found or error accessing deployments.\n")

        except Exception as e:
            print(f"Error listing deployments: {e}\n")


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Vertex AI Deployment Helper with validation and cost estimation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate configuration only
  python deploy_helper.py --agent-path healthcare_agent_deploy --validate-only

  # Deploy with interactive confirmation
  python deploy_helper.py --agent-path healthcare_agent_deploy

  # Dry run (show command without executing)
  python deploy_helper.py --agent-path healthcare_agent_deploy --dry-run

  # List existing deployments
  python deploy_helper.py --list-deployments

Environment Variables:
  GOOGLE_CLOUD_PROJECT or PROJECT_ID     Your GCP project ID
  GOOGLE_CLOUD_LOCATION or REGION        Deployment region (default: us-central1)
        """
    )

    parser.add_argument(
        '--agent-path',
        default='healthcare_agent_deploy',
        help='Path to agent directory (default: healthcare_agent_deploy)'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only run validation checks, do not deploy'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show deployment command without executing'
    )

    parser.add_argument(
        '--list-deployments',
        action='store_true',
        help='List existing deployments'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )

    args = parser.parse_args()

    # Create deployment manager
    manager = DeploymentManager(args.agent_path, verbose=not args.quiet)

    # List deployments
    if args.list_deployments:
        manager.list_deployments()
        return 0

    # Validate only
    if args.validate_only:
        success = manager.validate()
        return 0 if success else 1

    # Deploy
    success = manager.deploy(dry_run=args.dry_run)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
