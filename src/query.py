import os
import json
import duckdb
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
import duckdb

load_dotenv()

model = "gpt-4o-mini"
client = OpenAI()

class QueryContext:
    def __init__(self, query: str):
        self.query = query
        self.result = None
        
    def query_csv(self) -> str:
        """Convert natural language query to SQL, execute it on Titanic.csv, and return results"""
        
        csv_path = "Titanic.csv"
        
        if not os.path.exists(csv_path):
            return f"Error: {csv_path} not found"
    
        # Schema of Titanic CSV for LLM context
        csv_schema = """Titanic.csv has the following columns:
        - PassengerId (int)
        - Survived (int: 0 or 1)
        - Pclass (int: 1, 2, or 3 - passenger class)
        - Name (string)
        - Sex (string: 'male' or 'female')
        - Age (float)
        - SibSp (int: number of siblings/spouses)
        - Parch (int: number of parents/children)
        - Ticket (string)
        - Fare (float)
        - Cabin (string)
        - Embarked (string: 'C', 'Q', or 'S')
        """
    
        # Use LLM to generate SQL query
        sql_generation_messages = [
            {"role": "user", "content": f"""Convert this natural language query into a SQL query for DuckDB.
            
CSV Schema:
{csv_schema}

Natural Language Query: {self.query}

Return ONLY the SQL query, nothing else. Use SELECT * or specific columns as appropriate.
Example: "Show me all female passengers who survived" → SELECT * FROM 'Titanic.csv' WHERE Sex = 'female' AND Survived = 1
"""}
        ]
    
        try:
            sql_response = client.chat.completions.create(
                model=model,
                messages=sql_generation_messages,
                temperature=0.2,
            )
            
            sql_query = sql_response.choices[0].message.content.strip()
            
            # Execute SQL query using DuckDB
            conn = duckdb.connect(":memory:")
            result = conn.execute(sql_query).fetchall()
            columns = [desc[0] for desc in conn.description]
            
            # Convert results to list of dicts
            result_list = [dict(zip(columns, row)) for row in result]
            
            conn.close()
            
            if not result_list:
                return f"No records found matching: {self.query}"
            
            return json.dumps(result_list, default=str)
        
        except Exception as e:
            return f"Error executing query: {str(e)}"
        