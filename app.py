from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory, flash
from mysql.connector import Error
from config import *  # Certifique-se de que config.py está no mesmo diretório
from db_functions import * # Certifique-se de que db_functions.py está no mesmo diretório
import os
import re
import logging
import shutil  # Importe shutil para remoção de arquivos/diretórios

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) # Cria a pasta se não existir

def limpar_input(campo):
    campo_formatado = campo.replace(".","").replace("/","").replace("-","").replace(",","").replace("(","").replace(")","").replace(" ","")
    return campo_formatado


@app.route('/download/<filename>')
def download_curriculo(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        try:
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
        except Exception as e:
            return f"Erro ao baixar o arquivo: {e}", 500
    else:
        return "Arquivo não encontrado.", 404

# Rota da pagina inicial 
@app.route('/')
def index():
    if session:
        if 'adm' in session:
            login = 'adm'
        else:
            login = 'empresa'
    else:
        login = False

    try:
        comandoSQL = '''
        SELECT vaga.*, empresa.nome_empresa 
        FROM vaga 
        JOIN empresa ON vaga.id_empresa = empresa.id_empresa
        WHERE vaga.status = 'ativa'
        ORDER BY vaga.id_vaga DESC;
        '''
        conexao, cursor = conectar_db()
        cursor.execute(comandoSQL)
        vagas = cursor.fetchall()
        return render_template('index.html', vagas=vagas, login=login)
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)
    return render_template('index.html')

# Rota da pagina login (GET e o POST)
@app.route('/login', methods = ['GET','POST'])
def login():
    if session:
        if 'adm' in session:
            return redirect('/adm')
        else:
            return redirect('/empresa')

    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        if not email or not senha:  # Corrigi aqui para verificar ambos os campos corretamente
            erro = "Os campos precisam estar preenchidos!"
            return render_template('login.html', msg_erro=erro)

        if email == MASTER_EMAIL and senha == MASTER_PASSWORD:
            session['adm'] = True
            return redirect('/adm')

        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'SELECT * FROM empresa WHERE email = %s AND senha = %s'
            cursor.execute(comandoSQL, (email, senha))
            empresa = cursor.fetchone()

            if not empresa:
                return render_template('login.html', msgerro='E-mail e/ou senha estão errados!')

            # Acessar os dados como dicionário
            if empresa['status'] == 'inativa':
                return render_template('login.html', msgerro='Empresa desativada! Procure o administrador!')

            session['id_empresa'] = empresa['id_empresa']
            session['nome_empresa'] = empresa['nome_empresa']
            return redirect('/empresa')
        
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

# Rota do ADM
@app.route('/adm')
def adm():
    if not session:
        return redirect('/login')

    if not 'adm' in session:
        return redirect('/login')
    
    
    try:
        conexao, cursor = conectar_db()
        comandoSQL = "SELECT * FROM empresa WHERE status = 'ativa'"
        cursor.execute(comandoSQL)
        empresas_ativas = cursor.fetchall()

        comandoSQL = "SELECT * FROM empresa WHERE status = 'inativa'"
        cursor.execute(comandoSQL)
        empresas_inativas = cursor.fetchall()

        return render_template('adm.html', empresas_ativas=empresas_ativas, empresas_inativas= empresas_inativas)
    except Error as erro:
        return f"Erro da BD: {erro}"
    except Exception as erro:
        return f"Erro de BackEnd: {erro}"
    finally:
        encerrar_db(cursor, conexao)

#ROTA PARA ABRIR E RECEBER AS INFORMAÇÕES DE UMA NOVA EMPRESA
@app.route('/cadastrar_empresa', methods=['POST','GET'])
def cadastrar_empresa():
    #Verificar se tem uma sessão
    if not session:
        return redirect('/login')
    #Se não for ADM deve ser empresa
    if not 'adm' in session:
        return redirect('/empresa')
    #Acesso ao formulario de cadastro
    if request.method == 'GET':
        return render_template('cadastrar_empresa.html')

    #Acesso ao formulario de cadastro
    if request.method == 'POST':
        nome_empresa = request.form['nome_empresa']
        cnpj = limpar_input(request.form['cnpj'])
        telefone = limpar_input(request.form['telefone'])
        email = request.form['email']
        senha = request.form['senha']

        #Verificar se todos os campos estão preenchidos
        if not nome_empresa or not cnpj or not telefone or not email or not senha:
            return render_template('cadastrar_empresa.html', msg_erro='Todos os campos são obrigatórios.')

        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'INSERT INTO empresa (nome_empresa,cnpj,telefone,email,senha) VALUES (%s,%s,%s,%s,%s)'
            cursor.execute(comandoSQL, (nome_empresa,cnpj,telefone,email,senha))
            conexao.commit() #Para comandos DML
            return redirect('/adm')
        except Error as erro:
            conexao.rollback()
            if erro.errno == 1062:
                return render_template('cadastrar_empresa.html', msg_erro='Esse email já existe.')
            else:
                return f"Erro de BD: {erro}"
        except Exception as erro:
            return f"Erro de BackEnd: {erro}"
        finally:
            encerrar_db(cursor, conexao)

@app.route('/editar_empresa/<int:id_empresa>', methods=['GET','POST'])
def editar_empresa(id_empresa):
    #Verificar se tem uma sessão
    if not session:
        return redirect('/login')
    #Se não for ADM deve ser empresa
    if not session['adm']:
        return redirect('/login')

    if request.method == 'GET':
        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'SELECT * FROM empresa WHERE id_empresa = %s'
            cursor.execute(comandoSQL, (id_empresa,))
            empresa = cursor.fetchone()
            return render_template('editar_empresa.html', empresa=empresa)
        except Error as erro:
            conexao.rollback()
            return f"Erro de BD: {erro}"
        except Exception as erro:
            return f"Erro de BackEnd: {erro}"
        finally:
            encerrar_db(cursor, conexao)

        if request.method == "GET":
            return render_template('cadastrar_empresa.html')
            
    #Acesso ao formulario de cadastro
    if request.method == 'POST':
        nome_empresa = request.form['nome_empresa']
        cnpj = request.form['cnpj']
        telefone = request.form['telefone']
        email = request.form['email']
        senha = request.form['senha']

        #Verificar se todos os campos estão preenchidos
        if not nome_empresa or not cnpj or not telefone or not email or not senha:
            return render_template('editar_empresa', msg_erro='Todos os campos são obrigatórios.')

        try:
            conexao, cursor = conectar_db()
            comandoSQL = '''
            UPDATE empresa
            SET nome_empresa=%s, cnpj=%s, telefone=%s, email=%s, senha=%s
            WHERE id_empresa=%s;
            '''
            cursor.execute(comandoSQL, (nome_empresa,cnpj,telefone,email,senha, id_empresa))
            conexao.commit() #Para comandos DML
            return redirect('/adm')
        except Error as erro:
            if erro.errno == 1062:
                return render_template('editar_empresa.html', msg_erro='Esse email já existe.')
            else:
                return f"Erro de BD: {erro}"
        except Exception as erro:
            return f"Erro de BackEnd: {erro}"
        finally:
            encerrar_db(cursor, conexao)

@app.route('/status_empresa/<int:id_empresa>')
def status_empresa(id_empresa):
    #Verificar se tem uma sessão
    if not session:
        return redirect('/login')
    #Se não for ADM deve ser empresa
    if not session['adm']:
        return redirect('/login')

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT status FROM empresa WHERE id_empresa = %s'
        cursor.execute(comandoSQL, (id_empresa,))
        status_empresa = cursor.fetchone()
        
        if status_empresa['status'] == 'ativa':
            novo_status = 'inativa'
        else:
            novo_status = 'ativa'

        comandoSQL = 'UPDATE empresa SET status=%s WHERE id_empresa = %s'
        cursor.execute(comandoSQL, (novo_status, id_empresa))
        conexao.commit()
        #Se a empresa estiver sendo desativada, as vagas também serão
        if novo_status == 'inativa':
            comandoSQL = 'UPDATE vaga SET status = %s WHERE id_empresa = %s'
            cursor.execute(comandoSQL, (novo_status, id_empresa))
            conexao.commit()
        return redirect('/adm')
    except Error as erro:
        return f"Erro de BD: {erro}"
    except Exception as erro:
        return f"Erro de BackEnd: {erro}"
    finally:
        encerrar_db(cursor, conexao)

@app.route('/excluir_empresa/<int:id_empresa>', methods=['POST'])
def excluir_empresa(id_empresa):
    if not session or not session.get('adm'):
        return redirect(url_for('login'))

    try:
        conexao, cursor = conectar_db()

        # 1. Delete candidates associated with the company's vacancies.
        comandoSQL = "DELETE FROM candidato WHERE id_vaga IN (SELECT id_vaga FROM vaga WHERE id_empresa = %s)"
        cursor.execute(comandoSQL, (id_empresa,))
        conexao.commit()

        # 2. Delete vacancies associated with the company.
        comandoSQL = "DELETE FROM vaga WHERE id_empresa = %s"
        cursor.execute(comandoSQL, (id_empresa,))
        conexao.commit()

        # 3. Delete the company.
        comandoSQL = "DELETE FROM empresa WHERE id_empresa = %s"
        cursor.execute(comandoSQL, (id_empresa,))
        conexao.commit()
        flash("Empresa e dados relacionados excluídos com sucesso!", "success")
        return redirect(url_for('adm'))

    except mysql.connector.Error as e:
        conexao.rollback()
        logging.exception(f"Erro de banco de dados ao excluir empresa: {e}")
        flash("Erro ao excluir empresa. Tente novamente mais tarde.", "error")
        return redirect(url_for('adm'))

    except Exception as e:
        logging.exception(f"Erro inesperado ao excluir empresa: {e}")
        flash("Erro inesperado. Por favor, contate o administrador.", "error")
        return redirect(url_for('adm'))

    finally:
        encerrar_db(cursor, conexao)

@app.route('/empresa')
def empresa():
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    id_empresa = session['id_empresa']
    nome_empresa = session['nome_empresa']

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT * FROM vaga WHERE id_empresa = %s AND status = "ativa" ORDER BY id_vaga DESC'
        cursor.execute(comandoSQL, (id_empresa,))
        vagas_ativas = cursor.fetchall()

        comandoSQL = 'SELECT * FROM vaga WHERE id_empresa = %s AND status = "inativa" ORDER BY id_vaga DESC'
        cursor.execute(comandoSQL, (id_empresa,))
        vagas_inativas = cursor.fetchall()

        return render_template('empresa.html', nome_empresa=nome_empresa, vagas_ativas=vagas_ativas, vagas_inativas=vagas_inativas)         
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)  

# Rota de logout (Encerra sessões)
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/cadastrar_vaga', methods=['POST','GET'])
def cadastrar_vaga():
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')
    
    if request.method == 'GET':
        return render_template('cadastrar_vaga.html')
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        formato = request.form['formato']
        tipo = request.form['tipo']
        local = ''
        local = request.form['local']
        salario = ''
        salario = request.form['salario']
        id_empresa = session['id_empresa']

        if not titulo or not descricao or not formato or not tipo:
            return render_template('cadastrar_vaga.html', msg_erro="Os campos obrigatório precisam estar preenchidos!")
        
        try:
            conexao, cursor = conectar_db()
            comandoSQL = '''
            INSERT INTO Vaga (titulo, descricao, formato, tipo, local, salario, id_empresa)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(comandoSQL, (titulo, descricao, formato, tipo, local, salario, id_empresa))
            conexao.commit()
            return redirect('/empresa')
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)
#ROTA PARA VER DETALHES DA VAGA
@app.route('/sobre_vaga/<int:id_vaga>')
def sobre_vaga(id_vaga):
    try:
        comandoSQL = '''
        SELECT vaga.*, empresa.nome_empresa 
        FROM vaga 
        JOIN empresa ON vaga.id_empresa = empresa.id_empresa 
        WHERE vaga.id_vaga = %s;
        '''
        conexao, cursor = conectar_db()
        cursor.execute(comandoSQL, (id_vaga,))
        vaga = cursor.fetchone()
        
        if not vaga:
            return redirect('/')
        
        return render_template('sobre_vaga.html', vaga=vaga)
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)     

#ROTA PARA ALTERAR O STATUS DA VAGA
@app.route("/status_vaga/<int:id_vaga>")
def statusvaga(id_vaga):
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT status FROM vaga WHERE id_vaga = %s;'
        cursor.execute(comandoSQL, (id_vaga,))
        vaga = cursor.fetchone()
        if vaga['status'] == 'ativa':
            status = 'inativa'
        else:
            status = 'ativa'

        comandoSQL = 'UPDATE vaga SET status = %s WHERE id_vaga = %s'
        cursor.execute(comandoSQL, (status, id_vaga))
        conexao.commit()
        return redirect('/empresa')
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)


#ROTA PARA EDITAR A VAGA
@app.route('/editar_vaga/<int:id_vaga>', methods=['GET','POST'])
def editar_vaga(id_vaga):
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    if request.method == 'GET':
        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'SELECT * FROM vaga WHERE id_vaga = %s;'
            cursor.execute(comandoSQL, (id_vaga,))
            vaga = cursor.fetchone()
            return render_template('editar_vaga.html', vaga=vaga)
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        formato = request.form['formato']
        tipo = request.form['tipo']
        local = request.form['local']
        salario = request.form['salario']

        if not titulo or not descricao or not formato or not tipo:
            return redirect('/empresa')
        
        try:
            conexao, cursor = conectar_db()
            comandoSQL = '''
            UPDATE vaga SET titulo=%s, descricao=%s, formato=%s, tipo=%s, local=%s, salario=%s
            WHERE id_vaga = %s;
            '''
            cursor.execute(comandoSQL, (titulo, descricao, formato, tipo, local, salario, id_vaga))
            conexao.commit()
            return redirect('/empresa')
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

#ROTA PARA EXCLUIR VAGA
app.logger.setLevel(logging.DEBUG) # Define o nível de log para DEBUG para saída detalhada

@app.route('/excluir_vaga/<int:id_vaga>')
def excluir_vaga(id_vaga):
    app.logger.debug(f"Tentando excluir vaga com id: {id_vaga}")  # Log extra
    if not session or not session.get('adm'):
        app.logger.warning("Usuário não logado como administrador.")
        return redirect(url_for('login'))

    try:
        conexao, cursor = conectar_db()
        comandoSQL = "DELETE FROM vaga WHERE id_vaga = %s"
        app.logger.debug(f"Executando SQL: {comandoSQL}, Parâmetros: ({id_vaga})")
        cursor.execute(comandoSQL, (id_vaga,))
        linhas_afetadas = cursor.rowcount
        conexao.commit()
        app.logger.debug(f"Linhas afetadas: {linhas_afetadas}")
        if linhas_afetadas > 0:
            app.logger.info(f"Vaga com id {id_vaga} excluída com sucesso.")
            flash("Vaga excluída com sucesso!", "success")
        else:
            app.logger.warning(f"Nenhuma linha afetada ao excluir vaga com id {id_vaga}.")
            flash("Vaga não encontrada ou erro ao excluir.", "warning")
        return redirect(url_for('adm'))

    except mysql.connector.Error as e:
        app.logger.exception(f"Erro de banco de dados ao excluir vaga: {e}")
        flash(f"Erro ao excluir vaga: {e}", "error")  # Careful in production!
        return redirect(url_for('adm'))

    except Exception as e:
        app.logger.exception(f"Erro inesperado ao excluir vaga: {e}")
        flash("Erro inesperado. Contate o administrador.", "error")
        return redirect(url_for('adm'))

    finally:
        encerrar_db(cursor, conexao)



@app.route('/pesquisa', methods=['GET'])
def pesquisar():
    palavra_chave = request.args.get('q', '')
    try:
        conexao, cursor = conectar_db()
        comandoSQL = '''
        SELECT vaga.*, empresa.nome_empresa
        FROM vaga
        JOIN empresa ON vaga.id_empresa = empresa.id_empresa
        WHERE vaga.status = 'ativa' AND (
            vaga.titulo LIKE %s OR
            vaga.descricao LIKE %s
        )
        '''
        cursor.execute(comandoSQL, (f'%{palavra_chave}%', f'%{palavra_chave}%'))
        vagas = cursor.fetchall()
        return render_template('palavra_chave.html', vagas=vagas, palavra_chave=palavra_chave)
    except Error as erro:
        return f"ERRO! {erro}"
    finally:
        encerrar_db(cursor, conexao)

@app.route('/candidatar/<int:id_vaga>', methods=['POST', 'GET'])
def candidatar(id_vaga):
    if request.method == 'GET':
        return render_template('candidatar.html', id_vaga=id_vaga)

    if request.method == 'POST':
        nome_candidato = request.form.get('nome_candidato')
        email = request.form.get('email')
        telefone = limpar_input(request.form.get('telefone'))
        curriculo = request.files.get('curriculo')

        # Validação
        if not all([nome_candidato, email, telefone, curriculo, curriculo.filename]):
            return render_template('candidatar.html', id_vaga=id_vaga, msg_erro="Todos os campos são obrigatórios.")

        allowed_extensions = {'pdf', 'doc', 'docx'}
        if not curriculo.filename.lower().endswith(tuple(allowed_extensions)):
            return render_template('candidatar.html', id_vaga=id_vaga, msg_erro="Formato de arquivo inválido. Apenas PDF, DOC e DOCX são permitidos.")


        mydb = None
        cursor = None
        try:
            mydb, cursor = conectar_db()
            if mydb is None:
                return "Erro crítico: Não foi possível conectar ao banco de dados."

            # nome_arquivo = secure_filename(curriculo.filename)
            nome_arquivo = f"{nome_candidato}_{id_vaga}_{curriculo.filename}" #para evitar sobreposição de nomes
            caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
            curriculo.save(caminho_arquivo)

            comandoSQL = "INSERT INTO candidato (nome_candidato, email, telefone, curriculo, id_vaga) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(comandoSQL, (nome_candidato, email, telefone, nome_arquivo, id_vaga))
            mydb.commit()
            return redirect(url_for('sobre_vaga', id_vaga=id_vaga))

        except mysql.connector.Error as e:
            print(f"Erro de banco de dados: {e}")
            return render_template('candidatar.html', id_vaga=id_vaga, msg_erro=f"Erro ao cadastrar candidatura: {e}")
        except Exception as e:
            print(f"Erro inesperado: {e}")
            return render_template('candidatar.html', id_vaga=id_vaga, msg_erro=f"Erro interno do servidor: {e}")
        finally:
            encerrar_db(cursor, mydb)

@app.route('/candidatos/<int:id_vaga>')
def candidatos(id_vaga):
    try:
        conexao, cursor = conectar_db()
        comandoSQL = '''
        SELECT * FROM candidato WHERE id_vaga = %s
        '''
        cursor.execute(comandoSQL, (id_vaga,))
        candidatos = cursor.fetchall()
        return render_template('candidatos.html', candidatos=candidatos, id_vaga=id_vaga)  # Passando id_vaga
    except mysql.connector.Error as erro:
        return f"Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"Erro de Back End! {erro}"
    finally:
        encerrar_db(cursor, conexao)


@app.route("/excluir_curriculo/<int:id_candidato>", methods=["POST"])
def excluir_curriculo(id_candidato):
    if not session:  # Verifica se há uma sessão ativa
        return redirect(url_for('login'))

    try:
        conexao, cursor = conectar_db()

        # 1. Busca informações do candidato
        comandoSQL = "SELECT curriculo FROM candidato WHERE id_candidato = %s"
        cursor.execute(comandoSQL, (id_candidato,))
        candidato = cursor.fetchone()

        if not candidato:
            flash("Candidato não encontrado.", "warning")
            return redirect(request.referrer)

        nome_curriculo = candidato["curriculo"]
        if not nome_curriculo:
            flash("Currículo não encontrado para este candidato.", "warning")
            return redirect(request.referrer)

        caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_curriculo)

        # 2. Exclui o arquivo
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
            logging.info(f"Arquivo '{nome_curriculo}' excluído com sucesso.")
            flash(f"Currículo excluído com sucesso!", "success")
        else:
            logging.warning(f"Arquivo '{nome_curriculo}' não encontrado para exclusão.")
            flash(f"Arquivo '{nome_curriculo}' não encontrado para exclusão.", "warning")

        #Exclui o registro do candidato do banco de dados (opcional)
        comandoSQL = "DELETE FROM candidato WHERE id_candidato = %s"
        cursor.execute(comandoSQL, (id_candidato,))
        conexao.commit()

        return redirect(request.referrer)

    except Error as e:
        conexao.rollback()  # Importante em caso de erro
        logging.exception(f"Erro de banco de dados ao excluir currículo: {e}")
        flash("Erro ao excluir currículo. Tente novamente mais tarde.", "error")
        return redirect(request.referrer)
    except Exception as e:
        logging.exception(f"Erro inesperado ao excluir currículo: {e}")
        flash("Erro inesperado. Por favor, contate o administrador.", "error")
        return redirect(request.referrer)
    finally:
        encerrar_db(cursor, conexao)




#FINAL DO CODIGO
if __name__ == '__main__':

    app.run(debug=True)
