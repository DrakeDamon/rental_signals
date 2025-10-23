# Great Expectations Data Quality Suite

Comprehensive data quality validation for the Tampa Rent Signals pipeline, integrated with dbt models and Snowflake.

## 🎯 Overview

This Great Expectations setup provides:
- **Automated validation** of dbt staging, core, and mart models
- **Comprehensive test suites** with business rule validation
- **Snowflake integration** for direct database validation
- **Checkpoint-based workflows** for different pipeline stages
- **Data documentation** with automatic report generation

## 📁 Structure

```
great_expectations/
├── great_expectations.yml      # Main configuration
├── expectations/              # Expectation suites
│   ├── staging/              # Staging model validations
│   ├── core/                 # Core model validations
│   └── marts/                # Mart model validations
├── checkpoints/              # Validation checkpoints
├── validate_data_quality.py  # Python validation script
├── requirements.txt          # Dependencies
└── README.md                # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd great_expectations
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Set your Snowflake connection details:

```bash
export SNOWFLAKE_ACCOUNT="your_account"
export SNOWFLAKE_USER="your_user"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_DATABASE="RENTS"
export SNOWFLAKE_WAREHOUSE="WH_XS"
export SNOWFLAKE_ROLE="ACCOUNTADMIN"
export SNOWFLAKE_SCHEMA="DBT_DEV"
```

### 3. Run Validations

```bash
# Validate all layers
python validate_data_quality.py --layer all

# Validate specific layer
python validate_data_quality.py --layer staging
python validate_data_quality.py --layer core
python validate_data_quality.py --layer marts

# Validate specific marts
python validate_data_quality.py --layer marts --mart-names mart_rent_trends

# Fail fast on first error
python validate_data_quality.py --layer all --fail-fast
```

## 📊 Expectation Suites

### Staging Models

**`stg_aptlist_suite`**
- Row count validation (1K - 500K rows)
- Column completeness checks
- Rent index range validation (0-2000)
- Population bounds checking
- Data quality scoring validation
- Business key uniqueness

**`stg_zori_suite`**
- Row count validation (5K - 1M rows)
- ZORI value range validation (500-8000)
- Metro size rank validation
- State name format validation
- Size category enumeration
- High data quality standards

**`stg_fred_suite`**
- Economic indicator validation
- FRED series ID format checking
- CPI category validation
- Seasonal adjustment validation
- Value range checking for CPI data
- Reliability scoring validation

### Core Models

**`fact_rent_zori_suite`**
- Fact table grain uniqueness
- ZORI value business rules
- YoY/MoM change validation
- Growth category enumeration
- National ranking validation
- Data quality scoring

**`fact_rent_aptlist_suite`**
- Population-based validation
- Rent index business rules
- Market classification validation
- Cross-reference validation
- Calculated metric validation

### Mart Models

**`mart_rent_trends_suite`**
- Cross-source data validation
- Market temperature classification
- Affordability category validation
- Investment scoring validation
- Data freshness checks

## 🔧 Integration with dbt

Great Expectations integrates seamlessly with the dbt pipeline:

1. **After dbt staging**: Run `staging_data_quality_checkpoint`
2. **After dbt core**: Run `core_data_quality_checkpoint`
3. **After dbt marts**: Run mart-specific validations

### Example Integration in dbt

```yaml
# In dbt_project.yml
post-hook: "{{ run_great_expectations_validation() }}"
```

## 🎛️ Checkpoints

### Staging Checkpoint
- Validates all staging models after dbt run
- Ensures data quality before core processing
- Fails fast if critical issues found

### Core Checkpoint
- Validates fact tables and dimensions
- Checks referential integrity
- Validates calculated measures

### Custom Checkpoints
Create additional checkpoints for:
- Incremental validation
- Source-specific validation
- Business rule validation

## 📈 Data Quality Metrics

The suite tracks:
- **Row counts**: Ensure expected data volume
- **Completeness**: Non-null critical fields
- **Validity**: Value ranges and formats
- **Uniqueness**: Primary/business key constraints
- **Consistency**: Cross-table relationships
- **Accuracy**: Business rule compliance
- **Timeliness**: Data freshness checks

## 🚨 Alerting and Monitoring

Configure notifications for validation failures:

```yaml
# In checkpoint YAML
action_list:
  - name: send_slack_notification
    action:
      class_name: SlackNotificationAction
      slack_webhook: ${SLACK_WEBHOOK}
      notify_on: failure
```

## 📋 Validation Reports

Access detailed reports:
- **HTML Reports**: `uncommitted/data_docs/local_site/index.html`
- **JSON Results**: `uncommitted/validations/`
- **Python Script**: Returns structured validation results

## 🔄 CI/CD Integration

Integrate with GitHub Actions:

```yaml
- name: Run Data Quality Validation
  run: |
    cd great_expectations
    python validate_data_quality.py --layer all --fail-fast
```

## 🛠️ Custom Expectations

Create custom expectations for business-specific rules:

```python
# Custom expectation example
class ExpectRentGrowthToBeReasonable(ColumnMapExpectation):
    # Implementation for Tampa-specific rent growth validation
```

## 📚 Best Practices

1. **Layer-specific validation**: Different standards for raw vs. marts
2. **Incremental validation**: Only validate new/changed data
3. **Business rule focus**: Validate what matters to stakeholders
4. **Performance optimization**: Use sampling for large datasets
5. **Version control**: All expectation suites in Git
6. **Documentation**: Clear descriptions for all expectations

## 🔧 Troubleshooting

**Connection Issues**:
- Verify Snowflake credentials
- Check network connectivity
- Validate warehouse permissions

**Validation Failures**:
- Review data docs for detailed results
- Check logs for specific error messages
- Validate upstream data sources

**Performance Issues**:
- Use sampling for large datasets
- Optimize SQL queries in batch requests
- Consider parallel execution for independent validations

## 🔗 Integration Points

- **dbt**: Post-hook validation
- **Dagster**: Asset checks integration
- **Snowflake**: Direct database validation
- **CI/CD**: GitHub Actions integration
- **Monitoring**: Slack/email notifications
- **Documentation**: Automated report generation