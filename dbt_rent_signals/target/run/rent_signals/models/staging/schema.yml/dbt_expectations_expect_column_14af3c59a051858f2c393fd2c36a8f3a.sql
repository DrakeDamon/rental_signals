
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from RENTS.DBT_DEV_test_failures.dbt_expectations_expect_column_14af3c59a051858f2c393fd2c36a8f3a
    
      
    ) dbt_internal_test