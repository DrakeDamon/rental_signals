
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from RENTS.DBT_DEV_test_failures.dbt_expectations_expect_column_46b3aa6dcc44aa88e3c233bb6e8e6243
    
      
    ) dbt_internal_test