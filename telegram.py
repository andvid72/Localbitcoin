#Importa funciones
import json,time,sys,platform,os.path,re,fileinput,requests,os,signal,threading, psutil, signal
from Binance import *
from funciones import *
from trading import *
from subprocess import Popen, CREATE_NEW_CONSOLE
from datetime import datetime,timedelta #Obtiene fecha y hora en formato humano
from lbcapi3 import api #api de Localbitcoins para Python 3
from nested_lookup import nested_lookup #extrae valor de listas y bibliotecas anidadas
import telepot,telebot #envía mensajes a Telegram
alias = youralias
token = yourtoken
#*************************************************
def TelegramPanel(TelegramProximoID,instruccion):
	from funciones import Llave,EnviarTelegram,DeterminaCuentaLocalbitcoins

	#Determina cuenta de Localbitcoins
	CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
	if not CuentaLocal: return TelegramProximoID

	#Obtiene info de avisos
	try: PanelControl = Llave(CuentaLocal).call('GET','/api/ads/',{'timeout':1}).json()
	except:
		cadena = 'No se pudo obtener el panel de la cuenta '+CuentaLocal
		EnviarTelegram(cadena)
		return TelegramProximoID
	online_provider = nested_lookup('online_provider',PanelControl)
	currency =  nested_lookup('currency',PanelControl)
	trade_type =  nested_lookup('trade_type',PanelControl)
	visible =  nested_lookup('visible',PanelControl)
	opening_hours = nested_lookup('opening_hours',PanelControl)
	hidden_by_opening_hours = nested_lookup('hidden_by_opening_hours',PanelControl)

	#Revisa todos los avisos
	cadena = 'PANEL DE AVISOS ' + CuentaLocal.upper() + '\n'
	for x in range(len(online_provider)):
		#Modfica Nombres
		mercado = online_provider[x].capitalize()
		if mercado=='National_bank' and currency[x]=='ARS': mercado = 'Transfe'
		if mercado=='Other' and currency[x]=='ARS': mercado = 'Transfe2'
		if mercado=='Cash_deposit' and currency[x]=='ARS': mercado = 'Depósito'
		if mercado=='Moneybookers' : mercado = 'Skrill'

		#Compra-Venta
		if trade_type[x] == 'ONLINE_BUY': mercado = mercado + '-compra'
		else: mercado = mercado + '-venta'
		mercado = '{:<15}'.format(mercado)

		#Visibilidad
		if not visible[x]: visibilidad = 'Inactivo'
		else:
			if hidden_by_opening_hours[x]: visibilidad = 'Oculto'
			else: visibilidad = 'Activo'
		visibilidad = '{:<10}'.format(visibilidad)

		#Ocultar por horas
		if opening_hours[x]=='null': horario = 'Simple'
		else: horario = 'Horario'
		horario = '{:<10}'.format(horario)

		#Cadena
		cadena = cadena + mercado + '   ' + visibilidad + '   ' + horario + '\n'

	EnviarTelegram(cadena)
	return TelegramProximoID
#*************************************************
def TelegramAyuda():
	from funciones import EnviarTelegram
	ayudin1 = ['DASH: ordenes abiertas','PANEL: avisos activos','LBTC TRANSACCIONES','UMBRALES MODIFICAR','AVISO depo','COMPRA PAYTIZ']
	ayudin2 = ['RENTA: compra venta por monedero','IMPORTES paypal 200 500','VOLUMEN ars','HORARIO paypal si/no','UMBRALES VER']
	ayudin3 = ['ACTIVAR paypal','DESACTIVAR paypal','BOOK ars','CHAT contacto','VOLUMEN 24 ars','BOT terminales activas']
	ayudin4 = ['REACTIVAR paypal','BALANCE','LIBERAR contacto','PAGADO contacto','FUTUROS extraer','CLIENTE COMPRA 140','CLIENTE VENTA 128']
	ayudin5 = ['DISPUTA contacto','contacto: mensaje','5% paypal - $200 transfe','BINANCE BALANCE','MAILING','CLIENTE DATOS']
	ayudin6 = ['CUENTA transfe','FUTUROS depositar','LBTC FEE','PAYTIZ','BTC precio bitcoin']
	ayudin7 = ['LBTC ADDRESS','LBTC EXTRAER','COMPRA: cotización compra Paypal/Payoneer','BINANCE EQUILIBRAR','1234: mensaje']
	ayudin = ayudin1 + ayudin2 + ayudin3 + ayudin4 + ayudin5 + ayudin6 + ayudin7
	ayudin = sorted(ayudin)
	cadena = ''
	for z in range(len(ayudin)): cadena = cadena + ayudin[z]+'\n'
	EnviarTelegram(cadena)
#*************************************************
def TelegramBinanceDepositarFuturo(TelegramProximoID):
	#Presenta información
	from Binance import BinanceMargin,BinanceDepositarFuturo
	BinanceMargin('Depositar')

	#Pregunta cantidad a enviar
	BinanceAmount,TelegramProximoID = Repreguntador('Cántidad a enviar a futuros? ','EsNumero',TelegramProximoID)
	if not BinanceAmount: return TelegramProximoID
	BinanceAmount = float(BinanceAmount)

	#Enviás a Binance la cantidad indicada
	BinanceDepositarFuturo(BinanceAmount)

	return TelegramProximoID
#*************************************************
def TelegramBinanceExtraerFuturo(TelegramProximoID):
	#Presenta información
	from Binance import BinanceMargin,BinanceExtraerFuturo
	BinanceMargin('Extraer')

	#Pregunta cantidad a enviar
	BinanceAmount,TelegramProximoID = Repreguntador('Cántidad a extraer de futuros? ','EsNumero',TelegramProximoID)
	if not BinanceAmount: return TelegramProximoID
	BinanceAmount = float(BinanceAmount)

	#Enviás a Binance la cantidad indicada
	BinanceExtraerFuturo(BinanceAmount)

	return TelegramProximoID
#*************************************************
def TelegramPorcentaje(instruccion,TelegramProximoID):
	#Inicializo Variables
	from funciones import DatosMercado,EnviarTelegram,MarketRelation,DeterminaCuentaLocalbitcoins

	#Determina cuenta de Localbitcoins
	CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
	if not CuentaLocal:
		EnviarTelegram('Cuenta Localbitcoins mal informada!')
		return TelegramProximoID

	#Datos de mercado
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(instruccion,CuentaLocal)
	if not MarketName:
		EnviarTelegram('Mercado mal informado!')
		return TelegramProximoID

	#Verifico si está bien informado % ó $ según el mercado
	if (MarketName=='Transfe2' or MarketName =='Transfe' or MarketName =='Depo'):
		if '$' not in instruccion.upper():
			EnviarTelegram('$ no informado!')
			return TelegramProximoID
	else:
		if '%' not in instruccion:
			EnviarTelegram('% no informado!')
			return TelegramProximoID

	#Busco números en la instrucción recibida sobre porcentajes
	instruccion = instruccion.upper()
	instruccion = instruccion.replace('SALDO1','')
	instruccion = instruccion.replace('MAVE45','')
	instruccion = instruccion.replace('TRANSFE2','')
	instruccion = re.findall(r'[-+]?\d*\.?\d+|\d+',instruccion)
	if len(instruccion) != 2:
		EnviarTelegram('Instrucción incorrecta!')
		return TelegramProximoID

	#Determina porcentaje mínimo y máximo según el mercado
	Min = min(float(instruccion[0]),float(instruccion[1]))
	Max = max(float(instruccion[0]),float(instruccion[1]))
	if MarketName=='Transfe2' or MarketName =='Transfe' or MarketName =='Depo': Relation = Min; Relation1 = Max
	else: Relation = Max; Relation1 = Min

	#Modifico archivo BitstampRelation1
	if MarketName=='Transfe2' or MarketName =='Transfe' or MarketName =='Depo': BitstampRelation1 = round(Relation,2)
	else: BitstampRelation1 = round(1+float(Relation)/100,4)
	print('BitstampRelation1',BitstampRelation1)
	f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation1.txt','w')
	f.write(str(BitstampRelation1))
	f.close()

	#Modifico archivo BitstampRelation2
	if MarketName=='Transfe2' or MarketName =='Transfe' or MarketName =='Depo': BitstampRelation2 = round(Relation1,2)
	else: BitstampRelation2 = round(1+float(Relation1)/100,4)
	print('BitstampRelation2',BitstampRelation2)
	f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_BitstampRelation2.txt','w')
	f.write(str(BitstampRelation2))
	f.close()

	#Informa cambio de % en Telegram
	if MarketName=='Transfe2' or MarketName =='Transfe' or MarketName =='Depo': cadena = MarketName+' mínimo/máximo modificado: $'+str(Min)+' - $'+str(Max)
	else: cadena = MarketName+' porcentajes modificado: '+str(Min)+'% - '+str(Max)+'%'
	EnviarTelegram(cadena)

	return TelegramProximoID
#*************************************************
def TelegramRenta(ProximoID):
	from funciones import DatosMercado,EnviarTelegram
	from trading import PresentaAvisosTerceros
	global TelegramProximoID
	TelegramProximoID = ProximoID

	#COMPRA
	#Pregunta con qué comprás bitcoin y pasa listado de avisos
	MarketNameCompra,TelegramProximoID = Repreguntador('Monedero con el que comprás bitcoin? ','EsMonedero',TelegramProximoID)
	if 'SKRILL' in MarketNameCompra.upper() or 'NETELLER' in MarketNameCompra.upper() or 'ZELLE' in MarketNameCompra.upper(): MarketNameCompra = MarketNameCompra + 'compra'
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketNameCompra = DatosMercado(MarketNameCompra,'Saldo1')
	if not MarketNameCompra: return TelegramProximoID
	PresentaAvisosTerceros(MarketNameCompra,'Saldo1','telegram')

	#Pregunta cotización que tendría tu aviso
	respuesta,TelegramProximoID = Repreguntador('Precio de compra de bitcoins con '+MarketNameCompra+'? ','EsNumero',TelegramProximoID)
	if not respuesta: return TelegramProximoID
	compraBTC = float(respuesta)

	#Pregunta cotización que estás pagando
	respuesta,TelegramProximoID = Repreguntador('Cotización que pagás? ','EsNumero',TelegramProximoID)
	if not respuesta: return TelegramProximoID
	cotiCompra = float(respuesta)
	if MarketNameCompra=='Skrillcompra': compra = compraBTC*1.01*cotiCompra*1.0145
	elif  MarketNameCompra=='Netellercompra': compra = compraBTC*1.01*cotiCompra*1.0299
	else: compra = compraBTC*1.01*cotiCompra

	#VENTA
	#Pregunta cómo vendés bitcoin y pasa listado de avisos
	MarketNameVenta,TelegramProximoID = Repreguntador('Monedero con el que vendés bitcoin? ','EsMonedero',TelegramProximoID)
	if 'SKRILL' in MarketNameVenta.upper() or 'NETELLER' in MarketNameVenta.upper() or 'ZELLE' in MarketNameVenta.upper(): MarketNameVenta = MarketNameVenta + 'venta'
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketNameVenta = DatosMercado(MarketNameVenta,'Saldo1')
	if not MarketNameVenta: return TelegramProximoID
	PresentaAvisosTerceros(MarketNameVenta,'Saldo1','telegram')

	#Pregunta cotización que tendría tu aviso
	respuesta,TelegramProximoID = Repreguntador('Precio de venta de bitcoins con '+MarketNameVenta+'? ','EsNumero',TelegramProximoID)
	if not respuesta: return TelegramProximoID
	ventaBTC = float(respuesta)
	venta = ventaBTC*0.99

	#PRESENTA INFO
	rentabilidad = round((venta/compra-1)*100,2)
	cadena = 'Rentabilidad '+MarketNameCompra+' / '+MarketNameVenta+': '+str(rentabilidad)+'%'
	EnviarTelegram(cadena)

	return TelegramProximoID
#*************************************************
def TelegramCuenta(instruccion,TelegramProximoID):
	from funciones import DatosMercado,Archivador,EnviarTelegram,SelectorMinimoMaximo,LocalCall,DeterminaCuentaLocalbitcoins
	from trading import SelectorMinimoMaximo

	#Determina cuenta de Localbitcoins
	CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
	if not CuentaLocal: return TelegramProximoID

	#Datos de mercado
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(instruccion,CuentaLocal)
	if not MarketName: return TelegramProximoID

	#Verifico visibilidad
	z = LocalCall('/api/ad-get/'+NumAviso+'/',CuentaLocal)
	if not z: return TelegramProximoID
	visible = nested_lookup('visible',z)[0]

	#Procedo según la instrucción recibida
	if MarketName.upper() in instruccion.upper() and MarketName!='':
		# ~ if 'VER' in instruccion.upper():
			# ~ f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt','r')
			# ~ cadena = f.read()
			# ~ if not cadena: cadena = 'Archivo Importes'+MarketName+'.txt vacío!'
			# ~ f.close()
			# ~ EnviarTelegram(cadena)
			# ~ return TelegramProximoID

		# ~ if 'NUEV' in instruccion.upper():
			#Muestra archivo cuentas actual
		cadena = 'Archivo de cuentas '+MarketName+' actual:\n\n'
		f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt','r')
		cadena = cadena + f.read()
		if not cadena: cadena = 'Archivo Importes'+MarketName+'.txt vacío'
		f.close()
		EnviarTelegram(cadena)

		#Pregunta si se va a borrar archivo anterior antes de modificar
		respuesta,TelegramProximoID = Repreguntador('Borrar antes de modificar (si/no)? ','EsAfirmativo',TelegramProximoID)
		if not respuesta: return TelegramProximoID
		if respuesta=='SI':
			#Elimina archivo importes
			if os.path.exists('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt'):
				try: os.remove('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt')
				except: pass
			f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt','w')
			f.close()

		#Pregunta nueva cuenta
		mensaje,TelegramProximoID = Repreguntador('Nuevas cuentas para archivo de Importes?','cuenta',TelegramProximoID)

		#Registra nueva cuenta en archivo
		if ('CBU' in mensaje or 'CVU' in mensaje) and '$' in mensaje:
			Archivador('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt',mensaje)
			cadena = 'Archivo de cuentas '+MarketName+' actualizado!\n\n'
		else: cadena = 'Archivo de cuentas '+MarketName+' no se actualizó!\n\n'
		f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt','r')
		cadena = cadena + f.read()
		f.close()

		#Telegram
		EnviarTelegram(cadena)

		#Pregunta si se va a reactivar el aviso
		if not visible:
			respuesta,TelegramProximoID = Repreguntador('El aviso no está activo. Reactivar (si/no)? ','EsAfirmativo',TelegramProximoID)
			if not respuesta: return TelegramProximoID
			if respuesta=='SI':
				EnviarTelegram('Se inicia reactivación de aviso!')
				SelectorMinimoMaximo(MarketName,CuentaLocal,True)
		else:
			#Modificación máximo y mínimo
			EnviarTelegram('Se inicia modificación de importes máximo y mínimo')
			SelectorMinimoMaximo(MarketName,CuentaLocal,True)

	return TelegramProximoID
#*************************************************
def TelegramNuevosimportes(instruccion,TelegramProximoID):
	from funciones import DatosMercado,EnviarTelegram,DeterminaCuentaLocalbitcoins

	#Determina cuenta de Localbitcoins
	CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
	if not CuentaLocal: return '',TelegramProximoID,''

	#Datos de mercado
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(instruccion,CuentaLocal)
	if not MarketName:
		EnviarTelegram('Mal informado el mercado!')
		return '',TelegramProximoID,CuentaLocal
	if MarketName == 'Transfe' or MarketName=='Depo' or MarketName=='Transfe2':
		EnviarTelegram('Se inicia modificación de importes máximo y mínimo')
		return MarketName,TelegramProximoID,CuentaLocal

	#Busca importes a cargar en txt
	instruccion = re.findall(r' \d+',instruccion)
	instruccion = sorted(instruccion)
	if not instruccion:
		EnviarTelegram('Mal informados los importes!')
		return MarketName,TelegramProximoID,CuentaLocal

	#Calcula importes a cargar en txt
	MinAviso = instruccion[0].lstrip()
	if len(instruccion)==1: MaxAviso = MinAviso
	else: MaxAviso = instruccion[1].lstrip()
	NuevosImportes = '$' + MinAviso + '\n$' + MaxAviso

	#Carga importes en txt
	f = open('ArchivosOperativos/'+CuentaLocal+'_'+MarketName+'_Importes.txt','w')
	f.write(NuevosImportes)
	f.close()

	#Responde con Telegram al pedido
	cadena = CuentaLocal+' '+MarketName+' modificado: $'+MinAviso+' $'+MaxAviso
	EnviarTelegram(cadena)

	return MarketName,TelegramProximoID,CuentaLocal
#*************************************************
def TelegramDesactivar(instruccion,TelegramProximoID):
	from funciones import DatosMercado,LeerArchivoCrearLista,EnviarTelegram,DeterminaCuentaLocalbitcoins

	#Determina cuenta de Localbitcoins
	CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
	if not CuentaLocal: return '',TelegramProximoID,''

	#Datos de mercado
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(instruccion,CuentaLocal)
	if not MarketName:
		EnviarTelegram('No se informó mercado!')
		return NumAviso,TelegramProximoID,CuentaLocal

	#Desactiva bot
	TodoPids = LeerArchivoCrearLista('ArchivosOperativos/PidsMercados.txt')
	if TodoPids:
		for pids in TodoPids:
			ListaInfo = pids.rsplit('#')
			IntPid = ListaInfo[0]; CuentaLocalPid = ListaInfo[1]; MarketPid = ListaInfo[2]
			if MarketPid==MarketName and CuentaLocalPid==CuentaLocal:
				os.kill(int(IntPid),signal.SIGTERM)
				cadena = CuentaLocal+' '+MarketName+' bot cerrado!'
				EnviarTelegram(cadena)

	return NumAviso,TelegramProximoID,CuentaLocal
#*************************************************
def TelegramReactiva(instruccion,TelegramProximoID,CuentaLocal=''):
	from funciones import DatosMercado,EnviarTelegram,DeterminaCuentaLocalbitcoins

	#Determina cuenta de Localbitcoins
	CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
	if not CuentaLocal: return TelegramProximoID

	#Datos mercado
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(instruccion,CuentaLocal)
	if not MarketName:
		EnviarTelegram('No se informó mercado!')
		return TelegramProximoID

	#Responde con Telegram al pedido
	cadena = CuentaLocal+' '+MarketName+' inicia reactivación!'
	EnviarTelegram(cadena)

	#Activa terminal y aviso
	Popen([sys.executable,'bot.py',MarketName,str(TelegramProximoID),'reactiva',CuentaLocal], creationflags=CREATE_NEW_CONSOLE)

	return TelegramProximoID
#*************************************************
def TelegramActiva(instruccion,TelegramProximoID):
	from funciones import DatosMercado,EnviarTelegram,DeterminaCuentaLocalbitcoins

	#Determina cuenta de Localbitcoins
	CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
	if not CuentaLocal: return TelegramProximoID

	#Datos mercado
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(instruccion,CuentaLocal)
	if not MarketName:
		EnviarTelegram('No se informó mercado!')
		return TelegramProximoID

	#Responde con Telegram al pedido
	cadena = CuentaLocal+' '+MarketName+' inicia activación!'
	EnviarTelegram(cadena)

	#Activa terminal y aviso
	Popen([sys.executable,'bot.py',MarketName,str(TelegramProximoID),'activa',CuentaLocal], creationflags=CREATE_NEW_CONSOLE)

	return TelegramProximoID
#*************************************************
def TelegramBalance(TelegramProximoID):
	from funciones import LocalCall,EnviarTelegram,BitcoinArgentina,Bitstamp
	from Binance import BinanceBalance
	EnviarTelegram('Se inicia determinación de estado en todas las cuentas!')

	#Precio bitcoin
	ARSstamp = Bitstamp('bitstampusd*USD_in_ARS')
	USDstamp = Bitstamp('bitstampusd')

	#Balance Localbitcoin Saldo1
	LBTCbalanceSaldo1 = LocalCall('/api/wallet-balance/','Saldo1')
	try: LBTCbalanceSaldo1 = round(float(nested_lookup('balance',LBTCbalanceSaldo1)[0]),8)
	except: LBTCbalanceSaldo1 = 0

	#Balance Localbitcoin MAVE45
	LBTCbalanceMAVE45 = LocalCall('/api/wallet-balance/','MAVE45')
	try: LBTCbalanceMAVE45 = round(float(nested_lookup('balance',LBTCbalanceMAVE45)[0]),8)
	except: LBTCbalanceMAVE45 = 0

	#Determino balance total en Binance
	BinanceMargen,BinanceSpot,BinanceUSDT = BinanceBalance()
	BinanceTotal = round(BinanceMargen + BinanceSpot + BinanceUSDT/USDstamp,8)

	#Determino balance bitcoin en Binance
	BinanceMargen,BinanceSpot,BinanceUSDT = BinanceBalance()
	BinanceBitcoin = round(BinanceMargen + BinanceSpot,8)
	if BinanceBitcoin<0.0000001: BinanceBitcoin = 0

	#Determino balance tether en Binance
	if BinanceUSDT<1: BinanceUSDT = 0

	#Determina balance total
	balance = round(LBTCbalanceSaldo1 + LBTCbalanceMAVE45 + BinanceTotal,8)

	#Precio bitcoin Argentina
	PrecioArgentina = BitcoinArgentina()

	#Localbitcoins Fees
	try: fees = LocalCall('/api/fees/','Saldo1')['data']
	except: pass
	LBTCfee = float(fees.get('outgoing_fee'))

	#Telegram
	cadena1 = 'Precio Bitcoin: USD '+str(USDstamp)+' - USDT '+str(int(PrecioArgentina/USDstamp))+'\n'
	cadena2 = 'Saldo1: ARS '+str(int(LBTCbalanceSaldo1*PrecioArgentina))+' - USD '+str(int(LBTCbalanceSaldo1*USDstamp))+' - BTC '+str(round(LBTCbalanceSaldo1-LBTCfee,8))+'\n'
	cadena22 = 'MAVE45: ARS '+str(int(LBTCbalanceMAVE45*PrecioArgentina))+' - USD '+str(int(LBTCbalanceMAVE45*USDstamp))+' - BTC '+str(round(LBTCbalanceMAVE45-LBTCfee,8))+'\n'
	cadena3 = 'Binance Bitcoin: ARS '+str(int(BinanceBitcoin*PrecioArgentina))+' - USD '+str(int(BinanceBitcoin*USDstamp))+'\n'
	cadena4 = 'Binance Tether: ARS '+str(int(BinanceUSDT/USDstamp*PrecioArgentina))+' - USD '+str(BinanceUSDT)+'\n'
	cadena5 = 'Binance Total: ARS '+str(int(BinanceTotal*PrecioArgentina))+' - USD '+str(int(BinanceTotal*USDstamp))+'\n'
	cadena6 = 'Total: ARS '+str(int(balance*PrecioArgentina))+' - USD '+str(int(balance*USDstamp))
	cadena = cadena1 + cadena2 + cadena22 + cadena3 + cadena4 + cadena5 + cadena6
	EnviarTelegram(cadena)

	return TelegramProximoID
#*************************************************
def TelegramMensaje(instruccion):
	from funciones import Llave,EnviarTelegram,DeterminaContacto

	#Evalua si está construida correctamente la instruccion
	try: instruccion.index(':')
	except: return

	#Obtengo contacto y cuenta local
	contacto,CuentaLocal = DeterminaContacto(instruccion)
	if not contacto:
		EnviarTelegram('Contacto mal informado para enviar mensaje!')
		return

	#Obtengo mensaje a enviar
	mensaje = instruccion[instruccion.index(':'):len(instruccion)]
	mensaje = mensaje.replace(': ','')
	mensaje = mensaje.replace(':','')
	if mensaje=='': return
	calltxt = '/api/contact_message_post/'+contacto+'/'
	parametros = {'msg':mensaje}
	cadena ='Mensaje enviado!'
	try:
		print(Llave(CuentaLocal).call('POST',calltxt,parametros).json()['data']['message'])
		EnviarTelegram(cadena)
	except:	return
#*************************************************
def TelegramFoto(response,TextCounter,file_id):
	from funciones import Llave,EnviarTelegram,DeterminaContacto
	bot = telepot.Bot(token)
	bot2 = telepot.Bot(tokenAugu)

	#Busco a qué chat corresponde la imagen
	caption = nested_lookup('caption',response)
	if not caption: return
	instruccion = caption[0]

	#Obtengo contacto y cuenta local
	contacto,CuentaLocal = DeterminaContacto(instruccion)
	if not contacto:
		EnviarTelegram('Contacto mal informado para subir foto!')
		return

	#Link a último archivo recibido
	files = bot.getFile(file_id[TextCounter])
	file_path = nested_lookup('file_path',files)
	file_path = file_path[len(file_path)-1]
	url = 'https://api.telegram.org/file/bot'+token+'/'+file_path

	#Descarga archivo a tu disco
	myfile = requests.get(url)
	mypath = 'ArchivosOperativos/ImagenesRecibidas/'+contacto+'.jpg'
	open(mypath,'wb').write(myfile.content)

	#Subo imagen a chat de Localbitcoins
	calltxt = '/api/contact_message_post/'+contacto+'/'
	f = open(mypath,'rb')
	f.close
	parametros = {'document': f}
	try:
		print(Llave(CuentaLocal).call('POST',calltxt,None,False,parametros).json()['data']['message'])
		ContactoCorto = contacto[len(contacto)-4:len(contacto)]
		cadena = ContactoCorto+'. Imagen subida'
		EnviarTelegram(cadena)
	except: pass
#*************************************************
def TelegramDashboard(instruccion,TelegramProximoID):
	from funciones import EnviarTelegram,DeterminaCuentaLocalbitcoins

	#Determina cuenta de Localbitcoins
	CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
	if not CuentaLocal: return TelegramProximoID

	#Leo Dashboard
	cadena = 'ArchivosOperativos/Dashboard_'+CuentaLocal+'.txt'
	f = open(cadena,'r')
	dash = f.read()
	f.close()
	try: dash = json.loads(dash)
	except: return TelegramProximoID
	if not dash: return TelegramProximoID
	contact_id = nested_lookup('contact_id',dash) #ok
	payment_method = nested_lookup('payment_method',dash) #ok
	amount =  nested_lookup('amount',dash) #ok
	name = nested_lookup('name',dash) #ok
	payment_completed_at = nested_lookup('payment_completed_at',dash)
	username = nested_lookup('username',dash) #ok
	disputed_at = nested_lookup('disputed_at',dash)

	#Imprimo Dashboard
	if not len(contact_id):
		cadena = 'No hay operaciones activas!'
		EnviarTelegram(cadena)
	else:
		name1 = []
		for x in name:
			if CuentaLocal in x: continue
			name1.append(x)
		cadena = ''
		for y in range(len(contact_id)):
			if payment_completed_at[y] == None: estado = 'Esperando Pago'
			elif disputed_at[y] != None: estado = 'En Disputa'
			else: estado = 'Pagado'
			contacto = str(contact_id[y]); ContactoCorto = contacto[len(contacto)-4:len(contacto)]
			cadena = cadena+payment_method[y]+' '+ContactoCorto+' '+name1[y]+' '+str(amount[y])+' '+estado+'\n'
		EnviarTelegram(cadena)

	return TelegramProximoID
#*************************************************
def TelegramContactoAbierto(instruccion,TelegramProximoID):
	from funciones import Llave,EnviarTelegram,LocalCall,LeerArchivoCrearLista,Desarchivador,DeterminaContacto

	#Determino Cuenta Local
	contacto,CuentaLocal = DeterminaContacto(instruccion)
	if not contacto:
		# ~ EnviarTelegram('Contacto mal informado!')
		return TelegramProximoID

	#Leo Dashboard
	f = open('ArchivosOperativos/Dashboard_'+CuentaLocal+'.txt','r')
	dash = f.read()
	f.close()
	try: dash = json.loads(dash)
	except: return
	contact_id = nested_lookup('contact_id',dash)
	amount =  nested_lookup('amount',dash)

	#Loop para revisar operaciones
	for y in range(len(contact_id)):
		#Contacto bien informado?
		ContactoAux = str(contact_id[y]); ContactoCorto = ContactoAux[len(ContactoAux)-4:len(ContactoAux)]
		if contacto!=ContactoAux: continue

		if 'LIBERA' in instruccion.upper() and ':' not in instruccion.upper() and 'DISPUTA' not in instruccion.upper():
			calltxt = '/api/contact_release/'+contacto+'/'
			for m in range(5):
				try: print(Llave(CuentaLocal).call('POST',calltxt).json()['data']['message'])
				except:
					time.sleep(5)
					continue
				else:
					cadena = ContactoCorto+' $'+str(amount[y])+'. Liberada'
					EnviarTelegram(cadena)
					break

			#No se liberó
			if m==4:
				cadena = ContactoCorto+' $'+str(amount[y])+'. Error al liberar'
				EnviarTelegram(cadena)
			continue

		if 'CANCELA' in instruccion.upper() and ':' not in instruccion.upper() and 'DISPUTA' not in instruccion.upper():
			calltxt = '/api/contact_cancel/'+contacto+'/'
			for m in range(5):
				try: print(Llave(CuentaLocal).call('POST',calltxt).json()['data']['message'])
				except:
					time.sleep(5)
					continue
				else:
					cadena = ContactoCorto+' $'+str(amount[y])+'. Cancelada'
					EnviarTelegram(cadena)
					break

			#No se canceló
			if m==4:
				cadena = ContactoCorto+' $'+str(amount[y])+'. Error al cancelar'
				EnviarTelegram(cadena)
			continue

		if 'DISPUTA' in instruccion.upper() and ':' not in instruccion.upper():
			#Evalua si hay mensaje para la disputa
			try: instruccion.index(':')
			except: mensaje = ''
			else:
				mensaje = instruccion[instruccion.index(':'):len(instruccion)]
				mensaje = mensaje.replace(': ','')
				mensaje = mensaje.replace(':','')

			calltxt = '/api/contact_dispute/'+contacto+'/'
			parametros = {'topic':mensaje}
			for m in range(2):
				try: print(Llave(CuentaLocal).call('POST',calltxt,parametros).json()['data']['message'])
				except:	continue
				else: break
			cadena = 'Disputa enviada!'
			EnviarTelegram(cadena)

		if ('INSTRUCCION' or 'INSTRUCCIÓN') in instruccion.upper():
			#Buscás email y MarketName para armar la instrucción
			EmailsOperacionesActivas = LeerArchivoCrearLista('ArchivosOperativos/Emails.txt')
			if not EmailsOperacionesActivas: EmailsOperacionesActivas = ['']
			email = ''; MarketName = ''
			for z in EmailsOperacionesActivas:
				if contacto in z:
					email = z[z.index('#')+1:z.rindex('#')]
					MarketName = z[z.rindex('#')+1:len(z)]
					break
			if not email or not MarketName: continue
			#Preguntás cotización para armar instrucción
			coti,TelegramProximoID = Repreguntador('Cotización?','EsNumero',TelegramProximoID)
			try: float(coti)
			except:	continue
			#Enviás instrucción
			telegrama = ''
			amount1 = str(float(amount[y]))
			cobro = str(int(float(amount[y])*float(coti)))
			if 'compra' in MarketName:	MarketName = MarketName.replace('compra','')
			if 'venta' in MarketName: MarketName = MarketName.replace('venta','')
			if MarketName=='Paypal': telegrama = 'DETALLES DE TU OPERACIÓN\n* Cantidad (USD): '+amount1+'\n* Cotización: '+coti+'\n* Cobro (ARS): '+cobro+'\n--------------------------------------------------\nPAGO\nImporte (USD): '+amount1+'\n1. '+MarketName+' Email: '+email+'\n2. Mensaje: Saldo 1'+'\n3. Si la moneda NO ES DÓLARES, se debe pasar a dólares.'+'\n4. Dirección de envío: No se necesita.'+'\n5. Una vez realizado, enviar captura del envío'
			else: telegrama = 'DETALLES DE TU OPERACIÓN\n* Cantidad (USD): '+amount1+'\n* Cotización: '+coti+'\n* Cobro (ARS): '+cobro+'\n--------------------------------------------------\nPAGO\nImporte (USD): '+amount1+'\n1. '+MarketName+' Email: '+email+'\n2. Finalidad de Pago: Service'+'\n3. Una vez realizado, enviar captura del envío'
			EnviarTelegram(telegrama)

	return TelegramProximoID
#*************************************************
def Repreguntador(cadena,accion,TelegramProximoID):

	def Preguntador(cadena,accion,ProximoID):
		from funciones import EnviarTelegram
		global TelegramProximoID
		TelegramProximoID = ProximoID
		bot = telepot.Bot(token)
		bot2 = telepot.Bot(tokenAugu)
		instruccion = ''

		#Hago pregunta
		EnviarTelegram(cadena)

		#Espero repregunta
		for segundero in range(30):
			#Espera nuevo mensaje de Telegram
			try: response = bot.getUpdates(offset=TelegramProximoID)
			except: continue

			#Determino si hay mensaje nuevo
			update_id = nested_lookup('update_id',response)
			if not update_id: continue
			TelegramProximoID = update_id[len(update_id)-1]+1

			#Nuevo mensaje
			text = nested_lookup('text',response)
			instruccion = text[len(text)-1] #tiene guardado el último mensaje de texto
			print(datetime.now().strftime('%H:%M:%S'),' Telegram nuevo mensaje ',instruccion)

			#Verifica si es número
			if accion=='EsNumero':
				try: float(instruccion)
				except:
					cadena = instruccion+' es inválido!'
					EnviarTelegram(cadena)
					return '',TelegramProximoID
				break

			#Verifica si es monedero
			if accion=='EsMonedero':
				ListaTest = ['TRANSFE2','PAYPAL','TRANSFE','PAYONEER','SKRILL','PAXUM','NETELLER','ZELLE','DEPO','WISE','RIPPLE','ETHEREUM','LITECOIN']
				k = 0
				for j in ListaTest:
					if j in instruccion.upper(): break
					k += 1
				if k==len(ListaTest):
					cadena = instruccion+' no es un monedero válido!'
					EnviarTelegram(cadena)
					return '',TelegramProximoID
				break

			#Verifica si es afirmativo
			if accion=='EsAfirmativo':
				ListaTest = ['SI','SÍ','NO','S','N']
				k = 0
				for j in ListaTest:
					if instruccion.upper()==j:
						instruccion = j
						if instruccion == 'SÍ' or instruccion == 'S': instruccion = 'SI'
						if instruccion == 'N': instruccion = 'NO'
						break
					k += 1
				if k==len(ListaTest):
					cadena = instruccion+' no es válido!'
					EnviarTelegram(cadena)
					return '',TelegramProximoID
				break

			#Cuenta
			if accion=='cuenta': break

		#Telegram
		if segundero == 29:
			cadena = 'No se recibió mensaje'
			EnviarTelegram(cadena)
			return '',TelegramProximoID

		return instruccion,TelegramProximoID
	#*************************************************
	RtaRecibida,TelegramProximoID = Preguntador(cadena,accion,TelegramProximoID)
	if not RtaRecibida: RtaRecibida,TelegramProximoID = Preguntador(cadena,accion,TelegramProximoID)
	return RtaRecibida,TelegramProximoID
#*************************************************
def TelegramCompra(ProximoID):
	from funciones import Llave,LocalCall,EnviarTelegram,BitcoinArgentina,Bitstamp
	global TelegramProximoID
	TelegramProximoID = ProximoID

	#Pregúnta máximo porcentaje para armar tabla
	MaxPorcentaje,TelegramProximoID = Repreguntador('Sobreprecio porcentual máximo (%)? ','EsNumero',TelegramProximoID)
	if not MaxPorcentaje: return TelegramProximoID
	Per1 = int(float(MaxPorcentaje))*10
	Per2 = Per1-45
	Per3 = Per2-45

	#Argentina
	PrecioArgentina = BitcoinArgentina()

	#Stamp
	USDstamp = Bitstamp('bitstampusd')

	#Mercados
	cadena = ''
	mercados = ['Paypal','Payoneer','Neteller','Moneybookers-skrill']
	for z in mercados:
		LBTC = '/sell-bitcoins-online/usd/' + z.lower() + '/.json'
		PrecioTodos = LocalCall(LBTC)
		cadena = cadena + z + ' \t   Mínimo   Máximo\n'
		for x in range (0,3):
			#Porcentaje
			Precio = float(nested_lookup('temp_price',PrecioTodos)[x])
			Porcentaje = (Precio / USDstamp - 1)*100
			cadena = cadena + str(round(Porcentaje,2)) + '%              '
			#Mínimo
			try: min_amount = float(nested_lookup('min_amount',PrecioTodos)[x])
			except: min_amount = 0
			cadena = cadena + str(int(min_amount)) + '           '
			#Máximo
			try: max_amount = float(nested_lookup('max_amount',PrecioTodos)[x])
			except: max_amount = 1000
			cadena = cadena + str(int(max_amount)) + '\n'
		cadena = cadena + '\n'

	#Titulo 1
	Titulo = 'Sobreprecio%'
	for z in range (Per1,Per2,-5): Titulo = Titulo + ' ' + str(z/10) + '   \t'
	cadena = cadena + Titulo + '\n'
	#Cuadro de Rentabilidad 1
	for x in range (5,16,1):
		Rentabilidad = 'Renta ' + str(x) + '%      '
		for y in range (Per1,Per2,-5):
			venta = PrecioArgentina*0.99
			compra = USDstamp*1.01*(1+y/1000)*(1+x/100)
			CotiCompra = int(venta / compra)
			Rentabilidad = Rentabilidad + str(CotiCompra) + '   \t'
		cadena = cadena + Rentabilidad + '\n'

	#Titulo 2
	Titulo = '\nSobreprecio%'
	for z in range (Per2,Per3,-5): Titulo = Titulo + ' ' + str(z/10) + '   \t'
	cadena = cadena + Titulo + '\n'

	#Cuadro de Rentabilidad 2
	for x in range (5,16,1):
		Rentabilidad = 'Renta ' + str(x) + '%      '
		for y in range (Per2,Per3,-5):
			venta = PrecioArgentina*0.99
			compra = USDstamp*1.01*(1+y/1000)*(1+x/100)
			CotiCompra = int(venta / compra)
			Rentabilidad = Rentabilidad + str(CotiCompra) + '   \t'
		cadena = cadena + Rentabilidad + '\n'

	#Telegram
	EnviarTelegram(cadena)

	return TelegramProximoID
#*************************************************
def TelegramCompraPaytiz():
	from funciones import Llave,LocalCall,EnviarTelegram,BitcoinArgentina,Bitstamp
	cadena = ''

	#Determino precio de Tether
	PrecioArgentina = BitcoinArgentina()
	USDstamp = Bitstamp('bitstampusd')
	USDT  = str(int(PrecioArgentina/USDstamp))
	cadena = 'USDT ' + USDT + '\n\n'

	#Stamp
	while True:
		try: USDstamp = float(Llave().call('GET','/api/equation/bitstampusd').json()['data'])
		except: continue
		else: break

	# ~ #Cuadro de Rentabilidad 5%
	# ~ cadena = cadena + 'Descuento 5%\n'
	# ~ for x in range (10,16,1):
		# ~ Rentabilidad = 'Renta ' + str(x) + '%      '
		# ~ venta = PrecioArgentina*0.99
		# ~ compra = USDstamp*(1+x/100)/(1-0.05)*1.01
		# ~ CotiCompra = int(venta / compra)
		# ~ Rentabilidad = Rentabilidad + str(CotiCompra) + '   \t'
		# ~ cadena = cadena + Rentabilidad + '\n'

	# ~ #Cuadro de Rentabilidad 7%
	# ~ cadena = cadena + '\nDescuento 7%\n'
	# ~ for x in range (10,16,1):
		# ~ Rentabilidad = 'Renta ' + str(x) + '%      '
		# ~ venta = PrecioArgentina*0.99
		# ~ compra = USDstamp*(1+x/100)/(1-0.07)*1.01
		# ~ CotiCompra = int(venta / compra)
		# ~ Rentabilidad = Rentabilidad + str(CotiCompra) + '   \t'
		# ~ cadena = cadena + Rentabilidad + '\n'

	#Cuadro de Rentabilidad 10%
	cadena = cadena + '\nDescuento 10%\n'
	for x in range (10,16,1):
		Rentabilidad = 'Renta ' + str(x) + '%      '
		venta = PrecioArgentina
		compra = USDstamp*(1+x/100)/(1-0.10)
		CotiCompra = int(venta / compra)
		Rentabilidad = Rentabilidad + str(CotiCompra) + '   \t'
		cadena = cadena + Rentabilidad + '\n'

	#Telegram
	EnviarTelegram(cadena)
#*************************************************
def TelegramBook(instruccion,DesdeDonde=''):
	#Variables
	from funciones import Llave,LocalCall,EnviarTelegram

	#Busca currency
	currencies = ['ARS','USD','EUR','CAD','BRL','ZAR','AUD','GBP','PAB','COP','CLP','RBL','PAYPAL','PAYONEER','PAXUM','SKRILL','NETELLER','ZELLE','ETH','XRP','']
	Local = True;	cadena = ''; instruccion = instruccion.upper(); Altcoin = False
	for currency in currencies:
		if currency in instruccion: break
	if currency=='SKRILL': currency = 'MONEYBOOKERS-SKRILL'
	if currency=='':
		EnviarTelegram('Mercado mal informado!')
		return
	if len(currency)>3 or currency=='ETH' or currency=='XRP':
		Local = False
		if currency=='ETH' or currency=='XRP': Altcoin = True

	#Encuentro umbral de oferentes a considerar
	if not Altcoin:
		if Local: calltxt = '/api/equation/bitstampusd*USD_in_' + currency.upper()
		else: calltxt = '/api/equation/bitstampusd'
		umbral = float(Llave().call('GET',calltxt).json()['data'])*0.005

	#ASK
	#Obtiene datos
	if Local:
		if currency=='CAD': market = '/buy-bitcoins-online/cad/interac-e-transfer/.json'
		else: market = '/buy-bitcoins-online/' + currency + '/national-bank-transfer/.json'
	elif currency=='ETH': market = '/buy-bitcoins-online/eth/ethereum-altcoin/.json'
	elif currency=='XRP': market = '/buy-bitcoins-online/xrp/ripple-altcoin/.json'
	else: market = '/buy-bitcoins-online/usd/' + currency.lower() + '/.json'
	AvisosTerceros = LocalCall(market)
	precio = nested_lookup('temp_price',AvisosTerceros)
	maximo = nested_lookup('max_amount_available',AvisosTerceros)
	trade_count = nested_lookup('trade_count',AvisosTerceros)

	#Ordena markets, transforma lista de precios en números y los ordena
	precio1 = []
	for j in precio: precio1.append(float(j))
	precio = precio1

	#Busca anunciante a vencer
	avisos =  10
	if len(maximo) < 10: avisos = len(maximo)
	for i in range(avisos-1,-1,-1):
		#Oferentes sin stock
		if Altcoin:
			if not maximo[i]: maximo[i] = '1000'
		else:
			if not maximo[i]: maximo[i] = '10000000'
			if float(maximo[i]) <= umbral: continue

		#Anunciante Novato
		if trade_count[i]=='+30' or not '+' in trade_count[i]: continue

		#ASK
		ASK = precio[i]

		#Almacena Orderbook
		if Altcoin: cadena = cadena + str(round(precio[i],2)) + '\t' + str(int(float(maximo[i]))) + '\n'
		else: cadena = cadena + str(int(precio[i])) + '\t' + str(int(float(maximo[i]))) + '\n'

	#BID
	#Obtiene datos
	if Local:
		if currency=='CAD': market = '/sell-bitcoins-online/cad/interac-e-transfer/.json'
		else: market = '/sell-bitcoins-online/' + currency + '/national-bank-transfer/.json'
	elif currency=='ETH': market = '/sell-bitcoins-online/eth/ethereum-altcoin/.json'
	elif currency=='XRP': market = '/sell-bitcoins-online/xrp/ripple-altcoin/.json'
	else: market = '/sell-bitcoins-online/usd/' + currency.lower() + '/.json'
	AvisosTerceros = Llave().call('GET',market).json()
	precio = nested_lookup('temp_price',AvisosTerceros)
	maximo = nested_lookup('max_amount_available',AvisosTerceros)
	trade_count = nested_lookup('trade_count',AvisosTerceros)

	#Ordena markets, transforma lista de precios en números y los ordena
	precio1 = []
	for j in precio: precio1.append(float(j))
	precio = precio1

	#Busca anunciante a vencer
	cadena = cadena + '\n'
	avisos =  10; PriceFind = False
	if len(maximo) < 10: avisos = len(maximo)
	for i in range(avisos):
		#Oferentes sin stock
		if Altcoin:
			if not maximo[i]: maximo[i] = '1000'
		else:
			if not maximo[i]: maximo[i] = '10000000'
			if float(maximo[i]) <= umbral: continue

		#Anunciante Novato
		if trade_count[i]=='+30' or not '+' in trade_count[i]: continue

		#BID
		if not PriceFind:
			BID = precio[i]
			PriceFind = True

		#Almacena Orderbook
		if Altcoin: cadena = cadena + str(round(precio[i],2)) + '\t' + str(int(float(maximo[i]))) + '\n'
		else: cadena = cadena + str(int(precio[i])) + '\t' + str(int(float(maximo[i]))) + '\n'

	#Calcula Spread
	ASKcomi = ASK*0.99; BIDcomi = BID*1.01
	spread = ((ASKcomi/BIDcomi)-1)
	cadena = currency + ' ' + str(round(spread*100,2)) + '%\n' + cadena

	#Informa Resultado
	if DesdeDonde != '' : return spread
	EnviarTelegram(cadena)
#*************************************************
def TelegramChat(instruccion):
	#Variables
	from funciones import Llave,LocalCall,EnviarTelegram,DeterminaContacto

	#Obtengo contacto y cuenta local
	contacto,CuentaLocal = DeterminaContacto(instruccion)
	if not contacto:
		EnviarTelegram('Contacto mal informado para solicitar chat!')
		return

	#Solicita el chat
	calltxt = '/api/contact_messages/'+contacto +'/'
	TradeChat = LocalCall(calltxt,CuentaLocal)
	messages = nested_lookup('msg',TradeChat)
	if not messages: return

	#Elabora el chat
	ContactoCorto = contacto[len(contacto)-4:len(contacto)]
	chat = 'Chat ' + ContactoCorto +'\n\n'
	counter = 1
	for message in messages:
		if not message: continue
		chat += str(counter) + '. ' + message + '\n---------------------------\n'
		counter += 1
	EnviarTelegram(chat)
#*************************************************
def TelegramVolume(instruccion):
	#Variables
	from funciones import Llave,LocalCall,EnviarTelegram,Bitstamp

	#Busca currency
	currencies = ['ARS','USD','EUR','CAD','BRL','ZAR','AUD','GBP','PAB','COP','CLP','RBL','ETH','XRP','']
	for currency in currencies:
		if currency in instruccion.upper(): break
	if currency=='':
		EnviarTelegram('Mercado mal informado!')
		return

	#Recorre book para última semana
	LimitTime = time.time()-604800; 	Limit_tid = None; contador = 0; acumulado = 0; encontrado = False
	while True:
		parametros = {'max_tid':Limit_tid}
		try: book = Llave().call('GET','/bitcoincharts/'+currency+'/trades.json',parametros).json()
		except:
			EnviarTelegram('Error al tratar de obtener ordenes!')
			return
		amount = nested_lookup('amount',book)
		date = nested_lookup('date',book)
		tid = nested_lookup('tid',book)
		for x in range(len(amount)):
			if date[x] < LimitTime:
				encontrado = True
				break
			acumulado += float(amount[x]); contador += 1
		if encontrado == True: break
		Limit_tid = min(tid)-1
	cadena = currency + '\nAcumulado semana: ' + str(round(acumulado,2)) + ' BTC\nOperaciones semana: ' + str(contador)

	#Determina potencial renta mensual
	spread = TelegramBook(currency,'Volume')
	USDstamp = Bitstamp('bitstampusd')
	RentaMes = int(acumulado*spread*USDstamp*4)
	cadena = cadena + '\nSpread: ' + str(round(spread*100,2)) + '%\nRenta mes: $' + str(RentaMes)
	EnviarTelegram(cadena)
#*************************************************
def TelegramVolumen24(instruccion):
	#Variables
	from funciones import Llave,LocalCall,EnviarTelegram,Bitstamp

	#Busca currency
	currencies = ['ARS','USD','EUR','CAD','BRL','ZAR','AUD','GBP','PAB','COP','CLP','RBL','ETH','XRP','LTC']
	for currency in currencies:
		if currency in instruccion.upper(): break
	if currency=='':
		EnviarTelegram('Mercado mal informado!')
		return

	#Busca precio del bitcoin
	USDstamp = Bitstamp('bitstampusd')

	#Recorre book para última semana
	LimitTime = time.time()-604800; Limit_tid = None; contador = 0; acumulado = 0; encontrado = False
	cadena = 'Nro   \tHora         \tImporte (USD)\tAcumulado (USD)\n'

	while True:
		#Variables iniciales
		parametros = {'max_tid':Limit_tid}
		try: book = Llave().call('GET','/bitcoincharts/'+currency+'/trades.json',parametros).json()
		except:
			EnviarTelegram('Error al tratar de obtener ordenes de las últimas 24hs!')
			return
		amount = nested_lookup('amount',book)
		date = nested_lookup('date',book)
		tid = nested_lookup('tid',book)

		#Recorre ciclo de 500 operaciones
		for x in range(len(amount)):
			if date[x] < LimitTime:
				encontrado = True
				break

			#Suma cada nueva operación
			acumulado += float(amount[x])*USDstamp; contador += 1

			#Elabora cadena
			cadena = cadena + str(contador) + '       ' + time.strftime('%d%m-%H:%M', time.localtime(date[x])) + '   \t' + str(int(float(amount[x])*USDstamp)) + '        \t' + str(int(acumulado)) + '\n'

		#Se llegó a 24hs y se corta el ciclo
		if encontrado == True: break

		#Se actualiza contador tid
		Limit_tid = min(tid)-1

	#Presenta resultado
	print(cadena)
#*************************************************
def TelegramLBTCtransacciones(instruccion,TelegramProximoID):
	#Variables
	from funciones import LocalCall,EnviarTelegram,DeterminaCuentaLocalbitcoins

	#Determina cuenta de Localbitcoins
	CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
	if not CuentaLocal: return TelegramProximoID

	#Obtengo transacciones recibidas en local
	try: Wallet = LocalCall('/api/wallet/',CuentaLocal)['data']['received_transactions_30d']
	except: return TelegramProximoID
	amount = nested_lookup('amount',Wallet)
	created_at = nested_lookup('created_at',Wallet)
	description = nested_lookup('description',Wallet)

	#Filtro transacciones desde el exterior
	cadena = 'Fecha                          Cantidad\n'; contador = 0
	for x in range(len(amount)-1,-1,-1):
		if 'Contact' in description[x]: continue
		fecha = str(datetime.strptime(datetime.fromisoformat(created_at[x]).strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S'))
		cadena = cadena + fecha + '   ' + amount[x] + '\n'
		contador += 1
		if contador >= 5: break

	#Presento resultado
	EnviarTelegram(cadena)
	return TelegramProximoID
#*************************************************
def TelegramLBTCextraer(instruccion,TelegramProximoID):
	#Variables
	from funciones import EnviarTelegram,Llave,DeterminaCuentaLocalbitcoins,LocalCall

	#Determina cuenta de Localbitcoins
	CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
	if not CuentaLocal: return TelegramProximoID

	#Localbitcoins balance
	LBTCbalance = LocalCall('/api/wallet-balance/',CuentaLocal)
	try: LBTCbalance = round(float(nested_lookup('balance',LBTCbalance)[0]),8)
	except: LBTCbalance = 0

	#Localbitcoins Fees
	try: fees = LocalCall('/api/fees/',CuentaLocal)['data']
	except: pass
	LBTCfee = float(fees.get('outgoing_fee'))

	#Localbitcoins cántidad máxima que se puede extraer
	LBTCmax = round(LBTCbalance - LBTCfee,8)

	#Pregunta cantidad a enviar
	cadena = 'Cántidad de bitcoin a enviar?\nMáxima cantidad a extraer = ' + str(LBTCmax)
	AmountSent,TelegramProximoID = Repreguntador(cadena,'EsNumero',TelegramProximoID)
	if not AmountSent: return TelegramProximoID
	AmountSent = round(float(AmountSent),8)

	#Pregunta dirección a la que enviar
	deposit_address,TelegramProximoID = Repreguntador('Dirección a la que enviar?\nBinance = 19UyhZuvkT12hnXAyXc8VmiLiuYRKiWdJc','cuenta',TelegramProximoID)
	if not deposit_address: return TelegramProximoID

	#Envia bitcoins a Binance
	parametros = {'address':deposit_address,'amount':AmountSent}
	for m in range(3):
		try: print(Llave(CuentaLocal).call('POST','/api/wallet-send/',parametros).json()['data']['message'])
		except Exception as e:
			print(e)
			continue
		else:
			#Telegram informando éxito
			cadena = str(AmountSent)+' btc enviados a '+deposit_address
			EnviarTelegram(cadena)
			break

	return TelegramProximoID
#*************************************************
def TelegramHora(instruccion,TelegramProximoID):
	#Variables
	from funciones import Llave,EnviarTelegram,DatosMercado,LocalCall,DeterminaCuentaLocalbitcoins

	#Determina cuenta de Localbitcoins
	CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
	if not CuentaLocal: return TelegramProximoID
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(instruccion,CuentaLocal)

	#Determina si activa o desactiva horario
	HorarioActivo = True
	if 'NO' in instruccion.upper(): HorarioActivo = False

	#No se informó mercado
	if not MarketName:
		#avisos utilizados regularmente
		if CuentaLocal == 'Saldo1': avisos = [475496,488773,494501,622297,895691,1115387,1275609,1279728,1290393,1296303,1350190]
		if CuentaLocal == 'MAVE45': avisos = [1386978,1386835,1386981,1389093,1386980,1386979]

		#Se desactiva horario en todos los avisos
		if not HorarioActivo:
			for aviso in avisos:
				z = LocalCall('/api/ad-get/'+str(aviso)+'/',CuentaLocal)
				parametros = {
				'opening_hours':None,
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
				'min_amount':float(nested_lookup('min_amount',z)[0]),
				'max_amount':float(nested_lookup('max_amount',z)[0]),
				'visible':nested_lookup('visible',z)[0]}
				print(Llave(CuentaLocal).call('POST','/api/ad/'+str(aviso)+'/',parametros).json())
				print(Llave(CuentaLocal).call('POST','/api/ad/'+str(aviso)+'/',parametros).json()['data']['message'])
			cadena = 'Franja horaria desactivada en todos los avisos!'

		#Se activa horario en todos los avisos visibles
		else:
			for aviso in avisos:
				#Determina si cada aviso es visible para activarle el horario
				try: z = LocalCall('/api/ad-get/'+str(aviso)+'/',CuentaLocal)
				except: continue
				visible = nested_lookup('visible',z)[0]
				if not visible: continue

				#Obtenés horas según aviso
				if CuentaLocal == 'Saldo1': AvisosAccionadosxTerceros = [475496,494501,622297,1094283,1115387,1279728] #Son los avisos en que un cliente hace el envío. Ej: Paypal, Paxum
				if CuentaLocal == 'MAVE45': AvisosAccionadosxTerceros = [1386978,1389093,1386979]
				contador = 0
				for AvisoTercero in AvisosAccionadosxTerceros:
					#Es aviso accionado por terceros
					if aviso==AvisoTercero:
						opening_hours = '[[44,92],[36,92],[36,92],[36,92],[36,92],[36,92],[40,88]]'
						break
					contador += 1
				#Es aviso accionado por vos
				if contador == len(AvisosAccionadosxTerceros): opening_hours = '[[32,96],[32,96],[32,96],[32,96],[32,96],[32,96],[32,96]]'

				#Se activa horario en el aviso indicado
				parametros = {
				'opening_hours':opening_hours,
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
				'min_amount':float(nested_lookup('min_amount',z)[0]),
				'max_amount':float(nested_lookup('max_amount',z)[0]),
				'visible':nested_lookup('visible',z)[0]}
				print(Llave(CuentaLocal).call('POST','/api/ad/'+str(aviso)+'/',parametros).json())
				print(Llave(CuentaLocal).call('POST','/api/ad/'+str(aviso)+'/',parametros).json()['data']['message'])
			cadena = 'Franja horaria activada en todos los avisos activos!'

		#Envía mensaje
		EnviarTelegram(cadena)
		return TelegramProximoID

	#Determina si activa o desactiva horario
	if HorarioActivo:
		#Obtenés horas según aviso
		if CuentaLocal == 'Saldo1': AvisosAccionadosxTerceros = [475496,494501,622297,1094283,1115387,1279728]
		if CuentaLocal == 'MAVE45': AvisosAccionadosxTerceros = [1386978,1389093,1386979]
		contador = 0
		for aviso in AvisosAccionadosxTerceros:
			#Es aviso accionado por terceros
			if NumAviso==str(aviso):
				opening_hours = '[[44,92],[36,92],[36,92],[36,92],[36,92],[36,92],[40,88]]'
				break
			contador += 1

		#Es aviso accionado por vos
		if contador == len(AvisosAccionadosxTerceros): opening_hours = '[[32,96],[32,96],[32,96],[32,96],[32,96],[32,96],[32,96]]'
	else: opening_hours = None

	#Se activa horario en el aviso indicado
	z = LocalCall('/api/ad-get/'+NumAviso+'/',CuentaLocal)
	parametros = {
	'opening_hours':opening_hours,
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
	# ~ 'track_max_amount':bool(nested_lookup('track_max_amount',z)[0]),
	'require_trusted_by_advertiser':bool(nested_lookup('require_trusted_by_advertiser',z)[0]),
	'require_identification':bool(nested_lookup('require_identification',z)[0]),
	'min_amount':float(nested_lookup('min_amount',z)[0]),
	'max_amount':float(nested_lookup('max_amount',z)[0]),
	'visible':nested_lookup('visible',z)[0]}

	print(Llave(CuentaLocal).call('POST','/api/ad/'+NumAviso+'/',parametros).json()['data']['message'])
	if HorarioActivo == True: cadena = 'Franja horaria activada en ' + MarketName
	else: cadena = 'Franja horaria desactivada en ' + MarketName
	EnviarTelegram(cadena)

	return TelegramProximoID
#*************************************************
def TelegramUmbrales(instruccion,TelegramProximoID):
	from funciones import EnviarTelegram,Llave,LocalCall,SelectorMinimoMaximo,DeterminaCuentaLocalbitcoins

	#Determina cuenta de Localbitcoins
	CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
	if not CuentaLocal: return TelegramProximoID

	#Ver umbrales
	if 'VER' in instruccion.upper():
		with open('ArchivosOperativos/'+CuentaLocal+'_UmbralPublicacionVisible.txt') as f:
			UmbralPublicacionVisible = float(f.readlines()[0])
			f.close()
		with open('ArchivosOperativos/'+CuentaLocal+'_UmbralDividePago.txt') as f:
			UmbralDividePago = float(f.readlines()[0])
			f.close()
		cadena = 'Umbral Publicacion Visible ' + str(int(UmbralPublicacionVisible)) + '.  Umbral Dividir Pago ' + str(int(UmbralDividePago))
		EnviarTelegram(cadena)
		return TelegramProximoID

	#Modificar umbrales
	if 'MODIFICAR' in instruccion.upper():
		#Encuentro umbrales de referencia
		while True:
			try: ARSstamp = round(float(Llave(CuentaLocal).call('GET','/api/equation/bitstampusd*USD_in_ARS').json()['data']))
			except: continue
			else: break
		ReferenciaPublicacionVisible = int(ARSstamp*0.005)		#15000
		ReferenciaDividePago = int(ReferenciaPublicacionVisible*3)	#40000

		#Pregunta nueve umbral para aviso visible
		cadena = 'Importe mínimo para que el aviso sea visible? '
		UmbralPublicacionVisible,TelegramProximoID = Repreguntador(cadena,'EsNumero',TelegramProximoID)
		if not UmbralPublicacionVisible: return TelegramProximoID
		UmbralPublicacionVisible = int(float(UmbralPublicacionVisible))

		#Modifico archivo UmbralPublicacionVisible
		f = open('ArchivosOperativos/'+CuentaLocal+'_UmbralPublicacionVisible.txt','w')
		f.write(str(UmbralPublicacionVisible))
		f.close()

		#Pregunta nueve umbral para dividir importe
		cadena = 'Importe a partir del cual se divide en dos? '
		UmbralDividePago,TelegramProximoID = Repreguntador(cadena,'EsNumero',TelegramProximoID)
		if not UmbralDividePago: return TelegramProximoID
		UmbralDividePago = int(float(UmbralDividePago))

		#Modifico archivo UmbralDividePago
		f = open('ArchivosOperativos/'+CuentaLocal+'_UmbralDividePago.txt','w')
		f.write(str(UmbralDividePago))
		f.close()

		#Informa en Telegram
		cadena = 'Umbrales actualizados! Se inicia modificación de avisos activos!'
		EnviarTelegram(cadena)

		#Determina qué avisos están activos para modificar los importes
		if CuentaLocal == 'Saldo1': aviso = [488773,895691,1296303]; MarketName = ['Transfe','Transfe2','Depo']
		if CuentaLocal == 'MAVE45': aviso = [1386835,1386981]; MarketName = ['Transfe','Depo']

		for x in range(len(aviso)):
			#Verifico visibilidad
			try: z = LocalCall('/api/ad-get/'+str(aviso[x])+'/',CuentaLocal)
			except: continue
			visible = nested_lookup('visible',z)[0]
			if not visible: continue

			#Se actualiza publicación con nuevos umbrales
			SelectorMinimoMaximo(MarketName[x],CuentaLocal)

		#Informa en Telegram
		cadena = 'Avisos activos modificados!'
		EnviarTelegram(cadena)

	return TelegramProximoID
#*************************************************
def TelegramMailing(instruccion,TelegramProximoID):
	#Variables
	from funciones import Llave,LocalCall,EnviarTelegram,DatosMercado,CuentaLocalbitcoins

	#Pregunta cuenta de Localbitcoins
	TelegramProximoID,CuentaLocal = CuentaLocalbitcoins(TelegramProximoID)

	#Datos mercado
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(instruccion,CuentaLocal)
	if not MarketName: return TelegramProximoID

	#Telegram
	cadena = 'Preparando mailing en ' + MarketName + '!'
	EnviarTelegram(cadena)

	#Determina Mercado
	MercadoBuscado = ''
	if MarketName=='Depo':
		MercadoBuscado = 'CASH_DEPOSIT'
		mensaje = 'Hola, estamos vendiendo bitcoins por DEPÓSITO:\n\n\nhttps://localbitcoins.com/ad/'+NumAviso
	if MarketName=='Transfe2':
		MercadoBuscado = 'OTHER'
		mensaje = 'Hola, estamos vendiendo bitcoins al mejor precio de Locabitcoins por TRANSFERENCIA BANCARIA:\n\n\nhttps://localbitcoins.com/ad/'+NumAviso
	if MarketName=='Transfe':
		MercadoBuscado = 'NATIONAL_BANK'
		mensaje = 'Hola, estamos vendiendo bitcoins al mejor precio de Locabitcoins por TRANSFERENCIA BANCARIA:\n\n\nhttps://localbitcoins.com/ad/'+NumAviso
	if MarketName=='Paxum':
		MercadoBuscado = 'PAXUM'
		mensaje = 'Hello, buying bitcoins with Paxum:\n\n\nhttps://localbitcoins.com/ad/'+NumAviso
	if MarketName=='Paypal':
		MercadoBuscado = 'PAYPAL'
		mensaje = 'Hello, buying bitcoins with Paypal:\n\n\nhttps://localbitcoins.com/ad/'+NumAviso
	if MarketName=='Payoneer':
		MercadoBuscado = 'PAYONEER'
		mensaje = 'Hello, buying bitcoins with Payoneer:\n\n\nhttps://localbitcoins.com/ad/'+NumAviso
	if MercadoBuscado=='':
		EnviarTelegram('Mercado Inexistente')
		return

	#Busca últimas operaciones
	LastTrades = LocalCall('/api/dashboard/released/',CuentaLocal)
	payment_method = nested_lookup('payment_method',LastTrades)
	contact_id = nested_lookup('contact_id',LastTrades)
	username = nested_lookup('username',LastTrades)

	#Limpia username
	username1 = []
	for x in range(len(username)):
		if username[x]==CuentaLocal: continue
		username1.append(username[x])

	#Elabora mailing
	mailing=[]; username2=[]
	for x in range(len(payment_method)):
		if payment_method[x] == MercadoBuscado and username1[x] not in username2:
			username2.append(username1[x])
			mailing.append(contact_id[x])

	#Envía mailing
	cadena = ''
	for x in range(len(mailing)):
		time.sleep(1)
		calltxt = '/api/contact_message_post/'+str(mailing[x])+'/'
		parametros = {'msg':mensaje}
		try: Llave(CuentaLocal).call('POST',calltxt,parametros).json()
		except:
			cadena = cadena + str(username2[x]).upper() + ' error\n'
			continue
		cadena = cadena + str(username2[x]).upper() + ' enviado\n'

	#Telegram
	if cadena == '': cadena = 'Sin contactos para mailing en ' + MarketName + '!'
	EnviarTelegram(cadena)

	return TelegramProximoID
#*************************************************
def TelegramCoti(instruccion):
	#Variables
	from funciones import EnviarTelegram

	#Cotización base
	coti = re.findall(r'[-+]?\d*\.?\d+|\d+',instruccion)
	if not coti:
		EnviarTelegram('Cotización mal informada!')
		return
	coti = int(float(coti[0]))

	#Telegram
	cadena = '1000 ó más ' + str(coti) + '\n500 a 1000 ' + str(coti-1) + '\n200 a 500  ' + str(coti-2)
	EnviarTelegram(cadena)
#*************************************************
def TelegramAviso(instruccion,TelegramProximoID):
	#Variables
	from funciones import Llave,LocalCall,EnviarTelegram,DatosMercado,DeterminaCuentaLocalbitcoins

	#Determina cuenta de Localbitcoins
	CuentaLocal,TelegramProximoID = DeterminaCuentaLocalbitcoins(instruccion,TelegramProximoID)
	if not CuentaLocal: return TelegramProximoID

	#Datos mercado
	market1,market2,market3,NumAviso,EcuacionPrecio,BitRel,MarketName = DatosMercado(instruccion,CuentaLocal)
	if not MarketName: return TelegramProximoID

	#Telegram
	cadena = 'https://localbitcoins.com/ad/' + NumAviso
	EnviarTelegram(cadena)

	return TelegramProximoID
#*************************************************
def TelegramClienteVenta(instruccion,ProximoID):
	#Variables
	from funciones import EnviarTelegram
	global TelegramProximoID
	TelegramProximoID = ProximoID

	#Pregúnta quién firma
	Firmante,TelegramProximoID = Repreguntador('Quién firma (Andrés/Augusto)? ','cuenta',TelegramProximoID)
	if not Firmante: return TelegramProximoID

	#Cotizaciones
	coti = re.findall(r'[-+]?\d*\.?\d+|\d+',instruccion)
	if not coti:
		EnviarTelegram('Cotización no informada!')
		return
	coti = int(float(coti[0]))
	cotizaciones = '1000 ó más ' + str(coti) + '\n500 a 1000 ' + str(coti-1) + '\n200 a 500  ' + str(coti-2) + '\n\n'

	#Telegram
	cadena1 = 'Gracias por el contacto.\n\nEl saldo lo enviás a otra cuenta mediante email. Te pagamos en cuenta bancaria, Mercado Pago, Ualá o dónde nos indiques tuya o de terceros.\n\n'
	cadena2 = 'Te paso tasas que dependen de la cantidad de dólares que cambiás. No hay ninguna comisión adicional.\n\n'+cotizaciones+'En Google, Facebook y en la web, hay muchas referencias. Usás preferiblemente WSP.\n\n'
	if Firmante.upper()=='ANDRÉS' or Firmante.upper()=='ANDRES': cadena3 = 'Andrés\nSALDO 1\nWSP: +5491138095573\nhttps://www.saldo1.com.ar\nGoogle: Saldo1\nFacebook: https://www.facebook.com/Saldo.Uno/reviews'
	elif Firmante.upper()=='AUGUSTO': cadena3 = 'Augusto\nSALDO 1\nWSP: +5491162174892\nhttps://www.saldo1.com.ar\nGoogle: Saldo1\nFacebook: https://www.facebook.com/Saldo.Uno/reviews'
	else: cadena3 = 'SALDO 1\nWSP: +5491162174892\nhttps://www.saldo1.com.ar\nGoogle: Saldo1\nFacebook: https://www.facebook.com/Saldo.Uno/reviews'
	cadena = cadena1 + cadena2 + cadena3
	EnviarTelegram(cadena)

	return TelegramProximoID
#*************************************************
def TelegramClienteCompra(instruccion,ProximoID):
	#Variables
	from funciones import EnviarTelegram
	global TelegramProximoID
	TelegramProximoID = ProximoID

	#Pregúnta quién firma
	Firmante,TelegramProximoID = Repreguntador('Quién firma (Andrés/Augusto)? ','cuenta',TelegramProximoID)
	if not Firmante: return TelegramProximoID

	#Cotizaciones
	coti = re.findall(r'[-+]?\d*\.?\d+|\d+',instruccion)
	if not coti:
		EnviarTelegram('Cotización mal informada!')
		return
	coti = str(int(float(coti[0])))

	#Telegram
	cadena1 = 'Gracias por el contacto. $'+coti+' por dólar.\n\nPagás en cuenta bancaria o Rapipago. Mercado Pago con saldo en cuenta o bitcoin.\n\n'
	cadena2 = 'En Google, Facebook y en la web, hay muchas referencias. Usás preferiblemente WSP.\n\n'
	if Firmante.upper()=='ANDRÉS' or Firmante.upper()=='ANDRES': cadena3 = 'Andrés\nSALDO 1\nWSP: +5491138095573\nhttps://www.saldo1.com.ar\nGoogle: Saldo1\nFacebook: https://www.facebook.com/Saldo.Uno/reviews'
	elif Firmante.upper()=='AUGUSTO': cadena3 = 'Augusto\nSALDO 1\nWSP: +5491162174892\nhttps://www.saldo1.com.ar\nGoogle: Saldo1\nFacebook: https://www.facebook.com/Saldo.Uno/reviews'
	else: cadena3 = 'SALDO 1\nWSP: +5491162174892\nhttps://www.saldo1.com.ar\nGoogle: Saldo1\nFacebook: https://www.facebook.com/Saldo.Uno/reviews'
	cadena = cadena1 + cadena2 + cadena3
	EnviarTelegram(cadena)

	return TelegramProximoID
#*************************************************
def TelegramClienteDatos(instruccion):
	#Variables
	from funciones import EnviarTelegram

	#Telegram
	cadena0 = 'Tu nombre completo para agregarte a WSP?\n\n'
	cadena1 = 'Lo cargamos y cuando hay un pedido por importe aproximado, te pasamos instrucciones. Recibís tu pago en el mismo día o al siguiente.\n\n'
	cadena2 = 'La info que necesitamos para pagarte es ésta por favor:\n\n'
	cadena3 = 'BANCO\nTipo y Nro de Cuenta\nTitular\nCBU\nCUIL\nEmail\n\n'
	cadena = cadena0 + cadena1 + cadena2 + cadena3

	EnviarTelegram(cadena)
#*************************************************
def TelegramPaytiz(ProximoID):
	from funciones import EnviarTelegram
	global TelegramProximoID
	TelegramProximoID = ProximoID

	#Pregunta cantidad de pagos
	CantidadPagos,TelegramProximoID = Repreguntador('Cantidad de envíos? ','EsNumero',TelegramProximoID)
	if not CantidadPagos: return TelegramProximoID

	#Pregunta cotización
	Cotizacion,TelegramProximoID = Repreguntador('Cotizacion? ','EsNumero',TelegramProximoID)
	if not Cotizacion: return TelegramProximoID

	#Solicita emails de cada pago
	Pagos = 0; cadena = ''; Total = 0
	for y in range(int(CantidadPagos)):
		#Pregunta info para pago
		Informacion,TelegramProximoID = Repreguntador('Email y cantidad para el Pago '+str(y+1)+'?','cuenta',TelegramProximoID)
		if not Informacion:
			EnviarTelegram('No se pudo obtener el email o la cantidad!')
			return TelegramProximoID
		try:
			email = re.findall('([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)',Informacion)
			email = email[0]
		except:
			EnviarTelegram('No se pudo obtener el email!')
			return TelegramProximoID
		try: cantidad = re.findall(r'[-+]?\d*\.?\d+\s|\s[-+]?\d*\.?\d+',Informacion)
		except:
			EnviarTelegram('No se pudo obtener la cantidad!')
			return TelegramProximoID
		if not cantidad:
			EnviarTelegram('No se pudo obtener la cantidad!')
			return TelegramProximoID
		cantidad = cantidad[len(cantidad)-1]
		if email and cantidad:
			Pagos = Pagos + 1
			Total = round(Total + float(cantidad),2)
			cadena = cadena+'\n--------------------------------------------------\nPAGO '+str(Pagos)+'\n'+'Importe (USD): '+cantidad+'\n'+'1. Paypal Email: '+email+'\n'+'2. *IMPORTANTE!* Si la moneda de la cuenta a la que enviás NO ESTÁ DÓLARES, se debe cambiar para enviar dólares.\n'
			cadena = cadena+'3. Nota: Saldo 1\n4. Dirección de envío: No se necesita.\n5. Una vez realizado, ir al resumen en Paypal y obtener el detalle.'

	#Elabora encabezdo
	cobro = int(float(Cotizacion)*Total)
	cadena = 'DETALLES DE TU OPERACIÓN\n* Cantidad (USD): '+str(Total)+'\n* Cotización: '+Cotizacion+'\n* Cobro (ARS): '+str(cobro)+cadena

	#Envía Telegram
	EnviarTelegram(cadena)
	return TelegramProximoID
#*************************************************
def TelegramUSDT():
	from funciones import EnviarTelegram,BitcoinArgentina,LocalCall,MarketRelation,Bitstamp

	#Tether
	PrecioArgentinaVenta = BitcoinArgentina()
	PrecioArgentinaCompra = MarketRelation('Transfe','/buy-bitcoins-online/ars/national-bank-transfer/.json','bitstampusd*USD_in_ARS','CriptoenArgentina')
	USDstamp = Bitstamp('bitstampusd')
	USDTventa  = str(round(PrecioArgentinaVenta/USDstamp,2))
	USDTcompra  = str(round(PrecioArgentinaCompra/USDstamp,2))

	#Envía Telegram
	cadena = 'Tether Compra (USDT) $' + USDTcompra + '\nTether Venta (USDT) $' + USDTventa
	EnviarTelegram(cadena)
#*************************************************
def TelegramBot():
	from funciones import EnviarTelegram,LeerArchivoCrearLista

	#Determino en qué usuario  hay operaciones activas
	PidsMercados = LeerArchivoCrearLista('ArchivosOperativos/PidsMercados.txt')
	PidsSaldo1 = 0; PidsMave45 = 0; cadena = 'BOT ACTIVOS\n'
	for PidMercado in PidsMercados:
		ListaInfo = PidMercado.rsplit('#')
		cadena += ListaInfo[1] + ' ' + ListaInfo[2] + '\n'
	cadena = cadena.rstrip('\n')

	#Envío info
	EnviarTelegram(cadena)
#*************************************************
def BTC():
	#Variables
	from funciones import EnviarTelegram
	from Binance import send_signed_request

	Index = send_signed_request('GET','/dapi/v1/premiumIndex')
	pair = nested_lookup('pair',Index)
	for x in range(len(pair)):
		if pair[x]=='BTCUSD': break
	try:
		Index = float(nested_lookup('indexPrice',Index)[x])
		cadena = 'Precio bitcoin ' + str(int(Index))
		EnviarTelegram(cadena)
	except: return
#*************************************************
