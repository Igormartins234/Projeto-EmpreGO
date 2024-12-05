ambiente = 'desenvolvimento'

if ambiente == 'desenvolvimento':
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = 'senai'
    DB_NAME = 'emprego'

#CONFIG CHAVE SECRETA
SECRET_KEY = 'emprego'

MASTER_EMAIL = 'adm@adm'
MASTER_PASSWORD = 'adm'


UPLOAD_FOLDER = 'uploads' # ou o caminho completo para a pasta uploads