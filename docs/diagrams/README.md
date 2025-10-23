# Tampa Rent Signals - Architecture Diagrams

This directory contains comprehensive Mermaid diagrams documenting the Tampa Rent Signals project architecture, database schema, and system designs.

## 📋 Available Diagrams

### 1. **Database Schema** (`database_schema.mmd`)
Complete star schema design showing:
- **Dimensions**: Time, Location (SCD Type 2), Economic Series (SCD Type 2), Data Source
- **Facts**: Rent ZORI, Rent ApartmentList, Economic Indicators
- **Marts**: Business-ready analytics tables
- **Snapshots**: SCD Type 2 historical tracking tables
- **Relationships**: Primary/foreign key relationships and data lineage

### 2. **Dagster Orchestration Architecture** (`dagster_architecture.mmd`)
Software-defined assets and orchestration:
- **15 Assets**: Staging, core, and mart layer assets
- **12 Asset Checks**: Quality, freshness, and business rule validation
- **4 Pipeline Jobs**: Staging, core, marts, and full refresh
- **Automation**: Schedules, sensors, and event-driven triggers
- **Dependencies**: Asset lineage and execution flow

### 3. **Complete System Architecture** (`system_architecture.mmd`)
End-to-end system design:
- **Data Sources**: External APIs and data providers
- **Processing**: ETL scripts and data transformation
- **Storage**: Local development and cloud infrastructure
- **Analytics**: dbt models and Great Expectations validation
- **Orchestration**: Dagster asset management
- **Monitoring**: Observability and business intelligence tools

### 4. **Data Quality Framework** (`data_quality_framework.mmd`)
Comprehensive data validation approach:
- **Layer-specific Validation**: Bronze, silver, and gold quality standards
- **Great Expectations Integration**: 100+ validation rules
- **Dagster Asset Checks**: Real-time quality monitoring
- **Quality Gates**: Blocking vs. warning validation
- **Monitoring**: Quality dashboards and alerting

### 5. **Deployment Architecture** (`deployment_architecture.mmd`)
Production deployment and infrastructure:
- **Development Workflow**: Local development and CI/CD
- **Cloud Infrastructure**: AWS and Snowflake production setup
- **Container Orchestration**: Kubernetes and Dagster deployment
- **Monitoring**: Application and infrastructure observability
- **Security**: Access control and compliance monitoring

## 🔧 Viewing the Diagrams

### Online Viewers
- **Mermaid Live Editor**: https://mermaid.live/
- **GitHub**: Diagrams render automatically in GitHub's web interface
- **VS Code**: Use the "Mermaid Preview" extension

### Local Rendering
```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Render diagram to PNG
mmdc -i database_schema.mmd -o database_schema.png

# Render diagram to SVG  
mmdc -i dagster_architecture.mmd -o dagster_architecture.svg
```

### Integration with Documentation
These diagrams can be embedded in:
- **README files**: Link or embed rendered images
- **dbt docs**: Include in model descriptions
- **Confluence/Wiki**: Import for team documentation
- **Presentations**: Export as images for stakeholder communication

## 📊 Diagram Usage

### For Developers
- **Database Schema**: Understand table relationships and SCD Type 2 implementation
- **Dagster Architecture**: Navigate asset dependencies and pipeline structure
- **System Architecture**: Comprehend end-to-end data flow and tool integration

### For Stakeholders
- **System Architecture**: High-level understanding of the data platform
- **Deployment Architecture**: Infrastructure and operational overview
- **Data Quality Framework**: Confidence in data reliability and governance

### For Data Engineers
- **All Diagrams**: Complete technical reference for system maintenance and enhancement
- **Database Schema**: Query optimization and performance tuning
- **Data Quality Framework**: Validation rule management and monitoring

## 🔄 Maintenance

These diagrams should be updated when:
- New data sources are added
- Database schema changes occur
- Pipeline architecture evolves
- Deployment infrastructure changes
- Data quality rules are modified

**Responsibility**: Data engineering team should maintain diagram accuracy as part of standard development workflow.

## 📚 Related Documentation

- **Main README**: `/README.md` - Project overview and quick start
- **CLAUDE.md**: `/CLAUDE.md` - Development workflow and commands  
- **dbt Documentation**: `dbt_rent_signals/` - Model-specific details
- **Great Expectations**: `great_expectations/README.md` - Data quality documentation
- **Dagster Documentation**: `dagster_rent_signals/README.md` - Orchestration setup

## 🎯 Architecture Principles

These diagrams reflect the following architectural principles:
- **Modularity**: Clear separation of concerns across layers
- **Observability**: Comprehensive monitoring at every stage
- **Quality**: Data validation integrated throughout the pipeline
- **Scalability**: Cloud-native, container-based deployment
- **Maintainability**: Version-controlled, well-documented infrastructure