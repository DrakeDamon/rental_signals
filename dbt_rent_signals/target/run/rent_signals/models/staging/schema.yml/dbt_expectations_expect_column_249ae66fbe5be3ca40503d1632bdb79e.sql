
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from RENTS.DBT_DEV_test_failures.dbt_expectations_expect_column_249ae66fbe5be3ca40503d1632bdb79e
    
      
    ) dbt_internal_test