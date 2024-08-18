import json, time, sys, platform, os, re, fileinput, requests, threading, ast
from funciones import *
from telegram import *
from trading import *
from datetime import datetime #Obtiene fecha y hora en formato humano
from lbcapi3 import api #api de Localbitcoins para Python 3
from nested_lookup import nested_lookup #extrae valor de listas y bibliotecas anidadas
import telepot,telebot #envía mensajes a Telegram
import hmac, hashlib
from urllib.parse import urlencode
KEY = 'yourkey'
SECRET = 'yoursecret'
#*************************************************
def hashing(query_string):
    return hmac.new(SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
#*************************************************
def get_timestamp():
    return int(time.time() * 1000)
#*************************************************
def dispatch_request(http_method):
    session = requests.Session()
    session.headers.update({'Content-Type': 'application/json;charset=utf-8','X-MBX-APIKEY': KEY})
    return {'GET': session.get,'DELETE': session.delete,'PUT': session.put,'POST': session.post,}.get(http_method, 'GET')
#*************************************************
def send_signed_request(http_method, url_path, payload={}, URL=''):
	#Armo URL
	if URL=='spot': BASE_URL = 'https://api.binance.com'
	else: BASE_URL = 'https://dapi.binance.com'

	query_string = urlencode(payload)
	query_string = query_string.replace('%27', '%22')
	if query_string: query_string = '{}&timestamp={}'.format(query_string, get_timestamp())
	else: query_string = 'timestamp={}'.format(get_timestamp())
	url = BASE_URL + url_path + '?' + query_string + '&signature=' + hashing(query_string)
	params = {'url': url, 'params': {}}
	response = dispatch_request(http_method)(**params)
	return response.json()
#*************************************************
def BinanceBalance():
	from Tickets.Soldout_module import EnviarTelegram

	#Balance en Binance margin
	for x in range(10):
		margin_balance = send_signed_request('GET','/dapi/v1/balance')
		try: balance = nested_lookup('balance',margin_balance)[1]
		except:	continue
		else:break

	if x==9:
		balance = 0
		EnviarTelegram('Error al obtener Balance en Futuros!')
	BalanceMargen = round(float(balance),6)

	#Balance en Binance spot
	for x in range(10):
		free = send_signed_request('GET','/api/v3/account',URL='spot')
		if free.get('makerCommission'): break
	if x==9:
		print('Error al obtener BalanceBTC y BalanceUSDT!')
		return(BalanceMargen,0,0)

	#BalanceBTC
	BalanceBTC = nested_lookup('free',free)[0]
	BalanceBTC = round(float(BalanceBTC),6)
	if BalanceBTC<0.00001: BalanceBTC = 0

	#BalanceUSDT
	BalanceUSDT = nested_lookup('free',free)[11]
	BalanceUSDT = int(float(BalanceUSDT))
	if BalanceUSDT<1: BalanceUSDT = 0

	return(BalanceMargen,BalanceBTC,BalanceUSDT)
#*************************************************
def BinanceMargin(DesdeDonde):
	from Tickets.Soldout_module import EnviarTelegram,LocalCall

	#Determino balance en Binance
	BalanceMargen,BalanceSpot,BalanceUSDT = BinanceBalance()

	#Determino márgenes
	MarginAccount = send_signed_request('GET','/dapi/v1/account')
	asset = nested_lookup('asset',MarginAccount)
	for x in range(len(asset)):
		if asset[x]=='BTC': break

	#Determino marginBalance
	try: marginBalance = float(nested_lookup('marginBalance',MarginAccount)[x])
	except: return

	#maintMargin
	try: maintMargin = float(nested_lookup('maintMargin',MarginAccount)[x])
	except:	return

	#MarginRatio
	if marginBalance>0: MarginRatio = round(maintMargin/marginBalance*100,2)
	else:
		cadena = 'No hay dinero en la cuenta de futuros o hubo algún error al tratar de determinarlo!'
		#No hay dinero en la cuenta de futuros
		if DesdeDonde=='Depositar':
			#Determino balance en Localbitcoins Saldo1
			wallet = LocalCall('/api/wallet-balance/','Saldo1',m=10)
			LBTCbalance = 0
			if wallet:	Saldo1balance = float(nested_lookup('balance',wallet)[0])

			#Determino balance en Localbitcoins MAVE45
			wallet = LocalCall('/api/wallet-balance/','MAVE45',m=10)
			LBTCbalance = 0
			if wallet:	MAVE45balance = float(nested_lookup('balance',wallet)[0])

			#Balance Localbitcoin
			LBTCbalance = Saldo1balance + MAVE45balance

			#Determino balance bitcoin en Binance
			BalanceMargen,BalanceSpot,BalanceUSDT = BinanceBalance()

			#Determina balance total
			BitcoinTotal = round(LBTCbalance + BalanceSpot,4)

			#Construyo mensaje con bitcoins que se deberían enviar a futuros
			cadena = 'Balance Bitcoins: '+str(BitcoinTotal)+'\n'
			cadena += 'Margin Ratio 10%, debés enviar '+str(round(BitcoinTotal/2*0.1,4))+'\n'
			cadena += 'Margin Ratio 5%, debés enviar '+str(round(BitcoinTotal/2*0.05,4))+'\n'
			cadena += 'Margin Ratio 1%, debés enviar '+str(round(BitcoinTotal/2*0.01,4))

		#Telegram informando margen de mantenimiento
		EnviarTelegram(cadena)
		return

	#Binance liquidation price
	Liquidacion = send_signed_request('GET','/dapi/v1/positionRisk')
	symbol = nested_lookup('symbol',Liquidacion)
	for x in range(len(symbol)):
		if symbol[x]=='BTCUSD_PERP': break
	try: Liquidacion = float(nested_lookup('liquidationPrice',Liquidacion)[x])
	except:	return

	#Precio Bitcoin
	Index = send_signed_request('GET','/dapi/v1/premiumIndex')
	pair = nested_lookup('pair',Index)
	for x in range(len(pair)):
		if pair[x]=='BTCUSD': break
	try: Index = float(nested_lookup('indexPrice',Index)[x])
	except: return

	#Construyo mensaje con bitcoins que se deberían enviar a futuros
	if DesdeDonde=='Depositar':
		cadena = 'Margin Ratio: '+str(MarginRatio)+'%\nBalance Margen: '+str(round(BalanceMargen,4))+'\nBalance Spot: '+str(round(BalanceSpot,4))
		cadena += '\nPrecio Bitcoin: $'+str(int(Index))+'\nPrecio Liquidación: $'+str(int(Liquidacion))+'\n'
		if MarginRatio>10: cadena += 'Margin Ratio 10%, debés enviar '+str(round(maintMargin/0.1-marginBalance,4))+'\n'
		if MarginRatio>5: cadena += 'Margin Ratio 5%, debés enviar '+str(round(maintMargin/0.05-marginBalance,4))+'\n'
		if MarginRatio>1: cadena += 'Margin Ratio 1%, debés enviar '+str(round(maintMargin/0.01-marginBalance,4))
		if MarginRatio<=1: cadena += 'Margin Ratio menor a 1%, no hace falta enviar bitcoins a la cuenta de margen'

	if DesdeDonde=='Extraer':
		cadena = 'Margin Ratio: '+str(MarginRatio)+'%\nBalance Margen: '+str(round(BalanceMargen,4))+'\nBalance Spot: '+str(round(BalanceSpot,4))
		cadena += '\nPrecio Bitcoin: $'+str(int(Index))+'\nPrecio Liquidación: $'+str(int(Liquidacion))+'\n'
		if MarginRatio>=10: cadena += 'Margin Ratio mayor a 10%, no se debería retirar bitcoins a la cuenta spot\n'
		if MarginRatio<10: cadena += 'Margin Ratio 10%, podés retirar '+str(round(marginBalance-maintMargin/0.1,4))+'\n'
		if MarginRatio<5: cadena += 'Margin Ratio 5%, podés retirar '+str(round(marginBalance-maintMargin/0.05,4))+'\n'
		if MarginRatio<1: cadena += 'Margin Ratio 1%, podés retirar '+str(round(marginBalance-maintMargin/0.01,4))

	#Construyo mensaje de estado
	if DesdeDonde=='Estado':
		cadena = 'Margin Ratio: '+str(MarginRatio)+'%\nBalance Margen: BTC '+str(round(BalanceMargen,4))+' - USD '+str(int(BalanceMargen*Index))
		cadena += '\nPrecio Bitcoin: $'+str(int(Index))+'\nPrecio Liquidación: $'+str(int(Liquidacion))

	#Telegram informando margen de mantenimiento
	EnviarTelegram(cadena)
#*************************************************
def BinanceDepositarFuturo(AmountSent):
	from Tickets.Soldout_module import EnviarTelegram

	#Transferis de Spot a Future
	params = {'asset':'BTC','amount':AmountSent,'type':3}
	for x in range(10):
		try: send_signed_request('POST','/sapi/v1/futures/transfer',params,URL='spot')
		except: continue
		else:
			#Telegram informando éxito
			cadena = str(AmountSent)+' btc enviados de Spot a Future'
			EnviarTelegram(cadena)
			break
#*************************************************
def BinanceExtraerFuturo(AmountSent):
	from Tickets.Soldout_module import EnviarTelegram

	#Transferis de Spot a Future
	params = {'asset':'BTC','amount':AmountSent,'type':4}
	for x in range(10):
		try: print(send_signed_request('POST','/sapi/v1/futures/transfer',params,URL='spot'))
		except: continue
		else:
			#Telegram informando éxito
			cadena = str(AmountSent)+' btc enviados de Future a Spot'
			EnviarTelegram(cadena)
			break
#*************************************************
def BinancePosition():
	from Tickets.Soldout_module import EnviarTelegram,LocalCall

	#Determino balance en Binance
	BalanceMargen,BalanceSpot,BalanceUSDT = BinanceBalance()

	#Determino balance en Localbitcoins Saldo1
	wallet = LocalCall('/api/wallet-balance/','Saldo1',m=10)
	LBTCbalance = 0
	if wallet:	Saldo1balance = float(nested_lookup('balance',wallet)[0])

	#Determino balance en Localbitcoins MAVE45
	wallet = LocalCall('/api/wallet-balance/','MAVE45',m=10)
	LBTCbalance = 0
	if wallet:	MAVE45balance = float(nested_lookup('balance',wallet)[0])

	#Determina el total de bitcoins
	Totalbalance = Saldo1balance + MAVE45balance + BalanceMargen + BalanceSpot

	#Si no tengo suficientes bitcoins en futuros para cubrir tu posición total en bitcoins, no hago la operación
	if BalanceMargen==0 or Totalbalance>BalanceMargen*100:
		EnviarTelegram('Sin bitcoins en futuros, no se puede equilibrar posición!')
		return

	#Size Future Position
	response = send_signed_request('GET','/dapi/v1/account')

	#Busco la posición en la lista del símbolo BTCUSD_PERP y obtengo notionalValue
	symbol = nested_lookup('symbol',response)
	for x in range(len(symbol)):
		if symbol[x]=='BTCUSD_PERP': break
	try: notionalValue = float(nested_lookup('notionalValue',response)[x])
	except: return

	#Busco la posición en la lista del símbolo BTC y obtengo unrealizedProfit
	asset = nested_lookup('asset',response)
	for x in range(len(asset)):
		if asset[x]=='BTC': break
	try: unrealizedProfit = float(nested_lookup('unrealizedProfit',response)[x])
	except: return
	FuturePosition = notionalValue + unrealizedProfit

	#Determina la nueva posición en Binance
	NewOrderAmount = Totalbalance + FuturePosition
	if NewOrderAmount > 0: NewOrderType = 'sell' #tengo más bitcoins que cobertura, debo enviar SELL
	else: NewOrderType = 'buy'; NewOrderAmount *= -1 #tengo más cobertura que bitcoins, debo enviar BUY

	#Precio Bitcoin
	Index = send_signed_request('GET','/dapi/v1/premiumIndex')
	pair = nested_lookup('pair',Index)
	for x in range(len(pair)):
		if pair[x]=='BTCUSD': break
	try: Index = float(nested_lookup('indexPrice',Index)[x])
	except: return

	#Si el tamaña de la orden es menor a 1 contrato, no se ejecuta
	BitcoinAmount = round(NewOrderAmount,4)
	ContractsAmount = int(round(NewOrderAmount*Index/100,0))
	if ContractsAmount==0:
		cadena = 'Posición en Binance balanceada, no se ejecutará orden!'
		EnviarTelegram(cadena)
		return

	#Loop de control de trading
	OpenAskPrice,OpenBidPrice,ShortPosted,LongPosted = 0,0,False,False
	while True:
		#OrderBook
		OrderBook = send_signed_request('GET','/dapi/v1/depth',{'symbol':'BTCUSD_PERP'})
		try: AskPrice = nested_lookup('asks',OrderBook)[0][0][0]
		except: continue
		try: BidPrice = nested_lookup('bids',OrderBook)[0][0][0]
		except: continue
		#*************************************************
		if NewOrderType=='sell':
			#Si cambió el precio, verifico el estado de la orden
			if ShortPosted and AskPrice!=OpenAskPrice:
				Orderfilled = send_signed_request('GET','/dapi/v1/order',{'symbol':'BTCUSD_PERP','orderId':OrderID})
				try: filled_amount = float(nested_lookup('executedQty',Orderfilled)[0])
				except: pass
				else:
					#Orden ejecutada
					if filled_amount==ContractsAmount:
						cadena = datetime.now().strftime('%H:%M:%S') + ' Binance ' + NewOrderType + ' BTC ' + str(BitcoinAmount) + ' ejecutada!'
						EnviarTelegram(cadena)
						return
					else:
						ShortPosted = False
						ContractsAmount -= filled_amount
						try: send_signed_request('DELETE','/dapi/v1/order',{'symbol':'BTCUSD_PERP','orderId':OrderID})
						except: pass

			#Abre nueva orden
			if not ShortPosted:
				params = {'symbol':'BTCUSD_PERP','side':'SELL','type':'LIMIT','timeInForce':'GTX','quantity':ContractsAmount,'price':AskPrice}
				try: response = send_signed_request('POST','/dapi/v1/order',params)
				except: continue
				else:
					try: OrderID = nested_lookup('orderId',response)[0]
					except: continue
					ShortPosted = True; OpenAskPrice = AskPrice
			continue
		#*************************************************
		if NewOrderType=='buy':
			#Si cambió el precio, verifico el estado de la orden
			if LongPosted and BidPrice!=OpenBidPrice:
				Orderfilled = send_signed_request('GET','/dapi/v1/order',{'symbol':'BTCUSD_PERP','orderId':OrderID})
				try: filled_amount = float(nested_lookup('executedQty',Orderfilled)[0])
				except: pass
				else:
					#Orden ejecutada
					if filled_amount==ContractsAmount:
						cadena = datetime.now().strftime('%H:%M:%S') + ' Binance ' + NewOrderType + ' BTC ' + str(BitcoinAmount) + ' ejecutada!'
						EnviarTelegram(cadena)
						return
					else:
						LongPosted = False
						ContractsAmount -= filled_amount
						try: send_signed_request('DELETE','/dapi/v1/order',{'symbol':'BTCUSD_PERP','orderId':OrderID})
						except: pass

			#Abre nueva orden
			if not LongPosted:
				params = {'symbol':'BTCUSD_PERP','side':'BUY','type':'LIMIT','timeInForce':'GTX','quantity':ContractsAmount,'price':BidPrice}
				try: response = send_signed_request('POST','/dapi/v1/order',params)
				except: continue
				else:
					try: OrderID = nested_lookup('orderId',response)[0]
					except: continue
					LongPosted = True; OpenBidPrice = BidPrice;
			continue
#*************************************************


