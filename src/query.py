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
        """Convert natural language query to SQL, execute it on the active CSV dataset, and return results"""
        
        # Resolve csv path: check root first, then workspace/data/
        csv_path = "Titanic.csv"
        if not os.path.exists(csv_path):
            csv_path = os.path.join("workspace", "data", "Titanic.csv")
            
        if not os.path.exists(csv_path):
            return f"Error: Active database CSV file not found."
    
        # Auto-detect CSV schema using DuckDB
        try:
            conn = duckdb.connect(":memory:")
            # PRAGMA table_info lists the columns: (cid, name, type, notnull, dflt_value, pk)
            columns_info = conn.execute(f"PRAGMA table_info('{csv_path}')").fetchall()
            conn.close()
            
            if not columns_info:
                return "Error: Could not retrieve column schema from CSV."
                
            schema_lines = []
            for col in columns_info:
                schema_lines.append(f"        - {col[1]} ({col[2]})")
            
            detected_schema = "\n".join(schema_lines)
            csv_name = os.path.basename(csv_path)
            
            csv_schema = f"The dataset '{csv_name}' has the following columns and data types:\n{detected_schema}"
        except Exception as e:
            return f"Error analyzing CSV schema: {str(e)}"
    
        # Use LLM to generate SQL query based on the auto-detected schema
        sql_generation_messages = [
            {"role": "user", "content": f"""Convert this natural language query into a SQL query for DuckDB.
            
CSV Schema:
{csv_schema}

Natural Language Query: {self.query}

Return ONLY the executable SQL query, nothing else. Do not use markdown blocks. Use the table name '{csv_path}' in your SQL statement.
Example: "Show all passengers who survived" → SELECT * FROM '{csv_path}' WHERE Survived = 1
"""}
        ]
    
        try:
            sql_response = client.chat.completions.create(
                model=model,
                messages=sql_generation_messages,
                temperature=0.2,
            )
            
            sql_query = sql_response.choices[0].message.content.strip()
            # Remove any markdown formatting code blocks if LLM outputted them
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            
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
        