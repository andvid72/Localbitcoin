import json, time, sys, platform, os, re, fileinput, requests, threading, ast
from deribit import *
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
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

#Configura como abrir navegador
options = Options()
# ~ options.add_argument('headless')
options.add_experimental_option('excludeSwitches', ['enable-logging'])

#Ejecuta navegador
driver = webdriver.Chrome(options=options)
driver.get('https://app.airtm.com/login')
# ~ driver.get('https://app.airtm.com/funds/withdraw/amount')

#Espera que esté la página cargada
WebDriverWait(driver,10000).until(EC.visibility_of_element_located((By.ID,'email')))

#Login en la web
time.sleep(5)
driver.find_element_by_id('email').send_keys('andresvidela72@gmail.com')
time.sleep(5)
driver.find_element_by_id('password').send_keys('9324Casa')
time.sleep(5)
driver.find_element_by_id('submit').click()
time.sleep(90)
driver.get('https://app.airtm.com/login')
WebDriverWait(driver,10000).until(EC.visibility_of_element_located((By.ID,'email')))
driver.find_element_by_id('email').send_keys('andresvidela72@gmail.com')
time.sleep(5)
driver.find_element_by_id('password').send_keys('9324Casa')
time.sleep(5)
driver.find_element_by_id('submit').click()


driver.quit()
exit()

#RetiroARS
xp = '//div[@data-indice="/dolar/informal"]/div/div[2]/input[@value="percent data-class-variacion data-variacion text-nowrap text-right up"]'
WebDriverWait(driver,100).until(EC.presence_of_element_located((By.XPATH,xp)))
RetiroARS = driver.find_element_by_xpath(xp).text
print('RetiroARS',RetiroARS)

driver.quit()
