#Importa funciones
import json,time,sys,platform,os.path,re,fileinput,requests,os,signal,threading, psutil
from Binance import *
from funciones import *
from telegram import *
from trading import *
from respuesta import *
from subprocess import Popen, CREATE_NEW_CONSOLE
from datetime import datetime,timedelta #Obtiene fecha y hora en formato humano
from lbcapi3 import api #api de Localbitcoins para Python 3
from nested_lookup import nested_lookup #extrae valor de listas y bibliotecas anidadas
import telepot,telebot #envía mensajes a Telegram
#*************************************************
def LoopControl(operaciones):
	global dash,EsperaEmail

	#Servidor
	if MarketName=='Servidor':
		#TelegramListener
		threading.Thread(target=TelegramListener).start()

		while True:
			#Controles que se realizan en todos los usuarios de Localbitcoins
			LocalbitcoinsListener('Saldo1')
			LocalbitcoinsListener('MAVE45')
			EliminaPidsInactivos('PidsMercados')

			#Determino si debo leer dashboard
			PidsMercados = LeerArchivoCrearLista('ArchivosOperativos/PidsMercados.txt')
			PidsSaldo1 = 0; PidsMave45 = 0
			for PidMercado in PidsMercados:
				ListaInfo = PidMercado.rsplit('#')
				if ListaInfo[1]=='Saldo1': PidsSaldo1 += 1
				if ListaInfo[1]=='MAVE45': PidsMave45 += 1
			if PidsSaldo1>0: Dashboard('Saldo1')
			if PidsMave45>0: Dashboard('MAVE45')

			#Determino si debo entrar a calificador
			OperacionesTitulares = LeerArchivoCrearLista('ArchivosOperativos/OperacionesTitulares.txt')
			OperacionesTitularesSaldo1 = 0; OperacionesTitularesMave45 = 0
			for OperacionTitular in OperacionesTitulares:
				ListaInfo = OperacionTitular.rsplit('#')
				if ListaInfo[2]=='Saldo1': OperacionesTitularesSaldo1 += 1
				if ListaInfo[2]=='MAVE45': OperacionesTitularesMave45 += 1
			# ~ print(datetime.now().strftime('%H:%M:%S'),'Entra a Calificador')
			if OperacionesTitularesSaldo1>0: Calificador('Saldo1')
			# ~ print(datetime.now().strftime('%H:%M:%S'),'Sale de Calificador')
			if OperacionesTitularesMave45>0: Calificador('MAVE45')

	#Bot
	else:
		#Primera respuesta
		IrPrimeraRespuesta = False
		if MarketName=='Transfe' or MarketName=='Transfe2' or MarketName=='Depo': threading.Thread(target=PrimeraRespuesta,args=[MarketName,dash,operaciones,EsperaEmail,CuentaLocal]).start()
		else: IrPrimeraRespuesta = True
		while True:
			#Primera respuesta
			if IrPrimeraRespuesta: dash,operaciones,EsperaEmail = PrimeraRespuesta(MarketName,dash,operaciones,EsperaEmail,CuentaLocal)

			#Presenta y modifica aviso
			PosicionaTuAviso('pc',MarketName,CuentaLocal)

			#Leo Dashboard
			if MarketName=='Transfe' or MarketName=='Transfe2' or MarketName=='Depo':
				cadena = 'ArchivosOperativos/Dashboard_'+CuentaLocal+'.txt'
				try: f = open(cadena,'r')
				except:	pass
				else:
					dash = f.read()
					f.close()
					try: dash = json.loads(dash)
					except:	continue
					contact_count = dash['data']['contact_count']

					#No prosigo si dashboard está en cero
					if contact_count==0: continue

			#Print Dashboard
			if HayInternet() and dash:
				#Saldo1
				try: contact_count = nested_lookup('contact_count',dash)[0]
				except:	continue
				if contact_count>0: PrintDashboard(CuentaLocal)

			#Pregunta que PidServidor están vivos
			PidActivos = EliminaPidsInactivos('PidServidor')
			if PidActivos=='1': #Si no hay servidor activo, se lanza uno
				print('Se lanza nuevo servidor')
				Popen([sys.executable,'bot.py','Servidor','activa'], creationflags=CREATE_NEW_CONSOLE)
#*************************************************
def Dashboard(CuentaLBTC):
	global dash

	#Detecta PC
	node = platform.uname().node
	if node=='Dell': path = 'C:\Users\Videla\Documents\Python\Localbitcoins\ArchivosOperativos'
	else: path = 'C:/Users/andre/Documents/Python/ArchivosOperativos'

	#Busca Dashboard: info de nuevas ordenes
	try: dash = Llave(CuentaLBTC).call('GET','/api/dashboard/').json()
	except:	pass
	else:
		cadena = 'Dashboard_'+CuentaLBTC
		HacerTXT(dash,cadena,path)
#*************************************************
def PrintDashboard(CuentaLocal):
	#Obtiene información de dashboard
	contact_id = nested_lookup('contact_id',dash)
	payment_method = nested_lookup('payment_method',dash) #Identificación de los contactos
	trade_type = nested_lookup('trade_type',dash)
	amount =  nested_lookup('amount',dash)
	name = nested_lookup('name',dash)
	trade_count = nested_lookup('trade_count',dash)
	payment_completed_at = nested_lookup('payment_completed_at',dash)
	username = nested_lookup('username',dash)
	disputed_at = nested_lookup('disputed_at',dash)
	bot = telepot.Bot(token)
	tb = telebot.TeleBot(token)
	bot2 = telepot.Bot(tokenAugu)
	tb2 = telebot.TeleBot(tokenAugu)

	#Filtra el nombre, número de operaciones y puntaje de contraparte
	name1 = []
	for x in name:
		if CuentaLocal in x: continue
		name1.append(x)

	#Imprime Dashboard
	cadena = 'DASHBOARD\n'
	for y in range(len(contact_id)):
		if payment_completed_at[y] == None: estado = 'Esperando Pago'
		elif disputed_at[y] != None: estado = 'En Disputa'
		else: estado = 'Pagado'
		contacto = str(contact_id[y]); ContactoCorto = contacto[len(contacto)-4:len(contacto)]
		cadena = cadena+payment_method[y]+'\t'+trade_type[y]+'\t'+ContactoCorto+'\t'+name1[y]+'\t'+str(amount[y])+'\t'+estado+'\n'
	print(cadena)

	return
#*************************************************
#https://telepot.readthedocs.io/en/latest/reference.html
def TelegramListener():
	#Variables Globales
	global TelegramProximoID,MarketName
	bot = telepot.Bot(token)

	#Chequea mensajes
	while True:
		#Telegram actualiza mensajes
		try: response = bot.getUpdates(offset=TelegramProximoID)
		except:
			print(datetime.now().strftime('%H:%M:%S'),' Sin Telegram')
			time.sleep(5)
			continue

		#Determino si hay mensaje nuevo
		update_id = nested_lookup('update_id',response)
		if not update_id:
			time.sleep(1)
			continue
		TelegramProximoID = update_id[len(update_id)-1]+1

		#Nuevos mensaje, verifico si hay imágenes
		file_id = nested_lookup('file_id',response)
		if file_id:
			text,file_id = [],[]
			for x in range(len(response)):
				#Texto
				text1 = nested_lookup('text',response[x])
				if text1: text1 = text1[0]
				else : text1 = 'FOTO'
				text.append(text1)
				#Imagen
				file_id1 = nested_lookup('file_id',response[x])
				if file_id1: file_id1 = file_id1[1]
				else : file_id1 = ''
				file_id.append(file_id1)
		else: text = nested_lookup('text',response)

		#Inicia loop de revisión de mensajes nuevos
		BusqueDash,TextCounter = False,-1
		for instruccion in text:
			print(datetime.now().strftime('%H:%M:%S'),' Telegram nuevo mensaje ',instruccion)
			TextCounter = TextCounter+1
			if 'AYUDA' in instruccion.upper() and ':' not in instruccion.upper(): TelegramAyuda(); continue
			if 'BINANCE' in instruccion.upper() and 'EQUILIBRAR' in instruccion.upper() and ':' not in instruccion.upper():
				bot.sendMessage(alias,'Binance inicia balanceo para equilibrar posición'); bot.sendMessage(aliasAugu,'Binance inicia balanceo para equilibrar posición');
				BinancePosition(); continue
			if 'BOT' in instruccion.upper() and ':' not in instruccion.upper(): TelegramBot(); continue
			if 'FUTURO' in instruccion.upper() and 'DEPOSITAR' in instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramBinanceDepositarFuturo(TelegramProximoID); continue
			if 'FUTURO' in instruccion.upper() and 'EXTRAER' in instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramBinanceExtraerFuturo(TelegramProximoID); continue
			if 'BINANCE' in instruccion.upper() and 'BALANCE' in instruccion.upper() and ':' not in instruccion.upper(): BinanceMargin('Estado'); continue
			if 'USDT' in instruccion.upper() and ':' not in instruccion.upper(): TelegramUSDT(); continue
			if 'PANEL' in instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramPanel(TelegramProximoID,instruccion); continue
			# ~ if ('%' in instruccion or '$' in instruccion) and ':' not in instruccion:	TelegramProximoID = TelegramPorcentaje(instruccion,TelegramProximoID); continue
			if 'CLIENTE' in instruccion.upper() and 'VENTA' in instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramClienteVenta(instruccion,TelegramProximoID); continue
			if 'CLIENTE' in instruccion.upper() and 'COMPRA' in instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramClienteCompra(instruccion,TelegramProximoID); continue
			if 'CLIENTE' in instruccion.upper() and 'DATOS' in instruccion.upper() and ':' not in instruccion.upper(): TelegramClienteDatos(instruccion); continue
			if 'COMPRA' in instruccion.upper() and 'PAYTIZ' in instruccion.upper() and ':' not in instruccion.upper(): TelegramCompraPaytiz(); continue
			if 'COMPRA' == instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramCompra(TelegramProximoID); continue
			if 'BOOK' in instruccion.upper() and ':' not in instruccion.upper(): TelegramBook(instruccion); continue
			if 'AVISO' in instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramAviso(instruccion,TelegramProximoID); continue
			if 'VOLUMEN' in instruccion.upper() and '24' in instruccion.upper() and ':' not in instruccion.upper(): TelegramVolumen24(instruccion); continue
			if 'VOLUMEN' in instruccion.upper() and ':' not in instruccion.upper(): TelegramVolume(instruccion); continue
			if 'HORA' in instruccion.upper() and (':' or 'HORACIO') not in instruccion.upper(): TelegramProximoID = TelegramHora(instruccion,TelegramProximoID); continue
			if 'UMBRAL' in instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramUmbrales(instruccion,TelegramProximoID); continue
			if 'MAILING' in instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramMailing(instruccion,TelegramProximoID); continue
			if 'COTI' in instruccion.upper() and ':' not in instruccion.upper(): TelegramCoti(instruccion); continue
			if 'RENTA' in instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramRenta(TelegramProximoID); continue
			if 'PAYTIZ' in instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramPaytiz(TelegramProximoID); continue
			if 'LBTC' in instruccion.upper() and 'TRANSACCIONES' in instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramLBTCtransacciones(instruccion,TelegramProximoID); continue
			if 'LBTC' in instruccion.upper() and 'EXTRAER' in instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramLBTCextraer(instruccion,TelegramProximoID); continue
			if 'LBTC' in instruccion.upper() and 'ADDRESS' in instruccion.upper() and ':' not in instruccion.upper():
				CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
				try: cadena = Llave(CuentaLocal).call('POST','/api/wallet-addr/').json()['data']['address']
				except: continue
				EnviarTelegram(cadena)
				continue
			if 'LBTC' in instruccion.upper() and 'FEE' in instruccion.upper() and ':' not in instruccion.upper():
				try: fees = LocalCall('/api/fees/','Saldo1')['data']
				except: continue
				cadena = 'Depositar ' + fees.get('deposit_fee') + '    Extraer ' + fees.get('outgoing_fee')
				EnviarTelegram(cadena)
				continue
			if 'BTC' in instruccion.upper() and ':' not in instruccion.upper(): BTC(); continue
			if 'CUENTA' in instruccion.upper() and ':' not in instruccion.upper():
				TelegramProximoID = TelegramCuenta(instruccion,TelegramProximoID)
				continue
			if 'IMPORTE' in instruccion.upper() and ':' not in instruccion.upper():
				if 'CBU' in instruccion or 'CVU' in instruccion: continue
				MarketName,TelegramProximoID,CuentaLocal = TelegramNuevosimportes(instruccion,TelegramProximoID)
				if not MarketName: continue
				SelectorMinimoMaximo(MarketName,CuentaLocal)
				continue
			if ('%' in instruccion or '$' in instruccion) and ':' not in instruccion:
				if 'CBU' in instruccion or 'CVU' in instruccion: continue
				TelegramProximoID = TelegramPorcentaje(instruccion,TelegramProximoID); continue
			if 'DESACTIVA' in instruccion.upper() and ':' not in instruccion.upper():
				NumAviso,TelegramProximoID,CuentaLocal = TelegramDesactivar(instruccion,TelegramProximoID)
				if NumAviso and CuentaLocal:
					while True:
						ModificaAviso(NumAviso,1,10,False,CuentaLocal)
						TuAviso = LocalCall('/api/ad-get/'+NumAviso+'/',)
						try: visible = nested_lookup('visible',TuAviso)[0]
						except: continue
						if not visible:
							#Desactiva aviso
							cadena = 'Aviso desactivado!'
							EnviarTelegram(cadena)
							break
				continue
			if 'REACTIVA' in instruccion.upper() and ':' not in instruccion.upper(): TelegramReactiva(instruccion,TelegramProximoID); continue
			if 'ACTIVA' in instruccion.upper() and ':' not in instruccion.upper(): TelegramActiva(instruccion,TelegramProximoID); continue
			if 'BALANCE' in instruccion.upper() and ':' not in instruccion.upper(): TelegramProximoID = TelegramBalance(TelegramProximoID); continue
			#MENSAJE
			if ':' in instruccion: TelegramMensaje(instruccion); continue
			if 'CHAT' in instruccion.upper(): TelegramChat(instruccion); continue
			if 'FOTO' in instruccion.upper(): TelegramFoto(response,TextCounter,file_id); continue
			if 'DASH' in instruccion.upper(): TelegramProximoID = TelegramDashboard(instruccion,TelegramProximoID); continue
			#MERCADO
			market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(instruccion,'Saldo1')
			if MarketName:
				PresentaAvisosTerceros(MarketName,'Saldo1','telegram')
				continue
			#CONTACTO ABIERTO
			TelegramProximoID = TelegramContactoAbierto(instruccion,TelegramProximoID)
#*************************************************
def Calificador(CuentaLBTC):
	#Lee archivo Operaciones.txt
	ListaOperaciones = LeerArchivoCrearLista('ArchivosOperativos/Operaciones.txt')
	if not ListaOperaciones: return

	#Trading real
	pendientes = '' #string
	for z in reversed(ListaOperaciones): pendientes = pendientes+z+','
	if pendientes.endswith(','): pendientes = pendientes[0:len(pendientes)-1]
	try: Trades = Llave(CuentaLBTC).call('GET','/api/contact_info/',{'contacts':pendientes}).json() #diccionario
	except:	return

	#Carga operaciones
	closed_at = nested_lookup('closed_at',Trades) #lista
	if not closed_at: return

	released_at = nested_lookup('released_at',Trades)
	amount = nested_lookup('amount',Trades)
	name = nested_lookup('name',Trades)
	username = nested_lookup('username',Trades)
	trade_type = nested_lookup('trade_type',Trades)
	payment_completed_at = nested_lookup('payment_completed_at',Trades)
	currency = nested_lookup('currency',Trades)
	payment_method = nested_lookup('payment_method',Trades)
	contact_id = nested_lookup('contact_id',Trades)
	created_at = nested_lookup('created_at',Trades)

	#Acciona según el estado de cada operación
	ListaOperacionesPagadas = LeerArchivoCrearLista('ArchivosOperativos/OperacionesPagadas.txt')
	if not ListaOperacionesPagadas: ListaOperacionesPagadas = ['']
	for x in range(len(contact_id)):
			contacto = str(contact_id[x]); ContactoCorto = contacto[len(contacto)-4:len(contacto)]

			#OPERACION ABIERTA
			if not closed_at[x]:
				#OPERACION PAGADA
				if payment_completed_at[x]:
					if contacto in ListaOperacionesPagadas: continue
					Archivador('ArchivosOperativos/OperacionesPagadas.txt',contacto)
					cadena = ContactoCorto + ' $' + str(amount[x]) + '. Pagada'
					EnviarTelegram(cadena)
				continue

			#OPERACION CERRADA
			else:
				#Busco el nombre de usuario de la operación
				name1 = []
				for y in name:
					if CuentaLBTC in y: continue
					name1.append(y)
				username1 = []
				for y in username:
					if CuentaLBTC in y: continue
					username1.append(y)

				#Determino si tengo operaciones previas con este usuario
				UsernameInfo = LocalCall('/api/account_info/' + username1[x] + '/',CuentaLBTC)
				try: UsernameInfo['data']
				except:
					print('No se pudo obtener feedback!')
					continue
				try: has_feedback = nested_lookup('has_feedback',UsernameInfo)[0]
				except:
					print('No se pudo obtener feedback!')
					continue

				#La operación ha concluido y se elimina de los archivos
				Desarchivador('ArchivosOperativos/Operaciones.txt',contacto)
				global MarketName,market1,market2,market3,NumAviso,EcuacionPrecio

				#OPERACION CANCELADA
				if not released_at[x]:
					#Deja feedback
					if not has_feedback:
						if CuentaLBTC=='Saldo1': parametros = {'feedback':'neutral','msg':'SALDO 1'}
						if CuentaLBTC=='MAVE45': parametros = {'feedback':'neutral','msg':'MAVE45'}
						calltxt = '/api/feedback/'+username1[x]+'/'
						try: print(Llave(CuentaLBTC).call('POST',calltxt,parametros).json()['data']['message'])
						except: cadena = ContactoCorto+' $'+str(amount[x])+', error al calificar!'
						else: cadena = ContactoCorto+' $'+str(amount[x])+'. Cancelada. No existía calificación previa. Calificada neutral'
					else:
						my_feedback = nested_lookup('my_feedback',UsernameInfo)[0]
						cadena = ContactoCorto+' $'+str(amount[x])+'. Cancelada. Calificación previa '+my_feedback+'. No se modificó la calificación'
					EnviarTelegram(cadena)

					#-----------REESTABLEZCO IMPORTE POR CANCELACIÓN-------------
					#Busco titular correspondiente a la operación activa en OperacionesTitulares.txt
					OperacionesTitulares = LeerArchivoCrearLista('ArchivosOperativos/OperacionesTitulares.txt')
					Titular_N = ''
					for OperacionTitular in OperacionesTitulares:
						if contacto in OperacionTitular:
							ListaInfo = OperacionTitular.rsplit('#') #   contacto#titular#CuentaLocal#MarketName
							Titular_N = ListaInfo[1]
							CuentaLocal = ListaInfo[2]
							MarketName = ListaInfo[3]
							break
					if not Titular_N: continue

					#Lee archivo Importes
					with open('ArchivosOperativos/'+CuentaLBTC+'_'+MarketName+'_Importes.txt') as f:
						cuentas = f.readlines()
						f.close()

					#Determina la cuenta en la que reestablecer la operación cancelada
					Amount_N = ''
					if currency[x]=='ARS':
						z = 0
						for y in cuentas:
							if Titular_N in y:
								Amount_N = cuentas[z+3].replace('$','')
								break
							z += 1
					else:
						importes = []
						for y in cuentas:
							if '$' in y and not y.isupper():
							  z = y.replace('$','')
							  importes.append(int(z))
						Amount_N = str(importes[1])
					if not Amount_N: continue

					#Modifico arhivo cuentas
					nuevo_importe = '$'+str(int(Amount_N)+int(float(amount[x])))
					importe_a_buscar = '$'+str(Amount_N)
					importe_a_buscar = importe_a_buscar.replace('\n','')
					# ~ ListaArchivo = LeerArchivoCrearLista('ArchivosOperativos/Importes'+MarketName+'.txt')
					ListaArchivo = LeerArchivoCrearLista('ArchivosOperativos/'+CuentaLBTC+'_'+MarketName+'_Importes.txt')
					for y in range(len(ListaArchivo)):
						if ListaArchivo[y]==importe_a_buscar:
							ListaArchivo[y] = nuevo_importe
							break
					with open('ArchivosOperativos/'+CuentaLBTC+'_'+MarketName+'_Importes.txt','w') as f:
						for item in ListaArchivo:
							item = item+'\n'
							f.write('%s' %item)

					#Se elimina entrada de archivo OperacionesTitulares.txt
					for OperacionTitular in OperacionesTitulares:
						if str(contact_id[x]) in OperacionTitular:
							Desarchivador('ArchivosOperativos/OperacionesTitulares.txt',OperacionTitular)
							OperacionesTitulares.remove(OperacionTitular)
							break

					#Se elimina entrada de archivo Emails.txt
					EmailsOperacionesActivas = LeerArchivoCrearLista('ArchivosOperativos/Emails.txt')
					if EmailsOperacionesActivas:
						for y in EmailsOperacionesActivas:
							if str(contact_id[x]) in y:
								Desarchivador('ArchivosOperativos/Emails.txt',y)
								break

					#Determina nuevos mínimo y máximo después de la oferta, modifica y posiciona aviso
					market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(MarketName,CuentaLBTC)
					SelectorMinimoMaximo(MarketName,CuentaLBTC)
				#-------------------------------------------------
				#OPERACION LIBERADA
				else:
					#No hay calificación previa
					if not has_feedback:
						#Feedback
						if CuentaLBTC=='Saldo1':
							if currency[x]=='ARS': parametros = {'feedback':'trust','msg':'Impecable! SALDO 1'}
							if currency[x]=='USD': parametros = {'feedback':'trust','msg':'Awesome! SALDO 1'}
						if CuentaLBTC=='MAVE45':
							if currency[x]=='ARS': parametros = {'feedback':'trust','msg':'Impecable! MAVE45'}
							if currency[x]=='USD': parametros = {'feedback':'trust','msg':'Awesome! MAVE45'}

						#Intenta calificar
						calltxt = '/api/feedback/'+username1[x]+'/'
						for m in range(5):
							try: print(Llave(CuentaLBTC).call('POST',calltxt,parametros).json()['data']['message'])
							except:
								time.sleep(5)
								continue
							else:
								cadena = ContactoCorto+' $'+str(amount[x])+'. No existía calificación previa. Calificada trust!'
								EnviarTelegram(cadena)
								break

						#No se calificó
						if m==4:
							cadena = ContactoCorto+' $'+str(amount[x])+'Error al calificar!'
							EnviarTelegram(cadena)

						#mensaje final
						if currency[x]=='ARS': parametros = {'msg':'Calificado Confiable!'}
						if currency[x]=='USD': parametros = {'msg':'Trustworthy. Positive feedback'}
						calltxt = '/api/contact_message_post/'+contacto+'/'
						try: print(Llave(CuentaLBTC).call('POST',calltxt,parametros).json()['data']['message'])
						except: pass

					#Hay calificación previa positiva
					else:
						#mensaje final
						if currency[x]=='ARS': parametros = {'msg':'Confiable. Gracias por esta nueva operación'}
						if currency[x]=='USD': parametros = {'msg':'Always trustworthy.Thanks for this new trade'}
						calltxt = '/api/contact_message_post/'+contacto+'/'
						try: print(Llave(CuentaLBTC).call('POST',calltxt,parametros).json()['data']['message'])
						except: pass

						#Comunico
						cadena = ContactoCorto+' $'+str(amount[x])+'. Existía calificación previa trust!'
						EnviarTelegram(cadena)

					#Buscás el mercado correspondiente al contacto
					OperacionesTitulares = LeerArchivoCrearLista('ArchivosOperativos/OperacionesTitulares.txt')
					for OperacionTitular in OperacionesTitulares:
						if contacto in OperacionTitular:
							ListaInfo = OperacionTitular.rsplit('#') #   OperacionesTitulares = contacto#titular#CuentaLocal#MarketName
							CuentaLocal = ListaInfo[2]
							MarketName = ListaInfo[3]

					#Cierro bot si el aviso no está activo
					market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(MarketName,CuentaLocal)
					TuAviso = LocalCall('/api/ad-get/'+NumAviso+'/',CuentaLBTC,m=3)
					try: visible = nested_lookup('visible',TuAviso)[0]
					except:	visible = False
					if not visible:
						TodoPids = LeerArchivoCrearLista('ArchivosOperativos/PidsMercados.txt')
						if TodoPids:
							for Pid in TodoPids:
								ListaInfo = Pid.rsplit('#') #   PidsMercados = pid#CuentaLocal#MarketName
								CuentaLocalPid = ListaInfo[1]
								MarketNamePid = ListaInfo[2]
								if CuentaLocalPid==CuentaLocal and MarketNamePid==MarketName:
									IntPid = int(Pid[0:Pid.index('#')])
									try: os.kill(IntPid,signal.SIGTERM)
									except: print(CuentaLocal+' '+MarketName+' no pudo ser cerrado')
									else:
										cadena = CuentaLocal+' '+MarketName+' desactivado!'
										EnviarTelegram(cadena)
						EliminaPidsInactivos('PidsMercados')

					#Depuro archivos antes de verificar cierre de bot
					Depurador()

					#Binance balanceo posición
					BinancePosition()

					#Actualizo Dashboard
					Dashboard(CuentaLocal)

#*************************************************
def LocalbitcoinsListener(CuentaLBTC):
	#Levanta mensajes de últimos 5 minutos
	global Savedcreated_at

	parametros = {'after':datetime.utcnow()-timedelta(minutes=5)}
	try: mensajes = Llave(CuentaLBTC).call('GET','/api/recent_messages/',parametros).json()
	except:	return

	#Hay mensajes en los últimos 5 minutos?
	created_at = nested_lookup('created_at',mensajes)
	if not created_at:	return
	mensajes = mensajes['data']['message_list']

	#Busca mensajes/imagenes nuevas de terceros
	created_at,msg,attachment_name,contact_id,attachment_url = [],[],[],[],[]
	for x in range(len(mensajes)):
		if nested_lookup('username',mensajes[x])[0] != CuentaLBTC:
			created_at.append(nested_lookup('created_at',mensajes[x])[0])
			msg.append(nested_lookup('msg',mensajes[x])[0])
			contact_id.append(nested_lookup('contact_id',mensajes[x])[0])

			try: y = nested_lookup('attachment_name',mensajes[x])[0]
			except: attachment_name.append('')
			else:
				attachment_name.append(y)
				attachment_url.append(nested_lookup('attachment_url',mensajes[x])[0])

	if not msg and not attachment_name: return

	#Verifica si el mensaje se comunicó
	Savedcreated_atTimeFormat = datetime.fromisoformat(Savedcreated_at) #convierto string en fecha
	NuevoMensaje = False
	for x in range(len(created_at)-1,-1,-1):
		created_atTimeFormat = datetime.fromisoformat(created_at[x])
		if created_atTimeFormat <= Savedcreated_atTimeFormat: continue

		#Registra momento de creación del nuevo mensaje
		f = open('ArchivosOperativos/MensajeLBTC.txt','r')
		f.read().replace(Savedcreated_at,'')
		Savedcreated_at = created_at[x]
		f = open('ArchivosOperativos/MensajeLBTC.txt','w')
		f.write(Savedcreated_at)
		f.close()
		time.sleep(0.5)

		#Información del mensaje en LBTC
		contacto = str(contact_id[x]); ContactoCorto = contacto[len(contacto)-4:len(contacto)]
		try: Trade = Llave(CuentaLBTC).call('GET','/api/contact_info/'+contacto+'/').json()
		except:	continue
		amount = nested_lookup('amount',Trade)[0]
		currency = nested_lookup('currency',Trade)[0]
		payment_method = nested_lookup('payment_method',Trade)[0]
		trade_type = nested_lookup('trade_type',Trade)[0]
		payment_completed_at = nested_lookup('payment_completed_at',Trade)[0]
		released_at = nested_lookup('released_at',Trade)[0]
		bot = telepot.Bot(token)

		#Imagen
		if attachment_name[x]:
			print('Attachment_name',attachment_name)
			#Descargo Imagen a disco
			URLbackup = attachment_url[x].index('com')+3
			URL = attachment_url[x][URLbackup:len(attachment_url[x])]
			myfile = Llave(CuentaLBTC).call('GET',URL)
			mypath = 'ArchivosOperativos/ImagenesRecibidas/' + contacto + attachment_name[x]
			print('mypath',mypath)
			print('myfile',myfile)
			for w in range(10):
				try: print(open(mypath,'wb').write(myfile.content))
				except: continue
				else: break

			#Subo imagen a Telegram
			SubirFoto = open(mypath,'rb')
			SubirFoto.close
			cadena = ContactoCorto + ' (' + contacto + '). $' + str(int(float(amount)))
			try: bot.sendPhoto(alias,SubirFoto,cadena)
			except: pass
			SubirFoto = open(mypath,'rb')
			SubirFoto.close
			try: bot.sendPhoto(aliasAugu,SubirFoto,cadena)
			except: pass

			#Recuerdo enviar imagen por email
			if currency=='ARS'and not released_at:
				calltxt = '/api/contact_message_post/'+str(contact_id[x])+'/'
				if CuentaLBTC=='MAVE45': parametros = {'msg':'Gracias, te recordamos enviar comprobante a ventas2722@gmail.com y liberamos en minutos. El proceso es automático.'}
				if CuentaLBTC=='Saldo1': parametros = {'msg':'Gracias, te recordamos enviar comprobante a saldo.1.argentina@gmail.com y liberamos en minutos. El proceso es automático.'}
				for m in range(10):
					try: print(Llave(CuentaLBTC).call('POST',calltxt,parametros).json()['data']['message'])
					except:
						time.sleep(1)
						continue
					else: break

			#Enviaron una foto mientras espero verificación, asumo que es un ID y marco la contraparte como identificada
			if trade_type=='ONLINE_SELL' and currency=='USD' and not payment_completed_at:
				#Identifica contraparte
				calltxt = '/api/contact_mark_identified/' + contacto + '/'
				for m in range(5):
					try: print(Llave(CuentaLBTC).call('POST',calltxt).json()['data']['message'])
					except:
						time.sleep(1)
						continue
					else:
						cadena = ContactoCorto + ' $'+str(int(float(amount))) + '. Contraparte identificada'
						EnviarTelegram(cadena)
						break

				#Envia mensaje a contraparte autorizando a transferir
				calltxt = '/api/contact_message_post/' + contacto + '/'
				parametros = {'msg':'Thanks'}
				for m in range(3):
					try: print(Llave(CuentaLBTC).call('POST',calltxt,parametros).json()['data']['message'])
					except:
						time.sleep(1)
						continue
					else: break

		#Texto
		if msg[x]:
			cadena = ContactoCorto + ' (' + contacto + '). $'+str(int(float(amount))) + ': '+msg[x]
			EnviarTelegram(cadena)
#*************************************************
def EliminaPidsInactivos(PidTipo):
	#Elimina Pids inactivos de txt
	ArchivoPids = 'ArchivosOperativos/'+PidTipo+'.txt'
	TodoPids = LeerArchivoCrearLista(ArchivoPids)
	if TodoPids:
		for z in TodoPids:
			#Separo Pid del resto de la info
			IntPid = int(z[0:z.index('#')])
			if not psutil.pid_exists(IntPid):
				#Se elimina pids inactivos del archivo de pids.txt
				cadena = z+'\n'
				for line in fileinput.input(ArchivoPids, inplace=1):
					try: line = line.replace(cadena,'')
					except: continue
					try: line = line.replace(z,'')
					except: continue
					sys.stdout.write(line)

	#Busca Pid activo
	try: f = open(ArchivoPids,'r')
	except: return '1'
	else:
		Pids = f.readline() #str
		f.close()
		Pids = Pids.replace('\n','')
		if Pids:
			PidActivos = Pids[0:Pids.index('#')]
			if not PidActivos: return '1'
			return PidActivos
	return '1'
#*************************************************
#Define variables globales
alias = 701549748 #Lo obtenés en el chat IDBot de Telegram
token = '910296400:AAHRkd76QujDh8qnASbjEJv5kEc5DdAioco'  #Lo obtenés en el chat BotFather de Telegram
aliasAugu = 1684836450
tokenAugu = '1857137625:AAExcInbDRZcUpEu9Wj01YMFrNfwkz_9pCs'
EsperaEmail = False

#Inicia bot/servidor desde otro bot o PC
try: bool(sys.argv[1])

#Desde PC
except:
	MarketName,activacion,CuentaLocal = MercadoOperaciones()
	TelegramProximoID = 0
	lanzador = 'pc'

	#Servidor lanzado desde PC
	if MarketName=='Servidor':
		print('Servidor lanzado por humano!')

		#Si hay un servidor abierto, lo cierro para que quede solamente uno activo
		PidActivos = EliminaPidsInactivos('PidServidor')
		if PidActivos:
			if psutil.pid_exists(int(PidActivos)):
				os.kill(int(PidActivos), signal.SIGTERM)
				PidActivos = EliminaPidsInactivos('PidServidor')
		cadena = str(os.getpid())+'#Servidor'
		Archivador('ArchivosOperativos/PidServidor.txt',cadena)

		#Archivos de trabajo
		operaciones,Savedcreated_at = ArchivosTrabajo('Servidor') #list,str,str
		while('' in operaciones) : operaciones.remove('')
		LoopControl(operaciones)

	#Bot lanzado desde PC
	else:
		##Obtengo datos de mercado
		market1,market2,market3,NumAviso,EcuacionPrecio,BitstampRelation1,MarketName = DatosMercado(MarketName,CuentaLocal,'Inicio',activacion)
		try: Llave(CuentaLocal).call('POST','/api/ad-equation/'+NumAviso+'/',params={'price_equation': EcuacionPrecio+'*'+str(BitstampRelation1)}).json()['data']['message']
		except: pass

		#Archivos de trabajo
		operaciones,Savedcreated_at = ArchivosTrabajo(MarketName,CuentaLocal) #list,str,str
		while('' in operaciones) : operaciones.remove('')
		Relation = MarketRelation(MarketName,market1,EcuacionPrecio,CuentaLocal)

		if activacion == 'Activar':
			#Modifico archivo BitstampRelation1
			f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation1.txt','w')
			f.write(str(BitstampRelation1))
			f.close()
			#Presento mercado
			PresentaAvisosTerceros(MarketName,CuentaLocal,lanzador,Relation)
			BitstampRelation1,BitstampRelation2,TelegramProximoID = DatosIniciales(MarketName,lanzador,TelegramProximoID,CuentaLocal)

		if activacion == 'Reactivar':
			#Leo archivo BitstampRelation1
			f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation1.txt','r')
			BitstampRelation1 = round(float(f.read()),4)
			f.close()
			#Leo archivo BitstampRelation2
			f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation2.txt','r')
			BitstampRelation2 = round(float(f.read()),4)
			f.close()

#Desde BOT
else:
	#Servidor lanzado desde BOT
	if str(sys.argv[1])=='Servidor':
		MarketName='Servidor'
		TelegramProximoID = 0
		print('Servidor lanzado desde Bot!')

		#Lee PidServidor y lo registra
		EliminaPidsInactivos('PidServidor')
		cadena = str(os.getpid())+'#Servidor'
		Archivador('ArchivosOperativos/PidServidor.txt',cadena)

		#Archivos de trabajo
		operaciones,Savedcreated_at = ArchivosTrabajo('Servidor') #list,str,str
		while('' in operaciones) : operaciones.remove('')
		LoopControl(operaciones)

	#Bot lanzado desde BOT
	else:
		MarketName = sys.argv[1]
		TelegramProximoID = int(sys.argv[2])
		print('Bot lanzado desde Bot!')
		lanzador = 'telegram'
		if sys.argv[3] == 'activa': activacion = 'Activar'
		else: activacion = 'Reactivar'
		CuentaLocal = sys.argv[4]

		##Obtengo datos de mercado
		market1,market2,market3,NumAviso,EcuacionPrecio,BitstampRelation1,MarketName = DatosMercado(MarketName,CuentaLocal,'Inicio',activacion)
		try: Llave(CuentaLocal).call('POST','/api/ad-equation/'+NumAviso+'/',params={'price_equation': EcuacionPrecio+'*'+str(BitstampRelation1)}).json()['data']['message']
		except: pass

		#Archivos de trabajo
		operaciones,Savedcreated_at = ArchivosTrabajo(MarketName,CuentaLocal) #list,str,str
		while('' in operaciones) : operaciones.remove('')
		Relation = MarketRelation(MarketName,market1,EcuacionPrecio,CuentaLocal)

		if activacion == 'Activar':
			PresentaAvisosTerceros(MarketName,CuentaLocal,lanzador,Relation)
			BitstampRelation1,BitstampRelation2,TelegramProximoID = DatosIniciales(MarketName,lanzador,TelegramProximoID,CuentaLocal)
		if activacion == 'Reactivar':
			#Leo archivo BitstampRelation1
			f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation1.txt','r')
			BitstampRelation1 = round(float(f.read()),4)
			f.close()
			#Leo archivo BitstampRelation2
			f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation2.txt','r')
			BitstampRelation2 = round(float(f.read()),4)
			f.close()

#************PIDS  MERCADO************
#Desactiva bots de mercado activos iguales
TodoPids = LeerArchivoCrearLista('ArchivosOperativos/PidsMercados.txt')
if TodoPids:
	for pids in TodoPids:
		ListaInfo = pids.rsplit('#')
		IntPid = ListaInfo[0]; CuentaLocalPid = ListaInfo[1]; MarketPid = ListaInfo[2]
		if MarketPid==MarketName and CuentaLocalPid==CuentaLocal: os.kill(int(IntPid),signal.SIGTERM)
#Elimina pids no usados
EliminaPidsInactivos('PidsMercados')
#Registra pid de nuevo bot de mercado
cadena = str(os.getpid())+'#'+CuentaLocal+'#'+MarketName
Archivador('ArchivosOperativos/PidsMercados.txt',cadena)

#Si no hay Servidor activo, se crea uno
PidActivos = EliminaPidsInactivos('PidServidor')
if PidActivos:
	if not psutil.pid_exists(int(PidActivos)):
		Servidor = Popen([sys.executable,'bot.py','Servidor','activa'], creationflags=CREATE_NEW_CONSOLE)

#Activa aviso y establece máximo y mínimo de aviso
SelectorMinimoMaximo(MarketName,CuentaLocal)
if lanzador == 'telegram':
	cadena = MarketName+' aviso activo!'
	EnviarTelegram(cadena)

#Inicia loop de control
dash,espera = '',5
LoopControl(operaciones)
