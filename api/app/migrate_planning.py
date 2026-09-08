"""Run explicitly against an existing ECI database; never reset data."""
import os
from pathlib import Path
from sqlalchemy import create_engine, text

def main():
    engine=create_engine(os.environ['DATABASE_URL'])
    sql=Path('/migrations/005_pi_planning.sql').read_text()
    with engine.begin() as connection:
        for statement in sql.split(';'):
            if statement.strip(): connection.execute(text(statement))
    print('PI planning schema ready.')

if __name__ == '__main__': main()
