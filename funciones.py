#Importa funciones
import json,time,sys,platform,os.path,re,fileinput,requests,os,signal,threading, psutil, signal
from Binance import *
from trading import *
from telegram import *
from subprocess import Popen, CREATE_NEW_CONSOLE
from datetime import datetime,timedelta #Obtiene fecha y hora en formato humano
from lbcapi3 import api #api de Localbitcoins para Python 3
from nested_lookup import nested_lookup #extrae valor de listas y bibliotecas anidadas
import telepot,telebot #envía mensajes a Telegram
alias = youralias
token = yourtoken
#*************************************************
def EnviarTelegram(cadena):
	#Datos iniciales
	bot = telepot.Bot(token)
	tb = telebot.TeleBot(token)
	print(cadena)

	#Intenta 1º con telepot
	for m in range(10):
		try: bot.sendMessage(alias,cadena)
		except:
			time.sleep(1)
			continue
		else: break
	# ~ bot.sendMessage(aliasAugu,cadena)

	#Si telepot falló, intenta con telebot
	if m==9:
		for m in range(10):
			try: tb.send_message(alias,cadena)
			except:
				time.sleep(1)
				continue
			else: break
		# ~ tb.send_message(aliasAugu,cadena)
#*************************************************
def LocalCall(calltxt,CuentaLocal='Saldo1',m=10):
	libreria = {}
	for x in range(m):
		try: libreria = Llave(CuentaLocal).call('GET',calltxt).json()
		except:
			time.sleep(2)
			continue
		else: break
	return libreria
#*************************************************
def HacerTXT(Informacion,FileName,FilePath):
	FileName += '.txt'
	completeName = os.path.join(FilePath,FileName)
	with open(completeName,'w') as file:
		file.write(json.dumps(Informacion))
#*************************************************
def Llave(CuentaLocal='Saldo1'):
	#Cuenta Saldo 1
	if CuentaLocal=='Saldo1':
		hmac_key = '8ea3040c0c402dc77a478824e64427c4'
		hmac_secret = 'c92c9aaef4b8c0064b358a0a343a15864a90cea734dba33a336dec65c18015ce'

	#Cuenta MAVE45
	if CuentaLocal=='MAVE45':
		hmac_key = '9476a3e12b8cbc87022c1b210cbd9022'
		hmac_secret = 'b74936422f5d78a481c67a11c43ea1c6983b051af33cbee479550137ca7c361f'

	conn = api.hmac(hmac_key, hmac_secret)
	return conn
#*************************************************
#Obtener precio actual del bitcoin
def Bitstamp(EcuacionPrecio):
	from Binance import send_signed_request

	#Determina precio bitcoin
	calltxt = '/api/equation/'+EcuacionPrecio
	for m in range(5):
		try: stamp = Llave('Saldo1').call('GET',calltxt).json()
		except:
			# ~ print('Error en saldo1')
			time.sleep(2)
			try: stamp = Llave('MAVE45').call('GET',calltxt).json()
			except:
				# ~ print('Error en mave45')
				time.sleep(2)
				continue
		break

	#Se pudo obtener el precio del bitcoin?
	if m==4:
		try: Index = send_signed_request('GET','/dapi/v1/premiumIndex')
		except: stamp = 1
		else:
			pair = nested_lookup('pair',Index)
			for x in range(len(pair)):
				if pair[x]=='BTCUSD': break
			try: stamp = int(float(nested_lookup('indexPrice',Index)[x]))
			except: stamp = 1
	else:
		stamp = round(float(stamp['data']))

	return (stamp)
#*************************************************
#Invierte archivos escribiendo lo último arriba.
def Archivador(filename, line):
	with open(filename, 'r+') as f:
		content = f.read()
		f.seek(0, 0)
		f.write(line.rstrip('\r\n') + '\n' + content)
#*************************************************
def Desarchivador(filename,line):
	cadena = line+'\n'
	cadena1 = line
	for line in fileinput.input(filename,inplace=1):
		line = line.replace(cadena,'')
		line = line.replace(cadena1,'')
		sys.stdout.write(line)
#*************************************************
def LeerArchivoCrearLista (archivo):
	#Leer archivo
	try:
		with open(archivo) as f: lista = f.readlines()
	except: return []
	else:
		f.close()
		if not lista: return []
	#Crear lista
	x=0
	for z in lista:
		lista[x] = z.replace('\n','')
		x += 1
	while('' in lista) : lista.remove('')
	return lista
#*************************************************
def MercadoOperaciones():
	import msvcrt

	#*************************************************
	def Impresiones(Opciones):
		Tecla = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F','G','H']

		#Construye impresiones
		OpcionesDisponibles=''; TeclasPermitidas=[]
		for x in range(0,len(Opciones)):
			OpcionesDisponibles += Tecla[x]+'. '+Opciones[x]+'\n'
			TeclasPermitidas.append(Tecla[x])
		OpcionesDisponibles = OpcionesDisponibles.rstrip('\n')

		#Espera selección
		while True:
			print(OpcionesDisponibles)
			seleccion = msvcrt.getch().decode('ascii')
			time.sleep(1)
			print(seleccion)

			#Verifica si has presionado tecla admitida
			if seleccion.upper() in TeclasPermitidas:
				y = TeclasPermitidas.index(seleccion.upper())
				Respuesta = Opciones[y]
				return Respuesta
	#*************************************************
	#Define Mercados
	MercadosDisponibles1 = ['Servidor','Transfe','Transfe2','Paypal','Payoneer','Paxum','Skrillventa','Skrillcompra']
	MercadosDisponibles2 = ['Netellerventa','Netellercompra','Zellecompra','Zelleventa','Depo','Wise','Ripple','Ethereum','Litecoin']
	MercadosDisponibles = MercadosDisponibles1 + MercadosDisponibles2
	MarketName = Impresiones(MercadosDisponibles)

	#Es servidor
	if MarketName == 'Servidor':
		activacion = 'Activar'
		CuentaLocal = ''
	else:
		#Cuenta Local
		CuentasLocalDisponibles = ['Saldo1','MAVE45']
		CuentaLocal = Impresiones(CuentasLocalDisponibles)

		#Activar/Reactivar
		OpcionesDisponibles = ['Activar','Reactivar']
		activacion = Impresiones(OpcionesDisponibles)

	return MarketName,activacion,CuentaLocal
#*************************************************
def ArchivosTrabajo(MarketName,CuentaLocal=''):
	#Crea carpeta ArchivosOperativos si no existe
	try: os.makedirs('ArchivosOperativos')
	except FileExistsError: pass

	#Crea carpeta RemainingTimes si no existe
	try: os.makedirs('RemainingTimes')
	except FileExistsError: pass

	#Crea carpeta ImagenesRecibidas si no existe
	try: os.makedirs('ArchivosOperativos/ImagenesRecibidas')
	except FileExistsError: pass

	#Si Operaciones.txt no existe, se crea
	try: f = open('ArchivosOperativos/Operaciones.txt')
	except FileNotFoundError: f = open('ArchivosOperativos/Operaciones.txt', 'w')
	f.close()

	#Si OperacionesPagadas.txt no existe, se crea
	try: f = open('ArchivosOperativos/OperacionesPagadas.txt')
	except FileNotFoundError: f = open('ArchivosOperativos/OperacionesPagadas.txt', 'w')
	f.close()

	#Si OperacionesTitulares.txt no existe, se crea
	try: f = open('ArchivosOperativos/OperacionesTitulares.txt')
	except FileNotFoundError: f = open('ArchivosOperativos/OperacionesTitulares.txt', 'w')
	f.close()

	#Si MensajeLBTC.txt no existe, se crea
	try: f = open('ArchivosOperativos/MensajeLBTC.txt')
	except FileNotFoundError: f = open('ArchivosOperativos/MensajeLBTC.txt', 'w')
	f.close()

	if MarketName != 'Servidor':
		#Si UmbralPublicacionVisible.txt no existe, se crea
		try: f = open('ArchivosOperativos/'+CuentaLocal+'_UmbralPublicacionVisible.txt')
		except FileNotFoundError: f = open('ArchivosOperativos/'+CuentaLocal+'_UmbralPublicacionVisible.txt', 'w')
		f.close()

		#Si UmbralDividePago.txt no existe, se crea
		try: f = open('ArchivosOperativos/'+CuentaLocal+'_UmbralDividePago.txt')
		except FileNotFoundError: f = open('ArchivosOperativos/'+CuentaLocal+'_UmbralDividePago.txt', 'w')
		f.close()
		#Si BitstampRelation1.txt no existe, se crea
		try: f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation1.txt')
		except FileNotFoundError:
			f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation1.txt', 'w')
			f.write('1')
			f.close()
		#Si BitstampRelation2.txt no existe, se crea
		try: f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation2.txt')
		except FileNotFoundError:
			f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation2.txt', 'w')
			f.write('1')
			f.close()

		#Si ArchivoImportes.txt no existe, se crea
		try: f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt')
		except FileNotFoundError: f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt', 'w')
		f.close()

	#Si PidServidor.txt no existe, se crea
	try: f = open('ArchivosOperativos/PidServidor.txt')
	except FileNotFoundError: f = open('ArchivosOperativos/PidServidor.txt', 'w')
	f.close()

	#Si PidsMercados.txt no existe, se crea
	try: f = open('ArchivosOperativos/PidsMercados.txt')
	except FileNotFoundError: f = open('ArchivosOperativos/PidsMercados.txt', 'w')
	f.close()

	#Si Emails.txt no existe, se crea
	try: f = open('ArchivosOperativos/Emails.txt')
	except FileNotFoundError: f = open('ArchivosOperativos/Emails.txt', 'w')
	f.close()

	#Cargar historial de operaciones para respondedor
	operaciones = []
	f = open('ArchivosOperativos/Operaciones.txt','r')
	for x in f:
		x = x.strip('\n')
		operaciones.append(x)
	f.close()

	#Carga último mensaje de Localbitcoins
	f = open('ArchivosOperativos/MensajeLBTC.txt','r')
	Savedcreated_at = f.read()
	f.close()

	return operaciones,Savedcreated_at #operaciones:list
#*************************************************
def FiltroQR(name,FormaPago1,porcentaje=[],DesdeDonde=''):
	#Compite contra vendedores con palabras claves determinadas
	contador = 0
	PalabrasFiltro = ['QR','Mercado Pago','MercadoPago','Mercadopago','MERCADO PAGO','MERCADOPAGO','pagofacil','PAGOFACIL','RAPIPAGO','Mercado Pago CODIGO QR','Mercado Pago APP QR']
	for PalabraFiltrada in PalabrasFiltro:
		if PalabraFiltrada in FormaPago1: break
		contador += 1

	#Amplio la lista porcentaje si el filtor se activa desde la función PresentaAvisosTerceros
	if contador==len(PalabrasFiltro):
		if DesdeDonde=='PresentaAvisosTerceros': porcentaje.append(0)
		return porcentaje,False

	return porcentaje,True
#*************************************************
def BitstampRelationInicial(market1,MarketName,CuentaLocal):
	#Variables iniciales
	from funciones import BitcoinArgentina

	#Precio bitcoin ARS
	ARSstamp = LocalCall('/api/equation/bitstampusd*USD_in_ARS')
	ARSstamp = float(ARSstamp['data'])

	#Precio mercado
	PrecioArgentina = BitcoinArgentina()

	#Grabo BitstampRelation1
	BitstampRelation1 = round(PrecioArgentina/ARSstamp+0.04,2)

	#Modifico archivo BitstampRelation1
	f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation1.txt','w')
	f.write(str(BitstampRelation1))
	f.close()

	return BitstampRelation1
#*************************************************
def DatosMercado(MarketName,CuentaLocal,DesdeDonde='',activacion=''):
	market1,market2,market3,NumAviso,EcuacionPrecio,BitstampRelation1 = '','','','',0,0
	#TRANSFERENCIA ARGENTINA SELL OPCIÓN 2
	if 'TRANSFE2' in MarketName.upper():
		MarketName = 'Transfe2'
		market1 = '/buy-bitcoins-online/ars/national-bank-transfer/.json'
		market2 = '/buy-bitcoins-online/ars/transfers-with-specific-bank/.json'
		market3 = '/buy-bitcoins-online/ars/other-online-payment/.json'
		if CuentaLocal == 'Saldo1': NumAviso = '895691'
		EcuacionPrecio = 'bitstampusd*USD_in_ARS'
		if DesdeDonde=='Inicio' and activacion=='Activar': BitstampRelation1 = BitstampRelationInicial(market1,MarketName,CuentaLocal)
	#PAYPAL BUY
	if 'PAYPAL' in MarketName.upper():
		MarketName = 'Paypal'
		market1 = '/sell-bitcoins-online/usd/paypal/.json'
		market2,market3 = '',''
		if CuentaLocal == 'Saldo1':  NumAviso = '475496'
		if CuentaLocal == 'MAVE45': NumAviso = '1386978'
		EcuacionPrecio = 'bitstampusd'
		BitstampRelation1 = 1.00
	#TRANSFERENCIA ARGENTINA SELL
	if 'TRANSFE' in MarketName.upper() and 'TRANSFE2' not in MarketName.upper():
		MarketName = 'Transfe'
		market1 = '/buy-bitcoins-online/ars/national-bank-transfer/.json'
		market2 = '/buy-bitcoins-online/ars/transfers-with-specific-bank/.json'
		market3 = '/buy-bitcoins-online/ars/other-online-payment/.json'
		if CuentaLocal == 'Saldo1': NumAviso = '488773'
		if CuentaLocal == 'MAVE45': NumAviso = '1386835'  #MAVE45
		EcuacionPrecio = 'bitstampusd*USD_in_ARS'
		if DesdeDonde=='Inicio' and activacion=='Activar': BitstampRelation1 = BitstampRelationInicial(market1,MarketName,CuentaLocal)
	if 'DEPO' in MarketName.upper():
		MarketName = 'Depo'
		market1 = '/buy-bitcoins-online/ars/cash-deposit/.json'
		market2,market3 = '',''
		if CuentaLocal == 'Saldo1': NumAviso = '1296303' #SALDO1
		if CuentaLocal == 'MAVE45': NumAviso = '1386981'  #MAVE45
		EcuacionPrecio = 'bitstampusd*USD_in_ARS'
		if DesdeDonde=='Inicio' and activacion=='Activar': BitstampRelation1 = BitstampRelationInicial(market1,MarketName,CuentaLocal)
	#PAYONEER BUY
	if 'PAYONEER' in MarketName.upper():
		MarketName = 'Payoneer'
		market1 = '/sell-bitcoins-online/usd/payoneer/.json'
		market2,market3 = '',''
		if CuentaLocal == 'Saldo1': NumAviso = '494501' #SALDO1
		if CuentaLocal == 'MAVE45': NumAviso = '1389093'  #MAVE45
		EcuacionPrecio = 'bitstampusd'
		BitstampRelation1 = 0.95
	#SKRILL BUY
	if 'SKRILL' in MarketName.upper() and 'COMPRA' in MarketName.upper():
		MarketName = 'Skrillcompra'
		market1 = '/sell-bitcoins-online/usd/moneybookers-skrill/.json'
		market2,market3 = '',''
		if CuentaLocal == 'Saldo1': NumAviso = '622297' #SALDO1
		if CuentaLocal == 'MAVE45': NumAviso = '1386980'  #MAVE45
		EcuacionPrecio = 'bitstampusd'
		BitstampRelation1 = 0.95
	#SKRILL SELL
	if 'SKRILL' in MarketName.upper() and 'VENTA' in MarketName.upper():
		MarketName = 'Skrillventa'
		market1 = '/buy-bitcoins-online/usd/moneybookers-skrill/.json'
		market2,market3 = '',''
		if CuentaLocal == 'Saldo1': NumAviso = '368080' #SALDO1
		EcuacionPrecio = 'bitstampusd'
		BitstampRelation1 = 1.05
	#PAXUM BUY
	if 'PAXUM' in MarketName.upper():
		MarketName = 'Paxum'
		market1 = '/sell-bitcoins-online/usd/other-online-payment/.json'
		market2 = '/sell-bitcoins-online/usd/western-union/.json'
		market3 = '/sell-bitcoins-online/usd/moneygram/.json'
		if CuentaLocal == 'Saldo1': NumAviso = '1115387' #SALDO1
		if CuentaLocal == 'MAVE45': NumAviso = '1386979'  #MAVE45
		EcuacionPrecio = 'bitstampusd'
		BitstampRelation1 = 0.99
	#NETELLER BUY
	if 'NETELLER' in MarketName.upper() and 'COMPRA' in MarketName.upper():
		MarketName = 'Netellercompra'
		market1 = '/sell-bitcoins-online/usd/neteller/.json'
		market2,market3 = '',''
		if CuentaLocal == 'Saldo1' :NumAviso = '1275609' #SALDO1
		EcuacionPrecio = 'bitstampusd'
		BitstampRelation1 = 0.95
	#NETELLER SELL
	if 'NETELLER' in MarketName.upper() and 'VENTA' in MarketName.upper():
		MarketName = 'Netellerventa'
		market1 = '/buy-bitcoins-online/usd/neteller/.json'
		market2,market3 = '',''
		if CuentaLocal == 'Saldo1': NumAviso = '368078' #SALDO1
		EcuacionPrecio = 'bitstampusd'
		BitstampRelation1 = 1.05
	if 'ZELLE' in MarketName.upper() and 'COMPRA' in MarketName.upper():
		MarketName = 'Zellecompra'
		market1 = '/sell-bitcoins-online/usd/zelle/.json'
		market2,market3 = '',''
		if CuentaLocal == 'Saldo1': NumAviso = '1279728' #SALDO1
		EcuacionPrecio = 'bitstampusd'
		BitstampRelation1 = 0.95
	if 'ZELLE' in MarketName.upper() and 'VENTA' in MarketName.upper():
		MarketName = 'Zelleventa'
		market1 = '/buy-bitcoins-online/usd/zelle/.json'
		market2,market3 = '',''
		if CuentaLocal == 'Saldo1': NumAviso = '1290393' #SALDO1
		EcuacionPrecio = 'bitstampusd'
		BitstampRelation1 = 1.05
	if 'WISE' in MarketName.upper():
		MarketName = 'Transferwise'
		market1 = '/sell-bitcoins-online/usd/transferwise/.json'
		market2,market3 = '',''
		if CuentaLocal == 'Saldo1': NumAviso = '1332292' #SALDO1
		EcuacionPrecio = 'bitstampusd'
		BitstampRelation1 = 0.95
	if 'RIPPLE' in MarketName.upper():
		MarketName = 'Ripple'
		market1 = '/sell-bitcoins-online/ripple-altcoin/.json'
		market2,market3 = '',''
		if CuentaLocal == 'Saldo1': NumAviso = '1350190' #SALDO1
		EcuacionPrecio = 'poloniexxrp'
		BitstampRelation1 = 0.95
	if 'ETHEREUM' in MarketName.upper():
		MarketName = 'Ethereum'
		market1 = '/sell-bitcoins-online/ethereum-altcoin/.json'
		market2,market3 = '',''
		if CuentaLocal == 'Saldo1': NumAviso = '1350506' #SALDO1
		EcuacionPrecio = 'poloniexeth'
		BitstampRelation1 = 0.95
	if 'LITECOIN' in MarketName.upper():
		MarketName = 'Litecoin'
		market1 = '/sell-bitcoins-online/litecoin-altcoin/.json'
		market2,market3 = '',''
		if CuentaLocal == 'Saldo1': NumAviso = '1350505' #SALDO1
		EcuacionPrecio = 'poloniexltc'
		BitstampRelation1 = 0.95

	#DatosMercado, PosicionaTuAviso, MercadoOperaciones, TelegramBot, Preguntador
	if NumAviso=='': MarketName=''
	return market1,market2,market3,NumAviso,EcuacionPrecio,BitstampRelation1,MarketName
#*************************************************
#Chequea conexión a Internet
def HayInternet():
	try:
		requests.get('http://www.google.com/', timeout=(2,5))
		return True
	except: return False
#*************************************************
def DatosIniciales(MarketName,lanzador,TelegramProximoID,CuentaLocal):
	#Función que verifica el ingreso de números
	def CheckNumber(cadena,accion,ProximoID):
		global TelegramProximoID
		TelegramProximoID = ProximoID

		if lanzador=='pc':
			VecesPregunta = -1
			while True:
				VecesPregunta += 1
				if VecesPregunta >= 2:
					time.sleep(30)
					exit()
				instruccion = input(cadena)
				time.sleep(0.5)
				if accion=='EsNumero':
					try: float(instruccion)
					except:	continue
					else: break
				if accion=='EsAfirmativo':
					ListaTest = ['SI','SÍ','NO','S','N']
					for j in ListaTest:
						if instruccion.upper()==j:
							instruccion = j
							if instruccion == 'SÍ' or instruccion == 'S': instruccion = 'SI'
							if instruccion == 'N': instruccion = 'NO'
							return instruccion,TelegramProximoID
		else:
			instruccion,TelegramProximoID = Repreguntador(cadena,accion,TelegramProximoID)
			if not instruccion:
				time.sleep(30)
				exit()
		return instruccion,TelegramProximoID

	#BitstampRelation1
	if MarketName=='Transfe2' or MarketName =='Transfe' or MarketName =='Depo':
		cadena = 'Límite mínimo ($)? '
		BitstampRelation1,TelegramProximoID = CheckNumber(cadena,'EsNumero',TelegramProximoID)
	else:
		cadena = 'Límite máximo (%)? '
		BitstampRelation1,TelegramProximoID = CheckNumber(cadena,'EsNumero',TelegramProximoID)
		BitstampRelation1 = round(1+float(BitstampRelation1)/100,4)
	f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation1.txt','w')
	f.write(str(BitstampRelation1))
	f.close()

	#BitstampRelation2
	if MarketName=='Transfe2' or MarketName =='Transfe' or MarketName =='Depo':
		cadena = 'Límite máximo ($)? '
		BitstampRelation2,TelegramProximoID = CheckNumber(cadena,'EsNumero',TelegramProximoID)
	else:
		cadena = 'Límite mínimo (%)? '
		BitstampRelation2,TelegramProximoID = CheckNumber(cadena,'EsNumero',TelegramProximoID)
		BitstampRelation2 = round(1+float(BitstampRelation2)/100,4)
	f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation2.txt','w')
	f.write(str(BitstampRelation2))
	f.close()

	#Mínimo / Máximo
	if MarketName=='Transfe2' or MarketName=='Transfe' or MarketName=='Depo':
		#Muestra archivo de cuentas
		f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt','r')
		cadena = f.read()
		f.close()
		if not cadena: cadena = 'Archivo '+CuentaLocal+'_'+MarketName+'_Importes vacío!'
		else: cadena = 'Archivo '+CuentaLocal+'_'+MarketName+'_Importes actual:\n\n'+cadena+'\n'

		if lanzador == 'pc':
			print(cadena)
			Respuesta,TelegramProximoID = CheckNumber('Continuar (si/no)? ','EsAfirmativo',TelegramProximoID)
			if Respuesta=='NO':
				import msvcrt
				print('Por favor modificar archivo Importes'+MarketName+'.txt y presionar tecla para continuar')
				activacion = msvcrt.getch().decode('ascii')
				time.sleep(1)
				#Lee archivo cuentas.txt y lo presenta
				f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt','r')
				cadena = f.read()
				f.close()
				if not cadena: cadena = 'Archivo '+CuentaLocal+'_'+MarketName+'_Importes vacío!'
				else: cadena = 'Archivo '+CuentaLocal+'_'+MarketName+'_Importes actual:\n\n'+cadena+'\n'
				print(cadena)

		#Pregunta si se usa nuevo archivo Importes
		if lanzador == 'telegram':
			EnviarTelegram(cadena)

			#Pregunta si se modifica el archivo Importes
			Respuesta,TelegramProximoID = CheckNumber('Nuevo archivo de cuentas (si/no)? ','EsAfirmativo',TelegramProximoID)
			if Respuesta=='SI':
				#Elimina viejo archivo cuentas
				f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt','w')
				f.close()
				#Solicita nuevo archivo cuentas
				cadena = 'Cuenta para archivo '+CuentaLocal+'_'+MarketName+'_Importes?'
				NuevoArchivoCuentas,TelegramProximoID = Repreguntador(cadena,'cuenta',TelegramProximoID)

				#Registro nuevo archivo cuentas si está correctamente informado
				if ('CBU' in NuevoArchivoCuentas or 'CVU' in NuevoArchivoCuentas) and '$' in NuevoArchivoCuentas:
					Archivador('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt',NuevoArchivoCuentas)
					cadena = 'Archivo '+CuentaLocal+'_'+MarketName+'_Importes actualizado:\n\n'+NuevoArchivoCuentas
				else: cadena = 'Archivo '+CuentaLocal+'_'+MarketName+'_Importes no se actualizó!\n\n'

				#Telegram
				EnviarTelegram(cadena)

	else:
		MinAviso,TelegramProximoID = CheckNumber('Mínimo Aviso? ','EsNumero',TelegramProximoID)
		if MarketName=='Ripple' or MarketName=='Ethereum' or MarketName=='Litecoin': MinAviso = float(MinAviso)
		MinAviso = int(float(MinAviso))
		MaxAviso,TelegramProximoID = CheckNumber('Máximo Aviso? ','EsNumero',TelegramProximoID)
		if MarketName=='Ripple' or MarketName=='Ethereum' or MarketName=='Litecoin': MaxAviso = float(MaxAviso)
		MaxAviso = int(float(MaxAviso))
		#Graba txt
		NuevosImportes = '$'+str(MinAviso)+'\n$'+str(MaxAviso)
		f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt','w')
		f.write(NuevosImportes)
		f.close()

	return BitstampRelation1,BitstampRelation2,TelegramProximoID
#*************************************************
def MarketRelation(MarketName,market1,EcuacionPrecio,CuentaLocal):
	#Variables Iniciales
	from funciones import Bitstamp,LocalCall

	#Prepara contra mercados
	if 'sell' in market1: ContraMarket = market1.replace('sell','buy')
	else: ContraMarket = market1.replace('buy','sell')

	#Obtiene ContraMarket
	AvisosTerceros = LocalCall(ContraMarket)
	precio = nested_lookup('temp_price',AvisosTerceros)
	maximo = nested_lookup('max_amount_available',AvisosTerceros)
	trade_count = nested_lookup('trade_count',AvisosTerceros)

	#Ordena markets, transforma lista de precios en números y los ordena
	precio1 = []
	for j in precio: precio1.append(float(j))
	precio = precio1

	#Encuentro umbral de oferentes a considerar
	if MarketName=='Transfe2' or MarketName=='Transfe' or MarketName=='Depo': umbral = 10000
	else: umbral = 200

	#Busca mejor anunciante
	BestPrice = ''
	for i in range(len(precio)):
		#Elimina oferentes sin stock
		if MarketName=='Transfe2' or MarketName=='Transfe' or MarketName=='Depo':
			if not maximo[i]: maximo[i] = '10000000'
			if float(maximo[i]) <= umbral: continue
		else:
			if not maximo[i]: maximo[i] = '1000'
			if float(maximo[i]) <= umbral: continue

		#Anunciante Novato
		if trade_count[i]=='+30' or not '+' in trade_count[i]: continue

		#Mejor Precio
		BestPrice = precio[i]
		break

	#Calcula MarketRelation
	if CuentaLocal=='CriptoenArgentina': return BestPrice
	stamp = Bitstamp(EcuacionPrecio)
	if not stamp or not BestPrice:
		#Si no puedo encontrar el nuevo MarketRelation, uso BitstampRelation1
		f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation1.txt','r')
		MarketRelation1 = round(float(f.read()),4)
		f.close()
		return MarketRelation1
	MarketRelation1 = round(BestPrice/stamp,4)

	#Corrige  MarketRelation 1%
	# ~ if 'sell' in market1: MarketRelation1 -= 0.01
	# ~ else: MarketRelation1 += 0.01

	return MarketRelation1
#*************************************************
def Depurador():
	from funciones import LeerArchivoCrearLista,Desarchivador

	#Carga archivos
	ListaOperaciones = LeerArchivoCrearLista('ArchivosOperativos/Operaciones.txt')
	ListaOperacionesPagadas = LeerArchivoCrearLista('ArchivosOperativos/OperacionesPagadas.txt')
	ListaOperacionesTitulares = LeerArchivoCrearLista('ArchivosOperativos/OperacionesTitulares.txt')
	ListaEmails = LeerArchivoCrearLista('ArchivosOperativos/Emails.txt')

	#Depura OperacionesPagadas
	for OperacionPagada in ListaOperacionesPagadas:
		contador = 0
		for Operacion in ListaOperaciones:
			if Operacion in OperacionPagada: contador += 1
		if contador==0: Desarchivador('ArchivosOperativos/OperacionesPagadas.txt',OperacionPagada)

	#Depura OperacionesTitulares
	for OperacionTitular in ListaOperacionesTitulares:
		contador = 0
		for Operacion in ListaOperaciones:
			if Operacion in OperacionTitular: contador += 1
		if contador==0: Desarchivador('ArchivosOperativos/OperacionesTitulares.txt',OperacionTitular)

	#Depura Emails
	for Emails in ListaEmails:
		contador = 0
		for Operacion in ListaOperaciones:
			if Operacion in Emails: contador += 1
		if contador==0: Desarchivador('ArchivosOperativos/Emails.txt',Emails)
#*************************************************
def	BitcoinArgentina():
	PrecioTodosArgentina = LocalCall('/buy-bitcoins-online/ars/national-bank-transfer/.json')
	temp_price = nested_lookup('temp_price',PrecioTodosArgentina)
	min_amount = nested_lookup('min_amount',PrecioTodosArgentina)
	max_amount = nested_lookup('max_amount_available',PrecioTodosArgentina)

	for y in range(1,20):
		PrecioArgentina = float(temp_price[y])
		try: min_amountArgentina = float(min_amount[y])
		except: min_amountArgentina = 0
		try: max_amountArgentina = float(max_amount[y])
		except: max_amountArgentina = 100000
		if max_amountArgentina>15000 and min_amountArgentina<50000: break
	if y==19: PrecioArgentina = float(temp_price[2])
	# ~ PrecioArgentina = PrecioArgentina*0.99
	return PrecioArgentina
#*************************************************
def CuentaLocalbitcoins(TelegramProximoID):
	#Cuenta Local
	CuentaLocal,TelegramProximoID = Repreguntador('Cuenta Local (Saldo1/MAVE45)? ','cuenta',TelegramProximoID)
	if CuentaLocal.upper()=='MAVE45': CuentaLocal = 'MAVE45'
	if CuentaLocal.upper()=='SALDO1': CuentaLocal = 'Saldo1'
	if CuentaLocal!='MAVE45' and CuentaLocal!='Saldo1':
		EnviarTelegram('Cuenta Localbitcoins mal informada!')
		return TelegramProximoID,''
	return TelegramProximoID,CuentaLocal
#*************************************************
def DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID):
	from funciones import EnviarTelegram,CuentaLocalbitcoins

	#Determina cuenta de Localbitcoins
	CuentaLocal = ''
	if 'SALDO1' in instruccion.upper(): CuentaLocal = 'Saldo1'
	if 'MAVE45' in instruccion.upper(): CuentaLocal = 'MAVE45'

	#Pregunta cuenta de Localbitcoins
	if not CuentaLocal:
		TelegramProximoID,CuentaLocal = CuentaLocalbitcoins(TelegramProximoID)

		if not CuentaLocal:
			EnviarTelegram('No se informó usuario de Localbitcoins!')
			return '',TelegramProximoID

	return CuentaLocal,TelegramProximoID
#*************************************************
def DeterminaContacto(instruccion):
	#Obtengo contacto al que apunta el mensaje
	if ':' in instruccion:
		contacto = instruccion[0:instruccion.index(':')].upper()
		contacto = contacto.replace(' ','')
	else:
		contacto = re.findall(r'\d+',instruccion)
		if contacto: contacto = contacto[0]
		else: contacto = ''

	#Si el contacto informado tiene menos de 8 dígitos, determino el numero de contacto
	if len(contacto)<8:
		ListaOperacionesTitulares = LeerArchivoCrearLista('ArchivosOperativos/OperacionesTitulares.txt')
		for OperacionTitular in ListaOperacionesTitulares:
			if contacto in OperacionTitular:
				ListaInfo = OperacionTitular.rsplit('#')
				contacto = ListaInfo[0]
				break
		#El contacto no está abierto
		if len(contacto)<8: contacto = ''

	#Determino CuentaLocal correspondiente al contacto
	cadena = '/api/contact_info/'+contacto+'/'
	for m in range(5):
		try: ContactInfo = Llave('Saldo1').call('GET',cadena).json()
		except:
			time.sleep(5)
			continue
		else: break
	if m==4:
		print('No se logró obtener el contacto')
		return '',''

	error = nested_lookup('error',ContactInfo)
	if error: CuentaLocal = 'MAVE45'
	else: CuentaLocal = 'Saldo1'

	return contacto,CuentaLocal
#*************************************************
def ObtenerMercado(market):
	for m in range(3):
		try: AvisosTerceros = Llave('Saldo1').call('GET',market).json()
		except:
			time.sleep(5)
			try: AvisosTerceros = Llave('MAVE45').call('GET',market).json()
			except:
				time.sleep(5)
				continue
			else: return AvisosTerceros
		else: return AvisosTerceros

	if m==2:
		print('Error al obtener AvisosTerceros')
		return None
#*************************************************
