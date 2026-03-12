import camelot
from typing import List, Dict
import json

class TableExtractor:
    """Stage 4: Table extraction using Camelot"""
    
    @staticmethod
    def extract_tables(pdf_path: str) -> Dict:
        """
        Extract tables from PDF using Camelot
        
        Returns:
        {
            "tables_found": count,
            "tables": [
                {
                    "table_num": index,
                    "rows": num_rows,
                    "cols": num_cols,
                    "data": [rows],
                    "confidence": score
                }
            ]
        }
        """
        try:
            tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
            
            extracted_tables = []
            for idx, table in enumerate(tables):
                df = table.df
                
                extracted_tables.append({
                    "table_num": idx + 1,
                    "rows": len(df),
                    "cols": len(df.columns),
                    "data": df.values.tolist(),
                    "headers": df.columns.tolist(),
                    "confidence": table.accuracy if hasattr(table, 'accuracy') else 0
                })
            
            return {
                "tables_found": len(extracted_tables),
                "tables": extracted_tables
            }
        except Exception as e:
            return {
                "tables_found": 0,
                "tables": [],
                "error": str(e)
            }
    
    @staticmethod
    def extract_tables_as_json(pdf_path: str, table_nums: List[int] = None) -> List[Dict]:
        """
        Extract specific tables and return as structured JSON
        
        Args:
            pdf_path: Path to PDF file
            table_nums: List of table numbers to extract (1-indexed)
        
        Returns:
            List of extracted tables in JSON format
        """
        try:
            tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
            
            extracted = []
            for idx, table in enumerate(tables):
                if table_nums and (idx + 1) not in table_nums:
                    continue
                
                df = table.df
                
                # Convert to list of dictionaries
                records = df.to_dict('records')
                
                extracted.append({
                    "table_index": idx + 1,
                    "records": records,
                    "metadata": {
                        "rows": len(df),
                        "cols": len(df.columns),
                        "confidence": table.accuracy if hasattr(table, 'accuracy') else 0
                    }
                })
            
            return extracted
        except Exception as e:
            return [{
                "error": str(e),
                "tables_extracted": 0
            }]
