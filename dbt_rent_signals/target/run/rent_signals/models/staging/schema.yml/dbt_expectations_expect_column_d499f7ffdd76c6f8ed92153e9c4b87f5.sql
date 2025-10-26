
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from RENTS.DBT_DEV_test_failures.dbt_expectations_expect_column_d499f7ffdd76c6f8ed92153e9c4b87f5
    
      
    ) dbt_internal_test