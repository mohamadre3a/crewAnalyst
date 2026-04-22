import json
import pandas as pd
import numpy as np
from typing import Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool



class CSVPathInput(BaseModel):
    """Input schema for tools that only need the CSV file path."""
    address: str = Field(..., description="address of the csv file to load.")
    
class CSVDataOutput(BaseModel):
    """Output schema for tools that return a DataFrame characterstics: row count, column count, column names and dtypes."""
    row_count: int = Field(..., description="Number of rows in the DataFrame.")
    column_count: int = Field(..., description="Number of columns in the DataFrame.")
    column_names: list = Field(..., description="List of column names in the DataFrame.")
    column_dtypes: dict = Field(..., description="Dictionary mapping column names to their data types.")
    

class CSVSummaryTool(BaseTool):
    name: str = "CSV Summary Tool"
    description: str = (
        "This tool takes the path to a CSV file, loads it into a DataFrame, and returns a summary of the data including row count, column count, column names, and data types."
    )
    args_schema: Type[BaseModel] = CSVPathInput

    def _run(self, address: str) -> CSVDataOutput:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(address)
        
        # Create the output schema instance with the required information
        output = CSVDataOutput(
            row_count=df.shape[0],
            column_count=df.shape[1],
            column_names=df.columns.tolist(),
            column_dtypes=df.dtypes.apply(lambda x: str(x)).to_dict()
        )
        
        return output.model_dump_json()
    
    




