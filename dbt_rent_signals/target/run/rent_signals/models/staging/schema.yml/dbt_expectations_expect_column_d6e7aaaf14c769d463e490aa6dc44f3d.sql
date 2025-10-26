
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from RENTS.DBT_DEV_test_failures.dbt_expectations_expect_column_d6e7aaaf14c769d463e490aa6dc44f3d
    
      
    ) dbt_internal_test