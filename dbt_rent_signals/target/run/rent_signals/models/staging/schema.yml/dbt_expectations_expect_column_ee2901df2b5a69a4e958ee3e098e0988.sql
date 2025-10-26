
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from RENTS.DBT_DEV_test_failures.dbt_expectations_expect_column_ee2901df2b5a69a4e958ee3e098e0988
    
      
    ) dbt_internal_test