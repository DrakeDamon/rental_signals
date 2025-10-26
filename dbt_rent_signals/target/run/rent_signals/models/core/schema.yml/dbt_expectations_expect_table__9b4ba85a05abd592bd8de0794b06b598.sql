
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
        select *
        from RENTS.DBT_DEV_test_failures.dbt_expectations_expect_table__9b4ba85a05abd592bd8de0794b06b598
    
      
    ) dbt_internal_test