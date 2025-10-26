
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from RENTS.DBT_DEV_test_failures.dbt_expectations_expect_column_59d2f50cbc98e07c011188e7c398d8a8
    
      
    ) dbt_internal_test