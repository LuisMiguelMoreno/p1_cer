from flask import Flask, render_template, request, session
import re, requests
from elasticsearch import Elasticsearch
from beebotte import *
import time
from datetime import datetime
from threading import *
import statistics
from apscheduler.schedulers.background import BackgroundScheduler
import webbrowser
import logging

# Inicializacion de variables globales
indice_escritura = 0
indice_escritura_usuarios = 0
indice_lectura = 0
numero = 0
email = ""
username = ""
password = ""
username_activo = ""
usuario_logeado = False
media_bbt = 0
media_es = 0

# Definiciones Beebotte
my_token = 'token_WBkKXcrLIveYggP5'
my_hostname = 'api.beebotte.com'
canal_bbt = 'test'
resource_bbt = 'cer'
Dashboard_URL = 'https://beebotte.com/dash/72ec13d0-37e7-11ec-954b-39d34f82886a?shareid=shareid_JpbdUABsc1d0AF5k'
bbt = BBT(token = my_token, hostname= my_hostname)


# Definiciones Elasticsearch
es = Elasticsearch([{'host' : 'localhost', 'port': 9200}])
tabla = "tabla_8"
Dict_num = {"numero": float(numero)}

es1 = Elasticsearch([{'host' : 'localhost', 'port': 9200}])
tabla_reg = 'tabla_2'
# Dict_reg = {"email": str(email), "username":str(username), "password":str(password)}
Dict_reg = {"email": email, "username":username, "password":password}

# Reset de las tablas de elasticsearch
es.indices.delete(index=tabla, ignore=[400, 404])
res= es.create(index=tabla, id=0, body=Dict_num)

es1.indices.delete(index=tabla_reg, ignore=[400, 404])
res_reg= es1.create(index=tabla_reg, id=0, body=Dict_reg)


# Definiciones scheduler
scheduler = BackgroundScheduler()

# Definiciones Flask
app = Flask(__name__)
app.secret_key = "ayush"

# Funciones
def anadir_elemento():
    global indice_escritura
    global numero
    
    print ('Indice escritura ' + str(indice_escritura))
    numero = re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4]
    print(numero)
    es.index(index=tabla, id=indice_escritura, document={"numero": float(numero)}) # Se escribe el numero en Elasticsearch
    bbt.write(canal_bbt, resource_bbt, float(numero)) # Se escribe el numero en Beebotte
    indice_escritura += 1
    return numero

def obtener_elemento_elastic():
    # global indice_lectura
    global array_numeros_es
    global media_es

    array_numeros_es = []

    # print ('Indice lectura ' + str(indice_lectura))

    # devol = es.get(index=tabla, id=indice_lectura)
    # elemento = devol['_source']['numero']

    # indice_lectura += 1
    # return elemento

    # es.indices.refresh()
    busqueda_es = es.search(index=tabla)
    # print(busqueda_es)
    Num_elem = busqueda_es["hits"]["total"]["value"]
    for i in range (Num_elem):
        # print("Numero " + str(busqueda_es["hits"]["hits"][i]["_source"]["numero"]))
        array_numeros_es.append(busqueda_es["hits"]["hits"][i]["_source"]["numero"])
    # indice_lectura += 1
    print("Array elasticsearch " + str(array_numeros_es))
    media_es = statistics.mean(array_numeros_es)
    print("Media de elasticsearch: " + str(media_es))
    # print('Ultimo numero = ' + str(busqueda_es["hits"]["hits"][indice_lectura-1]["_source"]["numero"]))
    return media_es # busqueda_es["hits"]["hits"][indice_lectura - 1]["_source"]["numero"]

def obtener_elemento_bbt():
    global array_numeros_bbt
    global media_bbt

    array_numeros_bbt = []
    Numeros_leidos = bbt.read(canal_bbt, resource_bbt, limit = indice_escritura)
    for i in range(len(Numeros_leidos)):
        array_numeros_bbt.append(float(Numeros_leidos[i]['data']))
    print("Array bbt " + str(array_numeros_bbt))

    media_bbt = statistics.mean(array_numeros_bbt)
    print ("Media de bbt: " + str(media_bbt))
    return media_bbt #Numeros_leidos[indice_lectura - 1]['data']



# Flask
@app.route("/")
def index():
    if usuario_logeado:
        return render_template('index.html',user = username_activo, num_aleat = numero, media_es = media_es, media_bbt = media_bbt)
        # return render_template('index.html',num_aleat=re.compile('\d*\.?\d*<br>').findall(requests.get('https://www.numeroalazar.com.ar/').text)[0][:-4])
    else:
        return render_template('index.html',user = username_activo, num_aleat = 0, media_es = "No se puede mostrar la media", media_bbt = "No se puede mostrar la media")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route('/success',methods = ["POST"])   
def success():
    # global email
    # global username
    # global password
    global indice_escritura_usuarios
    global usuario_logeado
    global username_activo
    if request.method == "POST":  
        session['email']=request.form['email']
        session['username']=request.form['username']
        session['password']=request.form['password']
    #  print(session)
    #  print('Email: ' + session['email'])
    #  print('Nombre de usuario: ' + session['username'])  
    #  print('Contraseña: ' + session['password'])

    email = session['email']
    username = session['username']
    password = session['password']
    #  print(email)
    print("Usuario: " + username)
    #  print(password)
    usuario_registrado = False
    busqueda_es_reg = es1.search(index=tabla_reg)
    # print(busqueda_es_reg)

    for i in range (indice_escritura_usuarios):
        if (username in busqueda_es_reg["hits"]["hits"][i]["_source"]["username"]) or (email in busqueda_es_reg["hits"]["hits"][i]["_source"]["email"]):
            print ("Correo o username ya están en la base de datos")
            usuario_registrado = True
            break
        else:
            # print ("Username no está en la base de datos")
            usuario_registrado = False

    if (not usuario_registrado):
        print("Agrego username")
        es1.index(index=tabla_reg, id=indice_escritura_usuarios, document={"email": str(email), "username": str(username), "password": str(password)}) # Se escribe el numero en Elasticsearch
        indice_escritura_usuarios += 1
        usuario_logeado = True
        username_activo = username
        anadir_elemento()  
    #  time.sleep(0.5)         
    return render_template('index.html',user = username_activo, num_aleat = numero, media_es = media_es, media_bbt = media_bbt)

@app.route("/login")
def login():
    return render_template("login.html", mensaje = "")

@app.route("/loginsuccess",methods = ["POST"])
def loginsuccess():
    global usuario_logeado
    global username_activo

    if request.method == "POST":  
        session['username']=request.form['username']
        session['password']=request.form['password']
    username_login = session['username']
    password_login = session['password']
    busqueda_es_reg = es1.search(index=tabla_reg)
    # print(busqueda_es_reg)
    # print ("indice_escritura_usuarios " + str(indice_escritura_usuarios))

    for i in range(indice_escritura_usuarios):
        if username_login in busqueda_es_reg["hits"]["hits"][i]["_source"]["username"]:
            if password_login in busqueda_es_reg["hits"]["hits"][i]["_source"]["password"]:
                print("Usuario logeado correctamente")
                usuario_logeado = True
                username_activo = username_login
                # return ("Login satisfactorio")
                return render_template('index.html',user = username_activo, num_aleat = numero, media_es = media_es, media_bbt = media_bbt)
            else:
                usuario_logeado = False
                print("El usuario existe en la base de datos pero la contraseña es incorrecta")
                # return ("Contraseña erronea")
                return render_template("login.html", mensaje = "Contraseña erronea")
            break
        else:
            print("El usuario no existe en la base de datos")
            continue
            
    if (i == indice_escritura_usuarios-1 and usuario_logeado == False) :
        # return("Usuario no registrado")
        return render_template("login.html", mensaje = "Usuario no registrado")

@app.route("/logout")
def logout():
    global usuario_logeado
    global username_activo
    if (usuario_logeado):
        usuario_logeado = False
        username_activo = 'Ningún usuario'
        return render_template('index.html',user = username_activo, num_aleat = 0, media_es = "No se puede mostrar la media", media_bbt = "No se puede mostrar la media")
    else:
        return ('No había ningún usuario logeado')

@app.route("/anadir")
def anadir():
    if usuario_logeado:
        numero = anadir_elemento()
        return render_template('index.html',user = username_activo, num_aleat = numero, media_es = media_es, media_bbt = media_bbt)
    else:
        return render_template('index.html',user = username_activo, num_aleat = 0, media_es = "No se puede mostrar la media", media_bbt = "No se puede mostrar la media")

@app.route("/elastic")
def elastic():
    if usuario_logeado:
        media_es = obtener_elemento_elastic()
        return render_template('index.html',user = username_activo, num_aleat = numero, media_es = media_es, media_bbt = media_bbt)
    else:
        return render_template('index.html',user = username_activo, num_aleat = 0, media_es = "No se puede mostrar la media", media_bbt = "No se puede mostrar la media")

@app.route("/beebotte")
def beebotte():
    if usuario_logeado:
        media_bbt = obtener_elemento_bbt()
        return render_template('index.html',user = username_activo, num_aleat = numero, media_es = media_es, media_bbt = media_bbt)
    else:
        return render_template('index.html',user = username_activo, num_aleat = 0, media_es = "No se puede mostrar la media", media_bbt = "No se puede mostrar la media")

@app.route("/graphic")
def graphic():
    if usuario_logeado:
        webbrowser.open_new_tab(Dashboard_URL)
        return render_template('index.html',user = username_activo, num_aleat = numero, media_es = media_es, media_bbt = media_bbt)
    else:
        return render_template('index.html',user = username_activo, num_aleat = 0, media_es = "No se puede mostrar la media", media_bbt = "No se puede mostrar la media")



if __name__ == "__main__":
    #app.run()
    # hilo_gen_num = Thread(target=obtener_numero, daemon = True)
    # hilo_gen_num.start()
    # time.sleep(2)
    tiempo_refresco_segundos = 120
    scheduler.add_job(anadir_elemento, 'interval', seconds=tiempo_refresco_segundos)
    scheduler.start()
    # logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    # app.run(host='0.0.0.0', port=5000, debug=True)