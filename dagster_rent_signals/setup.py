from setuptools import find_packages, setup

setup(
    name="dagster-rent-signals",
    version="1.0.0",
    description="Dagster orchestration for Tampa Rent Signals data pipeline",
    packages=find_packages(exclude=["dagster_rent_signals_tests"]),
    install_requires=[
        "dagster[webserver,postgres]>=1.5.0",
        "dagster-dbt>=0.21.0", 
        "dagster-snowflake>=0.21.0",
        "dagster-great-expectations>=0.1.0",
        "dbt-core>=1.6.0",
        "dbt-snowflake>=1.6.0",
        "great-expectations[snowflake]>=0.17.0",
        "pandas>=1.5.0",
        "sqlalchemy-snowflake>=1.4.7",
        "snowflake-connector-python>=3.3.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0", 
            "black>=22.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
        ]
    },
)