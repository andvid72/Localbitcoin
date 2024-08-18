import json,time,sys,platform,os.path,re,fileinput,requests,os,signal,threading, psutil, signal
from Binance import *
from Tickets.Soldout_module import *
from telegram import *
from subprocess import Popen, CREATE_NEW_CONSOLE
from datetime import datetime,timedelta #Obtiene fecha y hora en formato humano
from lbcapi3 import api #api de Localbitcoins para Python 3
from nested_lookup import nested_lookup #extrae valor de listas y bibliotecas anidadas
import telepot,telebot #envía mensajes a Telegram
alias = youralias
token = yourtoken
#*************************************************
def PresentaAvisosTerceros(Market,CuentaLocal,DesdeDonde='',Relation=''):
	#variables
	from Tickets.Soldout_module import DatosMercado,Llave,Bitstamp,FiltroQR,EnviarTelegram,MarketRelation,CuentaLocalbitcoins,ObtenerMercado,LocalCall
	global BitstampRelation1,MarketName
	MarketName = Market
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(MarketName,CuentaLocal)
	if not MarketName: return [],[],[],[],[],[],[],[],0

	#Leo archivo BitstampRelation1
	f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation1.txt','r')
	BitstampRelation1 = round(float(f.read()),4)
	f.close()

	#Leo archivo BitstampRelation2
	f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation2.txt','r')
	BitstampRelation2 = round(float(f.read()),4)
	f.close()

	#market1
	AvisosTerceros = ObtenerMercado(market1)
	if not AvisosTerceros: return [],[],[],[],[],[],[],[],0
	name = nested_lookup('name',AvisosTerceros)
	FormaPago = nested_lookup('bank_name',AvisosTerceros)
	precio = nested_lookup('temp_price',AvisosTerceros)
	minimo = nested_lookup('min_amount',AvisosTerceros)
	maximo = nested_lookup('max_amount_available',AvisosTerceros)
	UserName = nested_lookup('username',AvisosTerceros)
	trade_count = nested_lookup('trade_count',AvisosTerceros)
	countrycode = nested_lookup('countrycode',AvisosTerceros)
	CantidadAvisos = int(nested_lookup('ad_count',AvisosTerceros)[0])

	#Mercado adicionales
	if MarketName=='Transfe2' or MarketName =='Transfe' or MarketName =='Paxum':
		if market2:
			AvisosTerceros = ObtenerMercado(market2)
			if not AvisosTerceros: return [],[],[],[],[],[],[],[],0
			name = name+nested_lookup('name',AvisosTerceros)
			FormaPago = FormaPago+nested_lookup('bank_name',AvisosTerceros)
			precio = precio+nested_lookup('temp_price',AvisosTerceros)
			minimo = minimo+nested_lookup('min_amount',AvisosTerceros)
			maximo = maximo+nested_lookup('max_amount_available',AvisosTerceros)
			UserName = UserName+nested_lookup('username',AvisosTerceros)
			trade_count = trade_count+nested_lookup('trade_count',AvisosTerceros)
			CantidadAvisos += int(nested_lookup('ad_count',AvisosTerceros)[0])
		if market3:
			AvisosTerceros = ObtenerMercado(market3)
			if not AvisosTerceros: return [],[],[],[],[],[],[],[],0
			name = name+nested_lookup('name',AvisosTerceros)
			FormaPago = FormaPago+nested_lookup('bank_name',AvisosTerceros)
			precio = precio+nested_lookup('temp_price',AvisosTerceros)
			minimo = minimo+nested_lookup('min_amount',AvisosTerceros)
			maximo = maximo+nested_lookup('max_amount_available',AvisosTerceros)
			UserName = UserName+nested_lookup('username',AvisosTerceros)
			trade_count = trade_count+nested_lookup('trade_count',AvisosTerceros)
			CantidadAvisos += int(nested_lookup('ad_count',AvisosTerceros)[0])

		#Ordena markets, transforma lista de precios en números y los ordena
		for j in range(CantidadAvisos): precio[j] = float(precio[j])
		if MarketName=='Transfe2' or MarketName =='Transfe': precio1 = sorted(precio)
		else: precio1 = sorted(precio, reverse=True)

		#Busca precios repetidos y los separa
		for j in range(CantidadAvisos-1,-1,-1):
			if precio1[j]==precio1[j-1]:
				m = precio.index(precio1[j])
				precio1[j] = precio1[j]+j/100
				precio[m] = precio1[j]

		#Prepara el resto de variables y las modifica según la lista de precios
		name1,FormaPago1,minimo1,maximo1,UserName1,trade_count1 = [],[],[],[],[],[]
		for i in range(CantidadAvisos):
			j = precio.index(precio1[i])
			name1.append(name[j])
			FormaPago1.append(FormaPago[j])
			minimo1.append(minimo[j])
			maximo1.append(maximo[j])
			UserName1.append(UserName[j])
			trade_count1.append(trade_count[j])
	else:
		for j in range(CantidadAvisos): precio[j] = float(precio[j])
		precio1 = precio
		name1 = name
		FormaPago1 = FormaPago
		minimo1 = minimo
		maximo1 = maximo
		UserName1 =UserName
		trade_count1 = trade_count
	#*************************************************
	#Presentar titulo
	def PresentaTitulo(BitstampRelation1,BitstampRelation2,Relation,CuentaLocal,MarketName):
		#Importa funciones
		from Tickets.Soldout_module import BitcoinArgentina

		#Armo titulares
		hora = datetime.now().strftime('%H:%M')
		cadena1 = CuentaLocal.upper() + ' ' + MarketName.upper()+' Hora '+str(hora)
		if MarketName=='Transfe2' or MarketName =='Transfe' or MarketName =='Depo':
			#Calcula precio USDT
			USDstamp = Bitstamp('bitstampusd')
			stamp = Bitstamp(EcuacionPrecio)
			USDT = str(round(stamp*Relation/USDstamp,2))
			cadena3 = ' / Min $'+ str(BitstampRelation1) + ' - Max $'+ str(BitstampRelation2) + ' / Ask-Bid $'+ USDT + '\n'
			cadena4 = 'Precio\tMínimo\tMáximo\tNombre\t\t\tUSDT\n'
		else:
			cadena3 = ' / Max '+ str(round((BitstampRelation1-1)*100,2)) + '% - Min '+ str(round((BitstampRelation2-1)*100,2)) + '% / Ask-Bid '+ str(round((Relation-1)*100,2)) + '%\n'
			cadena4 = 'Precio\tMínimo\tMáximo\tNombre\t\t\tPorcentaje\n'
		cadena = cadena1 + cadena3 + cadena4

		return cadena
	#*************************************************
	if DesdeDonde=='telegram':
		#Busco MarketRelation
		Relation = MarketRelation(MarketName,market1,EcuacionPrecio,CuentaLocal)

		if MarketName=='Transfe2' or MarketName =='Transfe' or MarketName =='Depo':
			#Calcula precio USDT
			USDstamp = Bitstamp('bitstampusd')
			stamp = Bitstamp(EcuacionPrecio)
			USDT = str(round(stamp*Relation/USDstamp,2))
			cadena = MarketName + '.  Ask-Bid $' + USDT + '\n'
		else:
			Relation = str(round((Relation-1)*100,2))
			cadena = MarketName + '.  Ask-Bid ' + Relation + '%\n'
	else:
		cadena = PresentaTitulo(BitstampRelation1,BitstampRelation2,Relation,CuentaLocal,MarketName)

	#Inicia variables
	porcentaje = []
	stamp = Bitstamp(EcuacionPrecio)

	#Encuentro umbral de oferentes a considerar
	if MarketName=='Transfe2' or MarketName=='Transfe' or MarketName=='Depo':
		with open('ArchivosOperativos/'+CuentaLocal+'_UmbralPublicacionVisible.txt') as f:
			UmbralPublicacionVisible = float(f.readlines()[0])
			f.close()

		#Calcula precio USDT
		USDstamp = Bitstamp('bitstampusd')
	else:
		if MarketName=='Ripple' or MarketName=='Ethereum' or MarketName=='Litecoin': UmbralPublicacionVisible = 0
		else: UmbralPublicacionVisible = 30  # USD50 mínimo para no considerar un oferente sin stock

	#Busca anunciante a vencer
	OferentesValidos = 0
	for i in range(CantidadAvisos):
		#Corrige valores
		precio1[i] = round(float(precio1[i]))
		if minimo1[i] == None: minimo1[i] = 0
		else: minimo1[i] = round(float(minimo1[i]))
		if maximo1[i] == None: maximo1[i] = 50000
		else: maximo1[i] = round(float(maximo1[i]))

		#Elimina oferentes sin stock
		if maximo1[i]<=UmbralPublicacionVisible:
			porcentaje.append(0)
			continue

		#Paxum
		if MarketName=='Paxum':
			if porcentaje[i] > 11: continue

		#Calcula porcentaje
		if MarketName=='Transfe2' or MarketName=='Transfe' or MarketName=='Depo': porcentaje.append(round(precio1[i]/USDstamp,2)); base1 = ' $'; base2 = '\n'
		else: porcentaje.append(round(100*(precio1[i]/stamp-1),2)); base1 = '  '; base2 = '%\n'

		if DesdeDonde=='telegram': cadena = cadena+str(precio1[i])+' $'+str(minimo1[i])+' $'+str(maximo1[i])+'  '+str(name1[i])+base1+str(porcentaje[i])+base2
		else: cadena = cadena+str(precio1[i])+'\t'+str(minimo1[i])+'\t'+str(maximo1[i])+'\t'+str(name1[i])+'\t'+base1+str(porcentaje[i])+base2

		#Limita a 10 oferentes
		OferentesValidos += 1
		if OferentesValidos >= 10: break

	#Imprime anuncios terceros
	if DesdeDonde!='Inicio':
		if DesdeDonde=='pc': print(cadena)
		if DesdeDonde=='telegram': EnviarTelegram(cadena)

	return name1,FormaPago1,precio1,minimo1,maximo1,UserName1,trade_count1,countrycode,CantidadAvisos
#*************************************************
def ModificaAviso(NumAviso,MinAviso,MaxAviso,EstadoVisible,CuentaLocal):
	from Tickets.Soldout_module import LocalCall,Llave
	#Obtener info actual del aviso
	z = LocalCall('/api/ad-get/'+NumAviso+'/',CuentaLocal)
	if not z: return
	min_amount = float(nested_lookup('min_amount',z)[0])
	max_amount = float(nested_lookup('max_amount',z)[0])
	visible = nested_lookup('visible',z)[0]

	#Verificar si hay diferencias y se debe modificar el aviso
	a1,a2,a3 = False,False,False
	if min_amount == MinAviso: a1 = True
	if max_amount == MaxAviso: a2 = True
	if visible == EstadoVisible: a3 = True
	if a1 and a2 and a3: return
	if MinAviso==0: MinAviso = 1
	if MaxAviso==0: MaxAviso = 1

	#opening_hours
	opening_hours = nested_lookup('opening_hours',z)[0]
	if opening_hours == 'null': opening_hours = None
	else: opening_hours = '[[44,92],[32,92],[32,92],[32,92],[32,92],[32,92],[40,88]]'

	#Parametros para modificar aviso
	parametros = {
	'opening_hours': opening_hours,
	'price_equation':nested_lookup('price_equation',z),
	'lat':float(nested_lookup('lat',z)[0]),
	'lon':float(nested_lookup('lon',z)[0]),
	'city':nested_lookup('city',z),
	'location_string':nested_lookup('location_string',z),
	'countrycode':nested_lookup('countrycode',z),
	'currency':nested_lookup('currency',z),
	'account_info':nested_lookup('account_info',z),
	'bank_name':nested_lookup('bank_name',z),
	'msg':nested_lookup('msg',z),
	'sms_verification_required':bool(nested_lookup('sms_verification_required',z)[0]),
	'track_max_amount':bool(nested_lookup('track_max_amount',z)[0]),
	'require_trusted_by_advertiser':bool(nested_lookup('require_trusted_by_advertiser',z)[0]),
	'require_identification':bool(nested_lookup('require_identification',z)[0]),
	'min_amount':MinAviso,
	'max_amount':MaxAviso,
	'visible':EstadoVisible}

	#Modifica aviso
	for x in range(3):
		try: print(Llave(CuentaLocal).call('POST','/api/ad/'+NumAviso+'/',parametros).json()['data']['message'])
		except:	continue
		else: break
	return
#*************************************************
def SelectorCuentas(ImporteOferta,contacto,MarketName,CuentaLocal):
	from Tickets.Soldout_module import DatosMercado,Llave,LeerArchivoCrearLista,Archivador,CuentaLocalbitcoins
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(MarketName,CuentaLocal)

	#Lee las cuentas a informar desde un archivo
	with open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt') as f:
		cuentas = f.readlines()
		f.close()

	#Determina los importes de cada cuenta
	importes = []
	for x in cuentas:
		if '$' in x and not x.isupper():
		  y = x.replace('$','')
		  importes.append(int(y))
	importes = sorted(importes)

	#Elige importe a usar
	CuentaBancaria=''; CuentaBancariaMensaje=''
	for x in range(len(importes)):
		if ImporteOferta <= importes[x]:
			#Eligo la cuenta a informar en función del importe
			importe_a_buscar = '$'+str(importes[x])
			z = 0
			for y in cuentas:
				if importe_a_buscar in y:
					#Actualiza OperacionesTitulares
					OperacionesTitulares = contacto+'#'+cuentas[z-3].replace('\n','')+'#'+CuentaLocal+'#'+MarketName
					Archivador('ArchivosOperativos/OperacionesTitulares.txt',OperacionesTitulares)

					#Arma cuenta según Transfe
					if MarketName=='Transfe' or MarketName=='Transfe2':
						#cuentas[z-5] = BANCO
						#cuentas[z-4] = Nro y tipo de cuenta / Código Rapipago
						#cuentas[z-3] = NOMBRE
						#cuentas[z-2] = CBU / CVU
						#cuentas[z-1] = CUIL
						CuentaBancariaMensaje = cuentas[z-5] + cuentas[z-4] + cuentas[z-3] + cuentas[z-2] + cuentas[z-1] #cuenta de banco
						TipoCuenta = cuentas[z-4]

						#Cuenta de banco
						if '$' in TipoCuenta:
							CuentaBancaria = TipoCuenta[0:TipoCuenta.index('$')+1] + '\n' + cuentas[z-2] + cuentas[z-1] #cuenta sin titular
							# ~ if '$' in TipoCuenta: CuentaBancaria = TipoCuenta[0:TipoCuenta.index('$')+1] + '\n' + cuentas[z-3] + cuentas[z-2] + cuentas[z-1] #cuenta de titular

						#Cuenta MP
						else: CuentaBancaria = 'CA $\n' + cuentas[z-2] + cuentas[z-4]

					#MarketName Depo
					else: CuentaBancaria = cuentas[z-5] + cuentas[z-4] + cuentas[z-2] + cuentas[z-1]
					# ~ else: CuentaBancaria = cuentas[z-5] + cuentas[z-4] + cuentas[z-3] + cuentas[z-2] + cuentas[z-1]
					break

				z+=1

			#Modifico arhivo cuentas
			nuevo_importe = '$'+str(int(importes[x]-ImporteOferta))
			ListaArchivo = LeerArchivoCrearLista('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt')
			for x in range(len(ListaArchivo)):
				if ListaArchivo[x]==importe_a_buscar:
					ListaArchivo[x] = nuevo_importe
					break
			with open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt','w') as f:
				for item in ListaArchivo:
					item = item+'\n'
					f.write('%s' %item)
			break

	#Determina nuevos mínimo y máximo después de la oferta
	SelectorMinimoMaximo(MarketName,CuentaLocal)

	return CuentaBancaria,CuentaBancariaMensaje
#*************************************************
def PosicionaTuAviso(DesdeDonde,MarketName,CuentaLocal1):
	from Tickets.Soldout_module import Llave,LocalCall,FiltroQR,Bitstamp,MarketRelation,DatosMercado,HayInternet
	global CuentaLocal
	CuentaLocal = CuentaLocal1

	#Si no hay Internet, cancelo posicionamiento
	if not HayInternet():
		time.sleep(30)
		return

	#Ejecuto funciones iniciales
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(MarketName,CuentaLocal)
	if not MarketName: return
	MarketRelation = MarketRelation(MarketName,market1,EcuacionPrecio,CuentaLocal)
	name,FormaPago,precio,minimo,maximo,UserName,trade_count,countrycode,CantidadAvisos = PresentaAvisosTerceros(MarketName,CuentaLocal,DesdeDonde,MarketRelation)
	if not CantidadAvisos:  return

	#Leo archivo BitstampRelation1
	f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation1.txt','r')
	BitstampRelation1 = round(float(f.read()),4)
	f.close()

	#Leo archivo BitstampRelation2
	f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation2.txt','r')
	BitstampRelation2 = round(float(f.read()),4)
	f.close()

	#Variables iniciales
	if MarketName=='Transfe2' or MarketName=='Transfe' or MarketName=='Skrillventa' or MarketName=='Netellerventa' or MarketName=='Zelleventa' or MarketName=='Depo': TipoMercado = 'venta'
	if MarketName=='Paypal' or MarketName=='Payoneer' or MarketName=='Paxum' or MarketName=='Skrillcompra' or MarketName=='Netellercompra' or MarketName=='Zellecompra' or MarketName=='Wise' or MarketName=='Ripple' or MarketName=='Ethereum' or MarketName=='Litecoin': TipoMercado = 'compra'

	#Obtener la info de tu aviso
	TuAviso = LocalCall('/api/ad-get/'+NumAviso+'/',CuentaLocal,m=10)
	try: visible = nested_lookup('visible',TuAviso)[0]
	except:	return

	if not visible: return
	TuPrecio = float(nested_lookup('temp_price',TuAviso)[0])

	#Encuentro umbral de oferentes a considerar
	if MarketName=='Transfe2' or MarketName=='Transfe' or MarketName=='Depo':
		Indice = 323
		with open('ArchivosOperativos/'+CuentaLocal+'_UmbralPublicacionVisible.txt') as f:
			UmbralPublicacionVisible = float(f.readlines()[0])
			f.close()
	else:
		if MarketName=='Ripple' or MarketName=='Ethereum' or MarketName=='Litecoin': Indice = 1; UmbralPublicacionVisible = 0
		else: Indice = 6; UmbralPublicacionVisible = 50  # USD50 mínimo para no considerar un oferente sin stock

	#Determina precio del bitcoin
	stamp = Bitstamp(EcuacionPrecio)
	if stamp==1: return
	if MarketName=='Transfe2' or MarketName=='Transfe' or MarketName=='Depo':
		USDstamp = Bitstamp('bitstampusd')
		if USDstamp==1: return
		BitstampRelation1 = BitstampRelation1/stamp*USDstamp
		BitstampRelation2 = BitstampRelation2/stamp*USDstamp

	#Busca anunciante a vencer
	Modificar = False
	for i in range(CantidadAvisos):
		#Corrige valores
		precio[i] = float(precio[i])
		if maximo[i] == None: maximo[i] = 50000
		else: maximo[i] = round(float(maximo[i]))

		#Elimina oferentes sin stock
		if maximo[i] <= UmbralPublicacionVisible: continue

		#Anunciante Novato
		y = '+' in trade_count[i]
		if trade_count[i]=='+30' or not y: continue

		#Evita competir contra vos mismo
		if UserName[i]=='Saldo1' or UserName[i]=='MAVE45': continue

		#SELL
		if TipoMercado == 'venta':
			if precio[i]>=stamp*BitstampRelation1 and precio[i]>=stamp*MarketRelation:
				#Precio Limite
				if precio[i]<=stamp*BitstampRelation2: PrecioLimite = precio[i]
				else: break

				#Hay que modificar?
				if TuPrecio>PrecioLimite-Indice-1 or TuPrecio<PrecioLimite-Indice+1:
					TuPrecio = PrecioLimite-Indice
					Modificar = True
				break
		#BUY
		if TipoMercado == 'compra':
			if 	precio[i]<=stamp*BitstampRelation1:
				#Precio Limite
				if precio[i]>=stamp*BitstampRelation2:
					PrecioLimite = precio[i]
					#Hay que modificar?
					if TuPrecio<PrecioLimite+Indice-1 or TuPrecio>PrecioLimite+Indice+1:
						TuPrecio = PrecioLimite+Indice
						Modificar = True
				else:
					#Precio Limite
					PrecioLimite = stamp*BitstampRelation2

					#Hay que modificar?
					if TuPrecio<PrecioLimite+Indice-1 or TuPrecio>PrecioLimite+Indice+1:
						TuPrecio = PrecioLimite+Indice
						Modificar = True
				break

	#Verificás si tu aviso infringe BitstampRelation1 ó BitstampRelation2
	if not Modificar:
		if TipoMercado=='venta':
			if TuPrecio<stamp*BitstampRelation1: TuPrecio = stamp*BitstampRelation1; Modificar = True
			if TuPrecio>stamp*BitstampRelation2: TuPrecio = stamp*BitstampRelation2; Modificar = True
		if TipoMercado=='compra':
			if TuPrecio>stamp*BitstampRelation1:
				TuPrecio = stamp*BitstampRelation1
				Modificar = True
			if TuPrecio<stamp*BitstampRelation2:
				TuPrecio = stamp*BitstampRelation2
				Modificar = True

	#Modifica precio
	if Modificar:
		#Chequea si varió la ecuación para modificarla
		try: EcuacionActiva = Llave(CuentaLocal).call('GET','/api/ad-get/'+NumAviso+'/').json()
		except: return
		EcuacionActiva = nested_lookup('price_equation',EcuacionActiva)[0]
		EcuacionNueva = EcuacionPrecio+'*'+str(TuPrecio/stamp)
		if EcuacionActiva==EcuacionNueva: return

		#Modificás precio de tu aviso
		for m in range (3):
			try: print(Llave(CuentaLocal).call('POST','/api/ad-equation/'+NumAviso+'/',params={'price_equation':EcuacionNueva}).json()['data']['message'])
			except: continue
			else: break
#*************************************************
def SelectorImportes(oferta,contacto,MarketName,CuentaLocal):
	from Tickets.Soldout_module import DatosMercado,Archivador,Llave,EnviarTelegram,Bitstamp
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(MarketName,CuentaLocal)

	#Lee importes en archivo txt
	with open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt') as f:
		cuentas = f.readlines()
		f.close()

	#Determina los importes mínimo y máximo
	importes = [] #lista
	for x in cuentas:
		if '$' in x and not x.isupper():
		  y = x.replace('$','')
		  importes.append(int(y))
	MinAviso = min(importes)
	MaxAviso = max(importes)-oferta

	#Graba txt
	NuevosImportes = '$'+str(MinAviso)+'\n$'+str(MaxAviso)
	f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt','w')
	f.write(NuevosImportes)
	f.close()

	#Actualiza OperacionesTitulares
	OperacionesTitulares = contacto+'#NN#'+CuentaLocal+'#'+MarketName
	Archivador('ArchivosOperativos/OperacionesTitulares.txt',OperacionesTitulares)

	#Liquidez superada?
	if MaxAviso<MinAviso:
		#Desactivas aviso
		ModificaAviso(NumAviso,1,10,False,CuentaLocal)
		cadena = 'Aviso ' + MarketName + ' desactivado!'
	else:
		#Obtiene balance y verifica el máximo del aviso con respecto a la cartera
		USDstamp = Bitstamp('bitstampusd')
		if MaxAviso < 0.02*USDstamp: cadena = MarketName+' importes modificados. Mínimo '+str(MinAviso)+'. Máximo '+str(MaxAviso)+'. Menor máximo posible '+str(int(0.02*USDstamp))+'. El aviso puede no ser visible!'
		else: cadena = MarketName+' importes modificados. Mínimo '+str(MinAviso)+'. Máximo '+str(MaxAviso)+'. Menor máximo posible '+str(int(0.02*USDstamp))

		#Determina nuevos mínimo y máximo después de la oferta
		SelectorMinimoMaximo(MarketName,CuentaLocal)

	#Telegram
	EnviarTelegram(cadena)

	return
#*************************************************
def SelectorMinimoMaximo(MarketName,CuentaLocal,visible=True):
	from Tickets.Soldout_module import DatosMercado,Llave
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(MarketName,CuentaLocal)

	#Lee las cuentas a informar desde un archivo
	with open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt') as f:
		cuentas = f.readlines()
		f.close()

	#Determina los importes de cada cuenta
	importes = []
	for LineaInfoCuenta in cuentas:
		if '$' in LineaInfoCuenta:
			LineaInfoCuenta = LineaInfoCuenta.replace('$','')
			LineaInfoCuenta = LineaInfoCuenta.replace('\n','')
			if LineaInfoCuenta.isnumeric():	importes.append(int(LineaInfoCuenta))

	#Si el archivo de importes está vacío, desactivo el aviso
	if not importes:
		#Desactivo aviso
		print('Aviso desactivado porque el archivo de importes está vacío')
		ModificaAviso(NumAviso,1,10,False,CuentaLocal)
		return

	if MarketName=='Transfe2' or MarketName=='Transfe' or MarketName=='Depo':
		#Lee UmbralPublicacionVisible
		with open('ArchivosOperativos/'+CuentaLocal+'_UmbralPublicacionVisible.txt') as f:
			UmbralPublicacionVisible = float(f.readlines()[0])
			f.close()

		#Lee UmbralDividePago
		with open('ArchivosOperativos/'+CuentaLocal+'_UmbralDividePago.txt') as f:
			UmbralDividePago = float(f.readlines()[0])
			f.close()

		#Elimino importes menores a umbral
		importes = sorted(importes)
		ImportesAux = list(importes)
		importes = []
		for x in range(len(ImportesAux)):
			if ImportesAux[x] < UmbralPublicacionVisible: continue
			importes.append(ImportesAux[x])

		#Si todas las cuentas quedaron con menos de Umbral, desactivo el aviso
		if not importes:
			print('Aviso desactivado porque las cuentas quedaron con menos de umbral')
			ModificaAviso(NumAviso,1,10,False,CuentaLocal)
			return

	# ~ #Selecciona importe máximo y mínimo - original
	# ~ MinImportes = min(importes); MaxAviso = max(importes)
	# ~ if MarketName=='Transfe2' or MarketName=='Transfe' or MarketName=='Depo':
		# ~ if MinImportes<=UmbralDividePago:
			# ~ MaxAviso = MinImportes
			# ~ MinAviso = MinImportes-100
		# ~ else:
			# ~ MaxAviso = MinImportes
			# ~ MinAviso = int(MinImportes/2)
			# ~ if MinAviso>UmbralDividePago:
				# ~ MinAviso = int(UmbralDividePago)
	# ~ else: MinAviso = MinImportes

	#Selecciona importe máximo y mínimo
	# ~ MaxAviso = max(importes); MinAviso = min(importes)
	# ~ if len(importes)==1 and (MarketName=='Transfe2' or MarketName=='Transfe' or MarketName=='Depo'):
		# ~ if MinAviso<=UmbralDividePago:
			# ~ MaxAviso = MinAviso
			# ~ MinAviso = MinAviso-100
		# ~ else:
			# ~ MaxAviso = MinAviso
			# ~ MinAviso = int(MinAviso/2)
			# ~ if MinAviso>UmbralDividePago:
				# ~ MinAviso = int(UmbralDividePago)

	#Selecciona importe máximo y mínimo
	importes = sorted(importes); L = len(importes)-1
	MinAviso = importes[0]; MaxAviso = importes[L]
	if MarketName=='Transfe2' or MarketName=='Transfe' or MarketName=='Depo':
		if MaxAviso/2>UmbralDividePago:
			if MinAviso>UmbralDividePago:
				MinAviso = int(MinAviso/2)
				if MinAviso>UmbralDividePago: MinAviso = int(UmbralDividePago)
			else:
				if importes[1]/2>MinAviso or MinAviso>UmbralDividePago: MinAviso = int(UmbralDividePago)
				if MinAviso<UmbralDividePago: MinAviso = int(UmbralDividePago)
		else:
			if L>=1:
				if MaxAviso>UmbralDividePago:
					if importes[1]/2>MinAviso or MinAviso>UmbralDividePago: MinAviso = int(importes[1]/2)
					if MinAviso<UmbralDividePago: MinAviso = int(UmbralDividePago)
				else:
					if MinAviso/2>UmbralPublicacionVisible: MinAviso = int(MinAviso/2)
			else:
				if MinAviso>UmbralDividePago: MinAviso = int(MinAviso/2)
				else: MinAviso = MinAviso-100

	#Modifico aviso con mínimo y máximo (aquí se activa aviso)
	if visible:
		cadena = MarketName+': '+str(MinAviso)+' - '+str(MaxAviso)
		print(cadena)
		ModificaAviso(NumAviso,MinAviso,MaxAviso,True,CuentaLocal)

	return
#*************************************************
