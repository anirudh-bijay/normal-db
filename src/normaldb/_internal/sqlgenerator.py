from typing import List, Dict, Any

class SQLGenerator:
    def __init__(
        self, relations: List[Dict[str, Any]],
        data_type_map:Dict[str, str] = None) -> str:
        """
        Generates the SQL queries to CREATE the tables, for the decomposed relations given by SchemaBuilder.
        
        Args:
            relations(List[Dict[str, Any]]) : a list of relations each with a 
                                                'attributes'(list of attributes) 
                                                'keys'(key corresponding to the relation)
        
        Returns: a SQL CREATE TABLE .. statement
        """
        if data_type_map is None:
            data_type_map = {}
            
        self.relations: List[Dict[str, Any]] = relations
        self.data_type_map: Dict[str, str] = data_type_map
    def generate(self) -> str:
        # build a primary key map for foreign key resolution
        # i.e. store the primary key to relation name mapping
        pk_map = {}
        for idx, rel in enumerate(self.relations):
            pk_attrs = rel['keys'][0]
            
            for pk_attr in pk_attrs:
                pk_map[pk_attr] = f"R{idx+1}"
        
        # store sql statements
        sql_statements = []
        for idx, relation in enumerate(self.relations):
            table_name = f"R{idx+1}"
            sql_stmt = f"CREATE TABLE {table_name} ( \n"
            # print(self.relations)
            # columns of table
            for attr in relation['attributes']:
                data_type = self.data_type_map.get(attr, "[data-type]")
                sql_stmt += f"  {attr} {data_type}, \n"
            
            # primary key
            pk = relation['keys'][0]
            sql_stmt += f"  PRIMARY KEY ({', '.join(pk)})"
            
            if len(relation['keys']) > 1:
                for i in range(1, len(relation['keys'])):
                    sql_stmt += f"\n  UNIQUE({', '.join(relation['keys'][i])})"
            
            # foreign keys
            for attr in relation['attributes']:
                if attr in pk_map and attr not in pk:
                    sql_stmt += f",\n  FOREIGN KEY ({attr}) REFERENCES {pk_map[attr]}({attr})"
                
            sql_stmt += "\n);"
            sql_statements.append(sql_stmt)
        
        # return the joined string
        print(sql_statements)
        return "\n\n".join(sql_statements)
        