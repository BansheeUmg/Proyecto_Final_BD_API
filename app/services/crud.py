"""SQL parametrizado; tablas y columnas solo provienen del registro interno."""
from fastapi import HTTPException
from app.database import rows

def list_records(db, table, offset, limit):
    return rows(db.cursor().execute(f'SELECT * FROM dbo.{table} ORDER BY id OFFSET ? ROWS FETCH NEXT ? ROWS ONLY', offset,limit))

def get_record(db, table, record_id):
    result=rows(db.cursor().execute(f'SELECT * FROM dbo.{table} WHERE id=?',record_id))
    if not result: raise HTTPException(404,'Registro no encontrado')
    return result[0]

def create_record(db, table, data):
    columns=','.join(data)
    placeholders=','.join('?' for _ in data)
    cursor=db.cursor().execute(f'INSERT dbo.{table} ({columns}) OUTPUT INSERTED.* VALUES ({placeholders})',*data.values())
    return rows(cursor)[0]

def update_record(db, table, record_id, data):
    assignments=','.join(f'{key}=?' for key in data)
    result=rows(db.cursor().execute(f'UPDATE dbo.{table} SET {assignments} OUTPUT INSERTED.* WHERE id=?',*data.values(),record_id))
    if not result: raise HTTPException(404,'Registro no encontrado')
    return result[0]

def delete_record(db, table, record_id):
    cursor=db.cursor().execute(f'DELETE FROM dbo.{table} OUTPUT DELETED.id WHERE id=?',record_id)
    if cursor.fetchone() is None: raise HTTPException(404,'Registro no encontrado')
