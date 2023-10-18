import json, time, sys, platform, os, re, fileinput, requests, threading, ast
from funciones import *
from telegram import *
from trading import *
from datetime import datetime #Obtiene fecha y hora en formato humano
from lbcapi3 import api #api de Localbitcoins para Python 3
from nested_lookup import nested_lookup #extrae valor de listas y bibliotecas anidadas
import telepot,telebot #envía mensajes a Telegram
token = deribitoken
alias = deribitalias
#*************************************************
LastHour = 0
def DeribitLiquidation():
	#Verifico si paso una hora para volver a chequear Deribit
	global LastHour
	CurrentHour = int(datetime.now().strftime('%H'))
	if CurrentHour == LastHour: return
	LastHour = CurrentHour

	#Precio de liquidación
	url = 'https://www.deribit.com/api/v2/'
	auth=('NynvpzIH','3z9q4-NTHFip4k50tHldX2vMlir0sHmKXdT5XVkBF94')
	while True:
		try: liquidation_price = requests.get(url+'/private/get_position', params={'instrument_name':'BTC-PERPETUAL'}, auth=auth, timeout=2).json()['result']['estimated_liquidation_price']
		except: continue
		else: break
#*************************************************
def DeribitMargin(DesdeDonde):
	from funciones import EnviarTelegram

	#Deribit account information
	url = 'https://www.deribit.com/api/v2/'
	auth=('NynvpzIH','3z9q4-NTHFip4k50tHldX2vMlir0sHmKXdT5XVkBF94')
	params = {'currency':'BTC'}
	while True:
		try: data = requests.get(url+'/private/get_account_summary', params=params, auth=auth, timeout=2).json()['result']
		except: continue
		else: break
	maintenance_margin = data['maintenance_margin']
	margin_balance = data['margin_balance']
	if margin_balance>0: maintenance_margin = round(maintenance_margin/margin_balance*100,2)
	else: maintenance_margin = 0

	#Determino balance en Localbitcoins y cantidad que se debería enviar
	wallet = LocalCall('/api/wallet-balance/',m=10)
	balance = round(float(nested_lookup('balance',wallet)[0]),4)
	AmountSent = round(balance/100,4)

	#Deribit liquidation price
	while True:
		try: Liquidacion = requests.get(url+'/private/get_position', params={'instrument_name':'BTC-PERPETUAL'}, auth=auth, timeout=2).json()['result']['estimated_liquidation_price']
		except: continue
		else: break

	#Precio Bitcoin
	while True:
		try: Index = requests.get(url+'/public/get_index_price', params={'index_name':'btc_usd'}, auth=auth, timeout=2).json()['result']['index_price']
		except: continue
		else: break

	#Construyo mensaje con bitcoins que se deberían enviar a Deribit
	if DesdeDonde=='Depositar':
		cadena = 'Margen Mantenimiento (MM): '+str(maintenance_margin)+'%\nBalance Deribit: '+str(round(margin_balance,4))
		cadena += '\nPrecio Liquidación: $'+str(int(Liquidacion))+'\n'
		cadena += 'MM 10%, enviar '+str(round(AmountSent*10,4))+'\n'
		cadena += 'MM 5%, enviar '+str(round(AmountSent*20,4))+'\n'
		cadena += 'MM 1%, enviar '+str(round(AmountSent*100,4))

	#Construyo mensaje con bitcoins que se deben extraer de Deribit
	if DesdeDonde=='Extraer':
		cadena = 'Margen Mantenimiento (MM): '+str(maintenance_margin)+'%\nBalance Deribit: '+str(round(margin_balance,4))+'\n'
		cadena += 'MM %'+str(round(maintenance_margin*2,2))+', extraer '+str(round(margin_balance/2,4))+'\n'
		cadena += 'MM %'+str(round(maintenance_margin*4,2))+', extraer '+str(round(margin_balance*3/4,4))+'\n'
		cadena += 'MM %'+str(round(maintenance_margin*8,2))+', extraer '+str(round(margin_balance*7/8,4))

	#Construyo mensaje de estado
	if DesdeDonde=='Estado':
		cadena = 'Margen Mantenimiento: '+str(maintenance_margin)+'%\nBalance: '+str(round(margin_balance,4))
		cadena += '\nPrecio Liquidación: $'+str(int(Liquidacion))+'\nPrecio Bitcoin: $'+str(int(Index))

	#Telegram informando margen de mantenimiento
	EnviarTelegram(cadena)

#*************************************************
def DeribitDepositar(AmountSent):
	from funciones import EnviarTelegram

	#Deribit account information
	url = 'https://www.deribit.com/api/v2/'
	auth=('NynvpzIH','3z9q4-NTHFip4k50tHldX2vMlir0sHmKXdT5XVkBF94')
	params = {'currency':'BTC'}
	while True:
		try: data = requests.get(url+'/private/get_account_summary', params=params, auth=auth, timeout=2).json()['result']
		except: continue
		else: break

	#Si no existe dirección para enviar bitcoin, la creo
	deposit_address = data['deposit_address']
	if deposit_address==None:
		params = {'currency':'BTC'}
		try: data = requests.get(url+'/private/create_deposit_address', params=params, auth=auth, timeout=2).json()['result']
		except: return
		deposit_address = data['address']

	#Envia bitcoins a Deribit
	parametros = {'address':deposit_address,'amount':AmountSent}
	for m in range(10):
		try: print(Llave().call('POST','/api/wallet-send/',parametros).json()['data']['message'])
		except:	continue
		else:
			#Telegram informando éxito
			cadena = str(AmountSent)+' btc enviados a Deribit con éxito'
			EnviarTelegram(cadena)
			break
#*************************************************
def DeribitPosition():
	from funciones import EnviarTelegram

	#Evaluo si hay dinero en Deribit
	url = 'https://www.deribit.com/api/v2/'
	auth=('NynvpzIH','3z9q4-NTHFip4k50tHldX2vMlir0sHmKXdT5XVkBF94')
	params = {'currency':'BTC'}
	while True:
		try: data = requests.get(url+'/private/get_account_summary', params=params, auth=auth, timeout=2).json()['result']
		except: continue
		else: break
	margin_balance = data['margin_balance']
	if margin_balance < 0.0002: return

	#Determino balance en Localbitcoins
	wallet = LocalCall('/api/wallet-balance/',m=10)
	LBTCbalance = 0
	if wallet:	LBTCbalance = round(float(nested_lookup('balance',wallet)[0]),5)

	#Determino balance en Deribit
	params = {'with_portfolio':'true'}
	while True:
		try: data = requests.get(url+'/private/get_subaccounts', params=params, auth=auth, timeout=2).json()
		except: continue
		else: break
	margin_balance = nested_lookup('margin_balance',data)
	Deribitbalance = 0
	for x in range(len(margin_balance)): Deribitbalance += margin_balance[x]
	Deribitbalance = round(Deribitbalance,5)

	#Determina el total de bitcoins
	Totalbalance = LBTCbalance + Deribitbalance

	#Determino tamaño de la posición abierta en Deribit
	while True:
		try: data = requests.get(url+'/private/get_account_summary', params={'currency':'BTC'}, auth=auth, timeout=2).json()['result']
		except:	continue
		else: break
	delta_total = data['delta_total']

	#Determina la nueva posición en Deribit
	NewOrderAmount = round(Totalbalance + delta_total,5)
	if NewOrderAmount > 0: NewOrderType = 'sell' #tengo más bitcoins que cobertura, debo enviar SELL
	else: NewOrderType = 'buy'; NewOrderAmount *= -1 #tengo más cobertura que bitcoins, debo enviar BUY
	if abs(NewOrderAmount) < 0.0001: NewOrderAmount = 0

	#Determina el tamaño de la orden en dólares
	while True:
		try: index_price = requests.get(url+'/public/get_index', params={'currency':'BTC'}, auth=auth, timeout=2).json()['result']['BTC']
		except: continue
		else: break

	#Si el tamaña de la orden es menor a 1 contrato, no se ejecuta
	NewOrderAmount = int(round(NewOrderAmount*index_price/10,0)*10)
	OrginalAmount = NewOrderAmount
	if not NewOrderAmount:
		cadena = 'Posición en Deribit balanceada, no se ejecutará orden!'
		EnviarTelegram(cadena)
		return

	#Loop de control de trading
	OpenAskPrice,OpenBidPrice,ShortPosted,LongPosted = 0,0,False,False
	while True:
		#OrderBook
		params = {'instrument_name':'BTC-PERPETUAL','depth':1}
		while True:
			try: OrderBook = requests.get(url+'public/get_order_book', params=params, auth=auth, timeout=2).json()
			except: continue
			else: break
		AskPrice = nested_lookup('asks',OrderBook)[0][0][0]; BidPrice = nested_lookup('bids',OrderBook)[0][0][0]
		#*************************************************
		if NewOrderType=='sell':
			#Si cambió el precio, verifico el estado de la orden
			if ShortPosted and AskPrice!=OpenAskPrice:
				try: Orderfilled = requests.get(url+'/private/get_order_state', params={'order_id':OrderID}, auth=auth, timeout=2).json()
				except Exception as e: print('1 error',e)
				else:
					filled_amount = Orderfilled['result']['filled_amount']
					#Orden ejecutada
					if filled_amount==NewOrderAmount:
						cadena = datetime.now().strftime('%H:%M:%S') + ' Deribit ' + NewOrderType + ' $' + str(OrginalAmount) + ' ejecutada!'
						EnviarTelegram(cadena)
						return
					else:
						ShortPosted = False
						NewOrderAmount -= filled_amount
						try: requests.get(url+'/private/cancel', params={'order_id':OrderID}, auth=auth, timeout=2).json()
						except: pass

			#Abre nueva orden
			if not ShortPosted:
				params = {'instrument_name':'BTC-PERPETUAL', 'amount':NewOrderAmount, 'price':AskPrice, 'post_only':'true'}
				try: OrderID = requests.get(url+'private/sell', params=params, auth=auth, timeout=2).json()['result']['order']['order_id']
				except Exception as e: print('2 error',e)
				else: ShortPosted = True; OpenAskPrice = AskPrice;

			continue
		#*************************************************
		if NewOrderType=='buy':
			#Si cambió el precio, verifico el estado de la orden
			if LongPosted and BidPrice!=OpenBidPrice:
				try: Orderfilled = requests.get(url+'/private/get_order_state', params={'order_id':OrderID}, auth=auth, timeout=2).json()
				except Exception as e: print('3 error',e)
				else:
					filled_amount = Orderfilled['result']['filled_amount']
					#Orden ejecutada
					if filled_amount==NewOrderAmount:
						cadena = datetime.now().strftime('%H:%M:%S') + ' Deribit ' + NewOrderType + ' $' + str(OrginalAmount) + ' ejecutada!'
						EnviarTelegram(cadena)
						return
					else:
						LongPosted = False
						NewOrderAmount -= filled_amount
						try: requests.get(url+'/private/cancel', params={'order_id':OrderID}, auth=auth, timeout=2).json()
						except: pass

			#Abre nueva orden
			if not LongPosted:
				params = {'instrument_name':'BTC-PERPETUAL', 'amount':NewOrderAmount, 'price':BidPrice, 'post_only':'true'}
				try: OrderID = requests.get(url+'private/buy', params=params, auth=auth, timeout=2).json()['result']['order']['order_id']
				except Exception as e: print('4 error',e)
				else: LongPosted = True; OpenBidPrice = BidPrice;

			continue
#*************************************************
def DeribitExtaer(amount,TelegramProximoID):
	from funciones import EnviarTelegram

	#Dirección Localbitcoin
	address = '34BtHVDryRFxQksputNdVT5Shr5DM84Ejr'  #21 julio 2020

	#Solicitás TFA
	tfa,TelegramProximoID = Repreguntador('Código de 6 dígitos de autenticación (2FA)? ','EsNumero',TelegramProximoID)
	if not tfa: return TelegramProximoID
	tfa = int(float(tfa))

	#Deribit account information
	url = 'https://www.deribit.com/api/v2/'
	auth=('NynvpzIH','3z9q4-NTHFip4k50tHldX2vMlir0sHmKXdT5XVkBF94')
	params = {'currency':'BTC','address':address,'amount':amount,'priority':'very_low','tfa':tfa}
	while True:
		try: requests.get(url+'/private/withdraw', params=params, auth=auth, timeout=2).json()
		except: continue
		else:
			#Telegram informando éxito
			cadena = 'Extraer' + str(amount)+'BTC. Por favor confirmar en el email recibido desde Deribit'
			EnviarTelegram(cadena)
			break
#*************************************************
