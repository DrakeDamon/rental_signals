
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from RENTS.DBT_DEV_test_failures.dbt_expectations_expect_column_a1d9e25aa7b364722ac5b8e3520e20dc
    
      
    ) dbt_internal_test