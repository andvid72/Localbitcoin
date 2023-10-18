import json, time, sys, platform, os, re, fileinput, requests, threading, ast
from funciones import *
from telegram import *
from trading import *
from respuesta import *
from datetime import datetime #Obtiene fecha y hora en formato humano
from lbcapi3 import api #api de Localbitcoins para Python 3
from nested_lookup import nested_lookup #extrae valor de listas y bibliotecas anidadas
import telepot,telebot #envía mensajes a Telegram
token = '910296400:AAHRkd76QujDh8qnASbjEJv5kEc5DdAioco'
bot = telepot.Bot(token)
alias = 701549748
#HacerTXT(Informacion,'Informacion','C:/Users/Videla/Documents/Python')
#*************************************************
def Ambito():
	from selenium import webdriver
	from selenium.webdriver.common.by import By
	from selenium.webdriver.support.ui import WebDriverWait
	from selenium.webdriver.support import expected_conditions as EC
	from selenium.webdriver.chrome.options import Options

	#Configura como abrir navegador
	options = Options()
	options.add_argument('headless')
	options.add_experimental_option('excludeSwitches', ['enable-logging'])

	#Ejecuta navegador
	driver = webdriver.Chrome(options=options)
	driver.get('https://www.ambito.com/contenidos/dolar.html')

	#BluePorcentual
	# ~ xp = '//div[@data-indice="/dolar/informal"]/div/div[2]/span[contains(@class,"variacion")]'
	# ~ xp = '//div[@data-indice="/dolar/informal"]/div/div[2]/span[@class="percent data-class-variacion data-variacion text-nowrap text-right up"]'
	# ~ WebDriverWait(driver,10000).until(EC.visibility_of_element_located((By.XPATH,xp)))
	# ~ BluePorcentual = driver.find_element_by_xpath(xp).text
	# ~ if not BluePorcentual:
		# ~ WebDriverWait(driver,10000).until(EC.visibility_of_element_located((By.XPATH,xp)))
		# ~ BluePorcentual = driver.find_element_by_xpath(xp).text
		# ~ if not BluePorcentual:	return
	# ~ print('BluePorcentual',BluePorcentual)

	xp = '//div[@data-indice="/dolar/informal"]/div/div[2]/span[@class="percent data-class-variacion data-variacion text-nowrap text-right up"]'
	WebDriverWait(driver,10000).until(EC.visibility_of_element_located((By.XPATH,xp)))
	try: BluePorcentual = driver.find_element_by_xpath(xp).text
	except:
		xp = '//div[@data-indice="/dolar/informal"]/div/div[2]/span[@class="percent data-class-variacion data-variacion text-nowrap text-right down"]'
		WebDriverWait(driver,10000).until(EC.visibility_of_element_located((By.XPATH,xp)))
		try: BluePorcentual = driver.find_element_by_xpath(xp).text
		except:
			xp = '//div[@data-indice="/dolar/informal"]/div/div[2]/span[@class="percent data-class-variacion data-variacion text-nowrap text-right equal"]'
			WebDriverWait(driver,10000).until(EC.visibility_of_element_located((By.XPATH,xp)))
			try: BluePorcentual = driver.find_element_by_xpath(xp).text
			except: return
	print('BluePorcentual',BluePorcentual)

	#BlueCompra
	xp = '//div[@data-indice="/dolar/informal"]/div[2]/div/span[@class="value data-compra"]'
	BlueCompra = driver.find_element_by_xpath(xp).text
	print('BlueCompra',BlueCompra)

	#BlueVenta
	xp = '//div[@data-indice="/dolar/informal"]/div[2]/div[2]/span[@class="value data-venta"]'
	BlueVenta = driver.find_element_by_xpath(xp).text
	print('BlueVenta',BlueVenta)

	#Liqui
	xp = '//div[@data-indice="/dolarrava/cl"]/div[2]/div/span[@class="value data-valor"]'
	Liqui = driver.find_element_by_xpath(xp).text
	print('Liqui',Liqui)

	#LiquiPorcentual
	xp = '//div[@data-indice="/dolarrava/cl"]/div/div[2]/span[contains(@class,"variacion")]'
	# ~ WebDriverWait(driver,100).until(EC.presence_of_element_located((By.XPATH,xp)))
	LiquiPorcentual = driver.find_element_by_xpath(xp).text
	print('LiquiPorcentual',LiquiPorcentual)

	#MEP
	xp = '//div[@data-indice="/dolarrava/mep"]/div[2]/div/span[@class="value data-valor"]'
	MEP = driver.find_element_by_xpath(xp).text
	print('MEP',MEP)

	#MepPorcentual
	xp = '//div[@data-indice="/dolarrava/mep"]/div/div[2]/span[contains(@class,"variacion")]'
	MepPorcentual = driver.find_element_by_xpath(xp).text
	print('MepPorcentual',MepPorcentual)

	driver.quit()
#*************************************************
Ambito()


