import mysql.connector
from config import *

#estabelece conexão com o BD
def conectar_db():
    conexao = mysql.connector.connect(
        host = DB_HOST,
        user = DB_USER,
        password = DB_PASSWORD,
        database = DB_NAME
    )
    # Alterar a linha abaixo
    cursor = conexao.cursor(dictionary=True)
    return conexao, cursor

#Encerra a conexão com o BD
def encerrar_db(cursor, conexao):
    cursor.close()
    conexao.close()
