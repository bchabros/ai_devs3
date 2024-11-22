INITIAL_PROMPT = """
You need to find IDs of active datacenters that are managed by managers who are currently on vacation (inactive).

Available commands:
1. show tables - to list all tables
2. show create table <table_name> - to show table structure
3. regular SELECT statements

What would be your next step to gather the necessary information? 
Remember to format your response with:
QUERY: (your SQL query)
REASONING: (your explanation)
IS_FINAL: (true/false)
"""
