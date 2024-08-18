import json, time, sys, platform, os, re, fileinput, requests, threading, ast
from Binance import *
from Tickets.Soldout_module import *
from telegram import *
from trading import *
from datetime import datetime #Obtiene fecha y hora en formato humano
from lbcapi3 import api #api de Localbitcoins para Python 3
from nested_lookup import nested_lookup #extrae valor de listas y bibliotecas anidadas
import telepot,telebot #envía mensajes a Telegram
alias = youralias
token = yourtoken
bot = telepot.Bot(token)
bot2 = telepot.Bot(tokenAugu)
#*************************************************
def PrimeraRespuesta(MarketName1,dash1,operaciones1,EsperaEmail1,CuentaLocal1):
	#Variables
	from Tickets.Soldout_module import DatosMercado,EnviarTelegram,Llave,Archivador
	global dash,operaciones,EsperaEmail,contacto,amount,MarketName,CuentaLocal
	dash = dash1; operaciones = operaciones1; EsperaEmail = EsperaEmail1; CuentaLocal = CuentaLocal1

	#Datos mercado
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(MarketName1,CuentaLocal)

	#Loop asincrónico
	SalirPrimeraRespuesta = True
	if MarketName=='Transfe' or MarketName=='Transfe2' or MarketName=='Depo': SalirPrimeraRespuesta = False

	while True:
		#Leo Dashboard
		cadena = 'ArchivosOperativos/Dashboard_'+CuentaLocal+'.txt'
		try: f = open(cadena,'r')
		except:
			if SalirPrimeraRespuesta: return dash,operaciones,EsperaEmail
			continue
		dash = f.read()
		f.close()
		try: dash = json.loads(dash)
		except:
			if SalirPrimeraRespuesta: return dash,operaciones,EsperaEmail
			continue

		#Busca errores en el dash
		error = nested_lookup('error',dash)
		if error: continue

		#No hay errores y procede
		contact_count = dash['data']['contact_count']
		if contact_count==0:
			if SalirPrimeraRespuesta: return dash,operaciones,EsperaEmail
			time.sleep(15)
			continue

		#Loop Primera Respuesta
		contact_id = nested_lookup('contact_id',dash)
		ID = nested_lookup('id',dash) #Nro de aviso (Paypal, Transferencia, MercadoPago, etc.)
		e = 0 #Contador email Paypal

		#Loop para revisar operaciones abiertas
		for y in range(len(contact_id)):
			#Datos
			contacto = str(contact_id[y])
			AvisoNuevaOferta = str(ID[y])
			amount =  round(float(nested_lookup('amount',dash)[y]),2)

			#Verifico si el contacto ya se registró
			if contacto in operaciones:

				#Nuevo contacto en Paypal
				if AvisoNuevaOferta==NumAviso and MarketName=='Paypal': e += 1

				#Estoy esperando el email
				if EsperaEmail:
					#Intentás detectar email para el pago
					email = DetectaEmail()
					if email:
						SegundaRespuesta(email)
						EsperaEmail = False
				continue

			#Nuevo aviso, no di respuesta
			advertiser = nested_lookup('advertiser',dash)[y]['username']
			name1 = nested_lookup('name',dash)
			username1 = nested_lookup('username',dash)
			name=[]; username=[]
			for x in name1:
				if CuentaLocal in x: continue
				name.append(x)
				username.append(x)

			#PUBLICACION TERCERO SELL
			if advertiser!=CuentaLocal and (MarketName=='Transfe' or MarketName=='Transfe2'):
				#Registra nueva operación en archivo y en lista
				operaciones.append(contacto)
				Archivador('ArchivosOperativos/Operaciones.txt',contacto) #Registra en archivo la nueva operación
				payment_method = nested_lookup('advertisement',dash)[y]['payment_method']
				if payment_method=='NATIONAL_BANK':
					#Envía mensaje con instrucciones
					CuentaBancaria,CuentaBancariaMensaje = SelectorCuentas(int(amount),contacto,MarketName,CuentaLocal)
					if CuentaLocal=='MAVE45': Titulo = '\nEnviar con concepto VARIOS y dejar referencia en blanco o poner VARIOS, sin ninguna mención a bitcoin o Local. Por favor enviar comprobante a ventas2722@gmail.com para liberación instantanea.\n\n'
					if CuentaLocal=='Saldo1': Titulo = '\nEnviar con concepto VARIOS y dejar referencia en blanco o poner VARIOS, sin ninguna mención a bitcoin o Local. Por favor enviar comprobante a saldo.1.argentina@gmail.com para liberación instantanea.\n\n'
					mensaje = Titulo+CuentaBancaria
					parametros = {'msg':mensaje}
					calltxt = '/api/contact_message_post/'+contacto+'/'
					for m in range(10):
						try: print(Llave(CuentaLocal).call('POST',calltxt,parametros).json()['data']['message'])
						except:
							time.sleep(1)
							continue
						else: break
					#Envía mensaje a Telegram
					ContactoCorto = contacto[len(contacto)-4:len(contacto)]
					TraderName = name[y]
					cadena = CuentaLocal+' '+MarketName+'\nContacto: '+ContactoCorto+' ('+contacto+'). Importe: '+str(amount)+'.\n'+TraderName+'\n'+CuentaBancariaMensaje
					EnviarTelegram(cadena)
				continue

			#Vender bitcoins por pesos en Argentina
			if AvisoNuevaOferta==NumAviso and (MarketName=='Transfe' or MarketName=='Transfe2' or MarketName=='Depo'):
				VenderArgentina(name[y])
				continue

			#Comprar bitcoins
			if AvisoNuevaOferta==NumAviso and (MarketName=='Paypal' or MarketName=='Payoneer' or MarketName=='Paxum' or MarketName=='Skrillcompra' or MarketName=='Netellercompra' or MarketName=='Zellecompra' or MarketName=='Wise'):
				if MarketName=='Paypal':
					email = nested_lookup('receiver_email',dash)[e]
					e += 1
					ComprarBTC(name[y],email)
				else: ComprarBTC(name[y])
				continue

			#Vender bitcoins
			if AvisoNuevaOferta==NumAviso and (MarketName=='Skrillventa' or MarketName=='Netellerventa' or MarketName=='Zelleventa'):
				VenderBTC(name[y])
				continue

		if SalirPrimeraRespuesta: return dash,operaciones,EsperaEmail
#*************************************************
def ComprarBTC(TraderName,email=''):
	#Variables
	from Tickets.Soldout_module import EnviarTelegram,Llave,Archivador,LocalCall
	from trading import SelectorImportes
	global EsperaEmail

	#Modifica Importes
	SelectorImportes(int(amount),contacto,MarketName,CuentaLocal)

	#Envía mensaje inicial a Telegram
	ContactoCorto = contacto[len(contacto)-4:len(contacto)]
	telegrama0 = MarketName+'. Contacto: '+ContactoCorto+' ('+contacto+'). Importe: '+str(amount)+'. '+TraderName; EnviarTelegram(telegrama0)

	#Registra nueva operación en archivo y en lista
	operaciones.append(contacto)
	Archivador('ArchivosOperativos/Operaciones.txt',contacto)

	#Verificás si informaron el email
	if not email and MarketName!='Wise':
		#Detecta email para el pago
		email = DetectaEmail()

		if not email:
			#Pedís email
			mensaje = '\nPlease let us have your email for payment.'
			parametros = {'msg':mensaje}
			calltxt = '/api/contact_message_post/'+contacto+'/'
			for m in range(10):
				try: print(Llave(CuentaLocal).call('POST',calltxt,parametros).json()['data']['message'])
				except:
					time.sleep(1)
					continue
				else: break
			EsperaEmail = True
			return

	#Comunico la nueva operación
	SegundaRespuesta(email)
#*************************************************
def DetectaEmail():
	BuscarEmail = LocalCall('/api/contact_messages/'+contacto+'/',CuentaLocal)
	if not BuscarEmail: return
	email = ''
	msg = nested_lookup('msg',BuscarEmail)
	for x in range(len(msg)):
		z = re.findall('([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)',msg[x])
		if z:
			email = z[0]
			break
	return email
#*************************************************
def SegundaRespuesta(email):
	#Se informó el email, envías segunda respuesta
	mensaje = '\nThank you. A computer program is processing this trade automatically, which will mark payment as made from the beginning. You will receive it as soon as possible. You release once money is credited to your account.'
	if MarketName=='Paypal': mensaje = mensaje + '\n\nPlease be aware that Paypal will charge its commission. 4% approximately. You will not have the full amount. We are paying an over-price of bitcoin price to partially offset this difference'
	parametros = {'msg':mensaje}
	calltxt = '/api/contact_message_post/'+contacto+'/'
	for m in range(10):
		try: print(Llave(CuentaLocal).call('POST',calltxt,parametros).json()['data']['message'])
		except:
			time.sleep(1)
			continue
		else: break

	#Registrás Email en archivo
	cadena = contacto+'#'+email+'#'+MarketName
	Archivador('ArchivosOperativos/Emails.txt',cadena)

	if MarketName=='Skrillcompra' or MarketName=='Netellercompra':
		telegrama1 = email; EnviarTelegram(telegrama1)

	if MarketName=='Paxum' or MarketName=='Payoneer' or MarketName=='Paypal' or MarketName=='Wise':
		telegrama1 = 'Podés enviar ahora? Hay un pedido en '+MarketName+' de '+str(int(amount)); telegrama2 = email
		EnviarTelegram(telegrama1); EnviarTelegram(telegrama2)

	#marcar pagado
	calltxt = '/api/contact_mark_as_paid/'+contacto+'/'
	try: print(Llave(CuentaLocal).call('POST',calltxt).json()['data']['message'])
	except: pass
#*************************************************
def VenderBTC(TraderName):
	#Variables
	from Tickets.Soldout_module import EnviarTelegram,Llave,Archivador
	from trading import SelectorImportes

	#Modifica txt
	SelectorImportes(int(amount),contacto,MarketName,CuentaLocal)

	#Registra nueva operación en archivo y en lista
	operaciones.append(contacto)
	Archivador('ArchivosOperativos/Operaciones.txt',contacto)

	#Envía Primera Respuesta
	mensaje = '\nThank you for your contact.\n\nPlease send clear photo of any ID provided that you do not have trade with us before.\n\nID name must match name on your account and LBC account. We do not accept third-party payments.\n\nOnce your ID is verified, payment information will be available.'
	ContactoCorto = contacto[len(contacto)-4:len(contacto)]
	telegrama1 = MarketName+'. Contacto: '+ContactoCorto+' ('+contacto+'). Importe: '+str(amount)+'. '+TraderName
	parametros = {'msg':mensaje}
	calltxt = '/api/contact_message_post/'+contacto+'/'
	for m in range(10):
		try: print(Llave(CuentaLocal).call('POST',calltxt,parametros).json()['data']['message'])
		except:
			time.sleep(1)
			continue
		else: break

	#Envía mensaje a Telegram
	EnviarTelegram(telegrama1)
#*************************************************
def VenderArgentina(TraderName):
	#Variables
	from Tickets.Soldout_module import EnviarTelegram,Llave,Archivador
	from trading import SelectorCuentas,SelectorMinimoMaximo

	#Registra nueva operación en archivo y en lista
	operaciones.append(contacto)
	Archivador('ArchivosOperativos/Operaciones.txt',contacto) #Registra en archivo la nueva operación

	#Selecciona cuenta
	CuentaBancaria,CuentaBancariaMensaje = SelectorCuentas(int(amount),contacto,MarketName,CuentaLocal)
	ContactoCorto = contacto[len(contacto)-4:len(contacto)]
	if not CuentaBancaria:
		mensaje = '\nGracias por el contacto. El aviso quedó activo, pero no podemos recibir un pago por el importe de esta operción. Por favor cancelar.'
		telegrama1 = 'Nueva Operación, Sin fondos, van a cancelar! '+CuentaLocal+' '+MarketName+'. Contacto: '+ContactoCorto+' ('+contacto+'). Importe: '+str(amount)+'\n'+TraderName
	else:
		if CuentaLocal=='MAVE45':
			# ~ if MarketName=='Transfe' or MarketName=='Transfe2': Titulo = '\nGracias por el contacto.\n\nPor favor enviar con concepto VARIOS y dejar referencia en blanco o poner VARIOS, sin ninguna mención a bitcoin o Local.\n\n'
			# ~ if MarketName=='Depo': Titulo = '\nGracias por el contacto.\n\n'
			if MarketName=='Transfe' or MarketName=='Transfe2': Titulo = '\nGracias por el contacto.\n\nPor favor enviar con concepto VARIOS y dejar referencia en blanco o poner VARIOS, sin ninguna mención a bitcoin o Local. Un progrma de computadora va a procesar esta operación automáticamente en minutos. Por favor enviar comprobante a ventas2722@gmail.com para liberación instantanea.\n\n'
			if MarketName=='Depo': Titulo = '\nGracias por el contacto. Un progrma de computadora va a procesar esta operación automáticamente en minutos. Por favor enviar comprobante a ventas2722@gmail.com para liberación instantanea.\n\n'
		if CuentaLocal=='Saldo1':
			if MarketName=='Transfe' or MarketName=='Transfe2': Titulo = '\nGracias por el contacto.\n\nPor favor enviar con concepto VARIOS y dejar referencia en blanco o poner VARIOS, sin ninguna mención a bitcoin o Local. Un progrma de computadora va a procesar esta operación automáticamente en minutos. Por favor enviar comprobante a saldo.1.argentina@gmail.com para liberación instantanea.\n\n'
			if MarketName=='Depo': Titulo = '\nGracias por el contacto. Un progrma de computadora va a procesar esta operación automáticamente en minutos. Por favor enviar comprobante a saldo.1.argentina@gmail.com para liberación instantanea.\n\n'
		mensaje = Titulo+CuentaBancaria
		telegrama1 = CuentaLocal+' '+MarketName+'\nContacto: '+ContactoCorto+' ('+contacto+'). Importe: '+str(amount)+'\n'+TraderName+'\n'+CuentaBancariaMensaje

	#Envía Primera Respuesta
	parametros = {'msg':mensaje}
	calltxt = '/api/contact_message_post/'+contacto+'/'
	for m in range(10):
		try: print(Llave(CuentaLocal).call('POST',calltxt,parametros).json()['data']['message'])
		except:
			time.sleep(1)
			continue
		else: break

	#Envía mensaje a Telegram
	EnviarTelegram(telegrama1)
#*************************************************
