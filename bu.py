# Бот для Эксмо ETH&BTC


#Импорт библиотек
import httplib
import urllib
import urllib2
import json
import hashlib
import hmac
import time
import copy
import string
import random
import socket
import sys

#описание констант kleine Exmo
#BTC_ak=['K-94220a18648ebd40f269cc68d5318bca79a366b4']
#BTC_as=['S-af39d67290cb6e3cdad902a5b2aff5e2309bf2df']

#описание констант
BTC_ak=['K-bf180d37cc7a66a4781608acacf68583bf2a9ada']
BTC_as=['S-faaa76ede0164eabc8eae3c85117425c69f18d6e']


#Выставление уровней для торговли (коридор) для пары ETH/RUB
#Вне коридора бот уходит в режим ожидания
level_up = 8888
level_down = 8300


# Переход с продажи крипты с криптой (ETH/BTC) на крипта/фиат-валюта
# цена биткоина должна быть больше минимальной и наоборот
btcPrice=-1
btcPriceMin =0
btcPriceMax =99999999
decimal_part =2 #decimal_part Знаков после запятой

nBTC_USD=0
nETH_USD=1
nBTC_RUB=2
nETH_RUB=3
nETH_BTC=4
nUSD_RUB=5
####################
globalNr = nBTC_USD#
####################


# Выбирается первая(главная) пара > globalNr < 
# Вторая пара выбирается автоматически, так что бы валюты не пересекались
# Вторая пара начинает работать только при наличии свободной валюты этой пары
# 0. BTC/USD + (2. ETH/RUB)
# 1. ETH/USD + (3. BTC/RUB)
# 3. BTC/RUB + (1. ETH/USD)
# 2. ETH/RUB + (0. BTC/USD)
# 4. ETH/BTC ( )
# 5. USD/RUB ()

pairs=['btc_usd','eth_usd', 'btc_rub','eth_rub','eth_btc', 'usd_rub']

# Свободная (не в ордере) актуальная крипто-валюта и ее минимально возможное значени для установки ордера
currency_A_Free = 0
min_currency_A = 1

# Свободная (не в ордере) актуальная фиат-валюта и ее минимально возможное значени для установки ордера
currency_B_Free = 0
min_currency_B=1

# Флаг для установки соединения при старте
startUp =1

#Все свободные валюты
btcFree = 0
usdFree = 0
ethFree = 0
rubFree = 0

# Валюта в резерве (в ордерах), пока не используется
# TODO можно печатать, в какой зоне стоят ордера
#usdReserved=0 
#rubReserved=0 
#btcReserved=0 
#ethReserved=0 

# Валюта в резерве и в ордерах 
usdTotal=0 
rubTotal=0 
btcTotal=0 
ethTotal=0 

# Минимальные значения валют, необходисые для участия в сделках  
am_min_BTC=0.0010001
am_min_USD=11
am_min_ETH=0.0105
am_min_RUB=400

#установка соединия
nonce_last=1 #
cons=0       #

# счетчик выставленных ордеров
count_tref=0

from_price    = [0,0,0,0,0,0] #актуальная цена минус минимальный процент: [0]-BTC/USD... [5]-USD/RUB.
to_price      = [0,0,0,0,0,0] #актуальная цена минус минимальный процент: [0]-BTC/USD... [5]-USD/RUB.
startPreis    = [0,0,0,0,0,0] #актульная цена для каждой валюты:         [0]-BTC/USD... [5]-USD/RUB.
diff_sell_buy = [0,0,0,0,0,0] #абсолютная разница между продажей и покупкой в соотсетсвующей валюте. Рассчитывается динамично. Здесь не используется. Применяется константа 5% 

min_diff =0.0059  # 0.5%	 двойной учет комиссии



# коэффициент для расчета начальной цены покупки или продажи
# используется для подгона начальный цены под "заглушки"
# 0.35 здесь - это суммированный минимальный объем продажи (или покупки) от середины стакана 
am_lim=0.35 
# TODO для разных валют это величина разная. Надо сделать для каждой отдельно или совсем убрать.
#Поэтому сделаю пока минимум, ca. 0
am_lim=0.0001

#статистические данные, собранные с помощью API за последне 24 часа
#[0]-BTC/USD... [5]-USD/RUB.
vBids = [0,0,0,0,0,0] # предложения покупки в стакане с учетом коэффициента по объемам (учет заглушек)
vAsks = [0,0,0,0,0,0] # предложения продажи в стакане с учетом коэффициента по объемам (учет заглушек)
aBids = [0,0,0,0,0,0] # актульные предложения покупки в стакане
aAsks = [0,0,0,0,0,0] # актуальные предложения продажи в стакане

low    = [0,0,0,0,0,0] # минимальная цена за 24 часа
avg    = [0,0,0,0,0,0] # средняя цена за 24 часа
high   = [0,0,0,0,0,0] # максимальная цена за 24 часа
avg_AB = [0,0,0,0,0,0] # средня цена в стакае (Bid+Ask)/2


#шесть основных цен за последнии 24 часа , максимум и минимум получены через API  
# [0] low              - минимум
# [1] low+(avg-low)/2
# [2] avg              - среднее значение
# [4] high-(avg-low)/2
# [5] high             - максимум
xPrice = [0,0,0,0,0]  

#актуальная зона последней покупки/продажи для каждой валюты; 
#[0]-BTC/USD... [5]-USD/RUB.
zone=[0,0,0,0,0,0] 

#                       Zone 5               #
#xPrice[4]------------------------------high #
#                       Zone 4               #
#xPrice[3]-----------------------------------#
#                       Zone 3               #
#xPrice[2]-------------------------------avg #
#                       Zone 2               #
#xPrice[1]-----------------------------------#
#                       Zone 1               #
#xPrice[0]-------------------------------low #
#                       Zone 0               #

max_11 = 11
# запоминание в массив предыдущих максимумов и минимумов
# запоминание в массив предыдущих максимумов и минимумов
saveZoneMax=[0,0,0,0,0,0]
saveZoneMin=[0,0,0,0,0,0]

#Установака соединения
def reset_con():
    global cons
    url="api.exmo.me"
    print 'reset_con', url
    try:
        cons.close()
    except:
        print '~',

    try:
        cons = httplib.HTTPSConnection(url, timeout=10)
    except:
        print '~',
        
    return



#глубина стакана
# В z{} записывается весь массив данных по Asks/Bids (200 ордеров) 
# Вычисляется середина стакана для актуальной пары и записывается в глобальный массив avg_AB[pairs_nr]
# pairs_nr - номер пары
# 0. BTC/USD + (3. ETH/RUB)
# 1. ETH/USD + (2. BTC/RUB)
# 2. BTC/RUB + (1. ETH/USD)
# 3. ETH/RUB + (0. BTC/USD)
# 4. ETH/BTC (особый случай, здесь не реализован)
# 5. USD/RUB (особый случай, здесь не реализован)
def get_depth(pairs_url, pairs_nr):
    global avg_AB    
    url='/v1/order_book/?pair='+pairs_url.upper()+'&limit=200' #ограничение на 200 ордеров
    headers = { "Content-type": "application/x-www-form-urlencoded", 'User-Agent' : 'bot17'}
    cons.request("GET", url, None, headers)
    response = cons.getresponse()
    y=json.load(response)

    z={}
    for p in y: 
        p2=p.lower()
        ask_quantity = y[p]['ask_quantity'] 
        bid_quantity=y[p]['bid_quantity'] 
        z[p2]={'asks':[], 'bids':[]}
        for q in y[p]['ask']:
            z[p2]['asks'].append([float(q[0]), float(q[1])])
        for q in y[p]['bid']:
            z[p2]['bids'].append([float(q[0]), float(q[1])])
    
    avg_AB[pairs_nr] = round ((z[pairs_url]['asks'][0][0]+z[pairs_url]['bids'][0][0])*0.5 , 4)

    return z

# Запись в глобальные переменные статистических данных за последние 24 часа, полученных с помощью API 
def get_statistics(pairs_url, pairs_nr):
    global avg
    global high
    global low

    pair = pairs_url.upper()
    url ='https://api.exmo.com/v1/ticker/' 
    headers = { "Content-type": "application/x-www-form-urlencoded", 'User-Agent' : 'bot17'}
    cons.request("GET", url, None, headers)
    response = cons.getresponse()
    a=json.load(response)

    #high - максимальная цена сделки за 24 часа
    #low - минимальная цена сделки за 24 часа
    #avg - средняя цена сделки за 24 часа
    #vol - объем всех сделок за 24 часа
    #vol_curr - сумма всех сделок за 24 часа
    #last_trade - цена последней сделки
    #buy_price - текущая максимальная цена покупки
    #sell_price - текущая минимальная цена продажи
    
    z={}
    z[pair]={}

    j=0;
    while j<9:
       z[pair][j]={}
       j +=1

    i=0;
    for m in a[pair]:
      p2=m.lower

      z[pair] [i] = float(a[pair][m])
      i +=1  

    avg[pairs_nr]       = z[pair][8]
    high[pairs_nr]      = z[pair][0]
    low[pairs_nr]       = z[pair][7]
    return z



#Статус аккаунта. Определение свободной и зарезервированной валюты
#Актуальная валютная пара записывается в currency_A_Free, currency_B_Free
#TODO две переменных для одного значения... потом подправить
def get_status(pairs_nr):
    global nonce_last
    global currency_A_Free
    global min_currency_A
    global currency_B_Free
    global min_currency_B

    global btcFree 
    global usdFree 
    global ethFree 
    global rubFree

    global btcTotal
    global usdTotal
    global ethTotal
    global rubTotal

    try:
        nonce = int(round(time.time()*1000))
        #nonce = int(time.time()*10-14830000000)
        #nonce =max(nonce, nonce_last+1)
        #nonce_last=nonce

        params = {"nonce": nonce}
        params = urllib.urlencode(params)
        H = hmac.new(BTC_as[0], digestmod=hashlib.sha512)
        H.update(params)
        sign = H.hexdigest()
        headers = {"Content-type": "application/x-www-form-urlencoded",
                           "Key":BTC_ak[0],
                           "Sign":sign }
   
        cons.request("POST", "/v1/user_info", params, headers)

        response = cons.getresponse()

        a = json.load(response)
        #print a
        z={}
        z['return']={}
        z['return']['funds']={}
        z['return']['res']={}

        for m in a['balances']:
            p2=m.lower()
            z['return']['funds'][p2] = float(a['balances'][m])


        for m in a['reserved']:
            p2=m.lower()
            z['return']['res'][p2] = float(a['reserved'][m]) 



        #pair=['btc_usd','eth_usd','eth_rub','btc_rub','eth_btc', 'usd_rub']
        #mm=pairs_url.split('_')
        #m1=mm[0]
        #m2=mm[1]


        btcFree =   z['return']['funds']['btc']
        usdFree =   z['return']['funds']['usd'] 
        ethFree =   z['return']['funds']['eth']
        rubFree =   z['return']['funds']['rub']

        btcReserved =   z['return']['res']['btc']
        usdReserved =   z['return']['res']['usd'] 
        ethReserved =   z['return']['res']['eth']
        rubReserved =   z['return']['res']['rub']

        btcTotal = btcFree+btcReserved
        usdTotal = usdFree+usdReserved
        ethTotal = ethFree+ethReserved
        rubTotal = rubFree+rubReserved

        #print 'btcTotal =', round(btcTotal,6)
        #print 'usdTotal =', round (usdTotal,2)
        #print 'ethTotal =', round(ethTotal,6) 
        #print 'rubTotal =', round (rubTotal,2) 

        if (pairs_nr==nBTC_USD or pairs_nr==nBTC_RUB):
           currency_A_Free = btcFree
           min_currency_A=am_min_BTC
           #print 'BTC/',
        elif (pairs_nr==nETH_USD or pairs_nr==nETH_RUB):
           currency_A_Free = ethFree
           min_currency_A=am_min_ETH
           #print 'ETC/',
        if (pairs_nr==nBTC_USD or pairs_nr==nETH_USD):
           currency_B_Free = usdFree
           min_currency_B= am_min_USD
           #print 'USD'
        elif (pairs_nr==nBTC_RUB or pairs_nr==nETH_RUB):
           currency_B_Free = rubFree
           min_currency_B= am_min_RUB 
           #print 'RUB'

        if (pairs_nr==nETH_BTC):
           currency_A_Free = ethFree
           min_currency_A=am_min_ETH
           currency_B_Free = btcFree
           min_currency_B= am_min_BTC
           #print 'ETH/BTC'

        #print 'currency_B_Free ', currency_B_Free 
        #print 'min_currency_B', min_currency_B
        #print 'currency_A_Free ', currency_A_Free 
        #print 'min_currency_A', min_currency_A 

        #print 'btcReserved =', round (btcReserved,4) 
        #print 'usdReserved =', round (usdReserved,4)
        #print 'ethReserved =', round (ethReserved,4) 

    except:
        print 'Fehler get_status',
        time.sleep(2)
        reset_con()
        return 0

    return z


#Статус ордеров передаются в массив z={}
def get_my_orders(ind_ak=0):
    global nonce_last
    try:
        nonce = int(round(time.time()*1000))
        params = {"nonce": nonce}
        params = urllib.urlencode(params)
        H = hmac.new(BTC_as[0], digestmod=hashlib.sha512)
        H.update(params)
        sign = H.hexdigest()
        headers = {"Content-type": "application/x-www-form-urlencoded",
                           "Key":BTC_ak[0],
                           "Sign":sign,
                           'User-Agent' : 'bot1'}
        cons.request("POST", "/v1/user_open_orders", params, headers)
        response = cons.getresponse()

        a = json.load(response)
        #print 'a', a
        z={}
        z['success']=0
        z['error']='all ok'
        z['return']={}
        for p in a:
            for j in range(len(a[p])):
                z['success']=1
                oid=a[p][j]["order_id"]
                
                p2=a[p][j]["pair"].lower()
                    
                z['return'][oid]={"pair":p2, "type":a[p][j]["type"],
                                  "amount":float(a[p][j]["quantity"]), "rate":float(a[p][j]["price"])}
                
        if z['success']==0:
            z['error']='no orders'
        
    except:
        print 'Fehler get_my_orders'
        time.sleep(2)
        reset_con()
        return 0

    return z


#Отмена ордера. Не используется
def cancel_order(ord, ind_ak=0):
    global nonce_last
    try:
        nonce = int(round(time.time()*1000))
        params = {"nonce": nonce}
        params = urllib.urlencode(params)

        params = {"nonce": nonce, "order_id":ord}
        params = urllib.urlencode(params)

        H = hmac.new(BTC_as[0], digestmod=hashlib.sha512)
        H.update(params)
        sign = H.hexdigest()

        headers = {"Content-type": "application/x-www-form-urlencoded",
                           "Key":BTC_ak[0],
                           "Sign":sign,
                           'User-Agent' : 'bot1'}
        cons.request("POST", "/v1/order_cancel", params, headers)
        response = cons.getresponse()

        a = json.load(response)
        
    except:
        print 'Fehler cancel_order'
        time.sleep(2)
        reset_con()
        return 0

    return a



#Торговля
# ord_type  : sell/bey
# ord_rate  : Цена
# ord_amount: Количество  
# p         : Пара ['btc_usd','eth_usd', 'eth_rub', 'btc_rub','eth_btc', 'usd_rub']
def trade(ord_type, ord_rate, ord_amount, p, ind_ak=0):
    #print 'ord_type, ord_rate, ord_amount, p, ind_ak=0'
    #print ord_type, ord_rate, ord_amount, p, ind_ak
    global nonce_last
    global count_tref 
    count = 0 
    try:
        nonce = int(round(time.time()*1000))
        params = {"nonce": nonce, "pair":p.upper(), 'quantity':ord_amount, 'price':ord_rate, 'type':ord_type}
        params = urllib.urlencode(params)
        H = hmac.new(BTC_as[0], digestmod=hashlib.sha512)
        H.update(params)
        sign = H.hexdigest()
        headers = {"Content-type": "application/x-www-form-urlencoded",
                           "Key":BTC_ak[0],
                           "Sign":sign,
                           'User-Agent' : 'bot1'}
        cons.request("POST", "/v1/order_create", params, headers) 
        response = cons.getresponse()
        a = json.load(response)
        count_tref = count_tref+1 #Счетчик продаж
        print '| order_id =', a['order_id'], ' count', count_tref
        if a['error']!='':
            print 'Trade: ', a['error']
            
        aa=a['order_id']
        return aa
        
    except:
        print 'Fehler! trade!'
        time.sleep(2)
        reset_con()
        return 0

# Массив с данными стакана (200 ордеров) обрабатывется для каждой пары
# В глобальные переменные Верхняя и Нижняя граница стаканов (продажа и покупка) 
# записываются актульные значения
# В массив rate записываются значения границ стакана с учетом объемов (для определения заглушек)
def find_rate(depth, pair, typ, am_lim, pairs_nr):
    global aBids  # 
    global aAsks  #
    rate=depth[pair][typ][0][0]
    if typ=='asks': 
       aAsks [pairs_nr] = depth[pair][typ][0][0] 
    if typ=='bids': 
       aBids[pairs_nr]  = depth[pair][typ][0][0] 
    am_sum = 0.0
    counter = 0
    for orders in depth[pair][typ]:
        am   = orders[1]
        rate = orders[0]
        am_sum += am
        counter+=1
        if am_sum>=am_lim:
            break
    return rate 

# Рассчет стартовая цены
# Для каждой пары стартовая цена примерно равна середине стакана, 
# т.е. средней цене между последних покупкой и продажей
# учет объемов (немного сдвигает цены)
def getStartPrice(pairs_url, pairs_nr):
  #print pairs_url, pairs_nr
  global vBids
  global vAsks
  depth=get_depth(pairs_url,pairs_nr)
  #print depth
  #запросить стакан c учетом объемов (заглушки)
  vAsks[pairs_nr] = round (find_rate(depth, pairs_url, 'asks', am_lim, pairs_nr),4)
  vBids[pairs_nr] = round (find_rate(depth, pairs_url, 'bids', am_lim, pairs_nr),4)
  startPreis = (vAsks[pairs_nr] +vBids[pairs_nr] )/2
  return startPreis

# Определение актуальной зоны покупки/продажи (активной зоны)
def getZone(i):
    global xPrice
    sPreis=getStartPrice(pairs[i], i)
#                       Zone 5               #
#xPrice[4]------------------------------high #
#                       Zone 4               #
#xPrice[3]-----------------------------------#
#                       Zone 3               #
#xPrice[2]-------------------------------avg #
#                       Zone 2               #
#xPrice[1]-----------------------------------#
#                       Zone 1               #
#xPrice[0]-------------------------------low #
#                       Zone 0               #
    xPrice[0]= low[ i]
    xPrice[1]= low[ i] +(avg[i]-low[i])*0.5
    xPrice[2]= avg[ i]
    xPrice[3]= high[i] - (avg[i]-low[i])*0.5
    xPrice[4]= high[i]

    z =0
    if (sPreis > xPrice[0]) and (sPreis <=xPrice[1]):  
       z = 1
    elif (sPreis >xPrice[1] ) and (sPreis <=xPrice[2]): 
       z = 2
    elif (sPreis > xPrice[2]) and (sPreis <=xPrice[3]): 
       z = 3
    elif (sPreis > xPrice[3]) and (sPreis <=xPrice[4]): 
       z = 4
    elif (sPreis > xPrice[4]):
       z =5 
    return z 


def getPairName(pairs_nr):
  #print 
  mm=pairs [pairs_nr] .split('_')
  #m1=mm[0]
  #m2=mm[1] 
  #print m1.upper(),'/', m2.upper() 
  return mm

def calPrice (price, diff_SB):
     max_line=len(xPrice)# Число линий, границ уровней
     #print 'max_line', max_line 
     max_price =len(xPrice)+2# Число расчитанных по уровням цен 
     #print 'max_price', max_price

#----------------------------------------------------------------------
     price[ 0]= xPrice[0] - diff_SB # Минимальная цена минус са. 5%
#----------------------------------------------------------------------
     price[ 1]= xPrice[0]           # Минимальная цена
     price[ 2]= xPrice[0] + diff_SB # Минимальная цена плюс са. 5%
#----------------------------------------------------------------------
     price[ 3]= xPrice[1] 
     price[ 4]= xPrice[2] - diff_SB # Средняя цена минус са. 5%
#----------------------------------------------------------------------
     price[ 5]= xPrice[2]           # Средняя цена  
     price[ 6]= xPrice[2] + diff_SB # Средняя цена цена плюс са. 5%
#----------------------------------------------------------------------
     price[ 7]= xPrice[3]
     price[ 8]= xPrice[4] - diff_SB #Максимальная цена минус са. 5%
#----------------------------------------------------------------------
     price[ 9]= xPrice[4]           #Максимальная цена цена  
     price[10]= xPrice[4] + diff_SB #Максимальная цена плюс са. 5%
#---------------------------------------------------------------------- 
 
     #for i in range(max_11):
       #print 'price[',i,']=', price[i] 

     return price

# Если остаток свободной валюты нельзя разбить на две минимальных, используется вся валюта 
def checkFreeMin (currency_A_Free, min):
      if (currency_A_Free > min ) and (currency_A_Free<2*min):
         min =currency_A_Free
      return min

#Номер в массице цен для текущей зоны при учете актуальной цены
def getPriceZone(zoneCount, akt):
   i=0            # Zone 0 
   if (zoneCount==1):
     i=1          # Zone 1-->xPrice [0]
     if (akt > xPrice[0]):
         i=2      # Zone 1-->xPrice [0]
   elif(zoneCount==2):
     i=3          # Zone 2-->xPrice [1]
     if (akt > xPrice[1]):
         i=4      # Zone 2-->xPrice [1]
   elif(zoneCount==3):
     i=5          # Zone 3-->xPrice [2]
     if (akt > xPrice[2]):
         i=6      # Zone 3-->xPrice [2]   
   elif(zoneCount==4):
     i=7          # Zone 4-->xPrice [3]
     if (akt > xPrice[3]):
         i=8      # Zone 4-->xPrice [3]
   elif(zoneCount==5):
     i=9          # Zone 5-->xPrice [4]
     if (akt > xPrice[4]):
         i=10      # Zone 5-->xPrice [4]
   return i 
def printInfoSellBuy ( diff_SB, pairs_nr):
     mm=getPairName(pairs_nr)
     m1=(mm[0]).upper()
     m2=(mm[1]).upper() 
     aBid = aBids[pairs_nr] #
     aAsk = aAsks[pairs_nr] #
     avg = avg_AB[pairs_nr]         # средняя величина стакана #TODO - можно брать среднюю цену за день
     print '|--------------------------------------------------------|' 
     print '| aBid/aAsk            Avg           from_price/to_price |' 
     print '|', round (aBid ,decimal_part), '/', round (aAsk ,decimal_part), ' ',
     print round (avg,decimal_part), ' ', round(from_price[pairs_nr],decimal_part), '/', round(to_price[pairs_nr],decimal_part) 
     print '|--------------------------------------------------------|' 
     print '| Diff_sell_buy :', round (diff_SB, decimal_part), m2, ' ->', round(100*diff_SB/avg,1), '%'#расчет минимальной абсолютной разницы покупки продажи от стартовой цены
     print '|--------------------------------------------------------|' 
     if (level_down>0):
        print '| level_down =', level_down, m1, '[',m2,']'
     if (level_up>0):
        print '| level_up =', level_up, m1, '[',m2,']'
     return 0
  # Продажа
def setSell_Currency (pairs_nr): 
     global min_currency_B
     global min_currency_A
     price = [ ] # расчетные цена на продажу
     for i in range(max_11):
       price.append(0)
     print '0'
     avg = avg_AB[pairs_nr]         # средняя величина стакана #TODO - можно брать среднюю цену за день
     diff_SB = avg*min_diff         # расчет разницы, абсолютная величина: средняя величина стакана на мин. разницу=5%
     cal_from_to_price(pairs_nr, avg, diff_SB)
     min_currency_B= avg_AB[pairs_nr] * min_currency_A # расчет минималького количества фиата для покупки минимального количество крипты по актуальной цене
     print '1'
     printInfoSellBuy ( diff_SB, pairs_nr)
     print '2'
     price_min = to_price[pairs_nr] # минимально возможная цена продажи равна последней цене продажи
     #Продажа на мин. разницу от цены покупки
     sell(price_min, pairs_nr, min_currency_A)
     if (currency_A_Free >= min_currency_A):
       #Продажа по различным зонам
       zoneCount = getZone(pairs_nr)
       price = calPrice(price, diff_SB) # Расчет цен для торговли по актуальеым максимальным/минимальных ценам за день
       #Выставление ордеров на продажу только на актульной зоне zoneCount и выше
       n=getPriceZone(zoneCount, avg) 
       for i in range(100):
          n=n+1
          if n>max_11:
            # достигнут максимум зоны, выставление ордеров повторить с актуальной зоны
            n=getPriceZone(zoneCount, avg)  
          # крипта закончилась, выход
          if (currency_A_Free < min_currency_A):
            break
          print '|                                                        |' 
          print '| price[',n,']=', price[n], getStringPair(pairs_nr)
          sell(price[n], pairs_nr, min_currency_A)

     return

def sell(price, pairs_nr, min_currency_A):
     pair = pairs[pairs_nr] # расчетные цена на покупку 
     mm=getPairName(pairs_nr)
     m1=(mm[0]).upper()
     m2=(mm[1]).upper() 

     aBid = aBids[pairs_nr] #
     aAsk = aAsks[pairs_nr] #
     price_min = to_price[pairs_nr] # минимально возможная цена продажи равна последней цене продажи
     if (price < price_min ): # цена меньше допустимой
           price = price_min
           print '| price => price_min =', round (price,decimal_part), m2
              
     if (price < aAsk): #Продажа дешевле чем актуальная цена
           price = aAsk+aAsk/1000 #Цена продажи в стакане + 0.1%
     print '| price = aAsk+aAsk/1000 :', round (price, decimal_part), m2 
     #Продажа
     min_currency_A=checkFreeMin(currency_A_Free, min_currency_A)
     trade('sell', round (price,4), min_currency_A, pair)
     print '|'
     print '| Sell by rate', round (price,decimal_part)  , m2,'/', m1, '   Quantity: ',  round (min_currency_A, decimal_part+2), m1 
     print '|________________________________________________________|'  
     get_status(pairs_nr) #Обновление данный о свободных валютах
     return 0

# Покупка
def setBuy_Currency (pairs_nr):   #Валюту купить
   price = [ ]  # расчетные цена на продажу
   for i in range(max_11):
     price.append(0)

   avg = avg_AB[pairs_nr]         # средняя величина стакана #TODO - можно брать среднюю цену за день
   diff_SB = avg*min_diff
   cal_from_to_price(pairs_nr, avg, diff_SB)
   min_currency_B= avg_AB[pairs_nr] * min_currency_A 
   printInfoSellBuy ( diff_SB, pairs_nr)
   price_max = from_price[pairs_nr]
   #купить по максимально возможной цене
   buy (price_max, pairs_nr, min_currency_A, min_currency_B)
   if (currency_B_Free >= min_currency_B):
    # покупка по различным зонам
     zoneCount = getZone(pairs_nr)
     price = calPrice(price, diff_SB)  
     print '|                                                        |' 
     n=getPriceZone(zoneCount, avg)
     for i in range(100):
        n=n-1
        if n<0: 
           n=getPriceZone(zoneCount, avg) 
           break 
        if (currency_B_Free < min_currency_B):
             break 
     print '| price[',n,']=', price[n], getStringPair(pairs_nr)
     buy (price[n], pairs_nr, min_currency_A, min_currency_B)
   return

def buy(price, pairs_nr, min_currency_A, min_currency_B):
   pair = pairs[pairs_nr] # расчетные цена на покупку 
   mm=getPairName(pairs_nr)
   m1=(mm[0]).upper()
   m2=(mm[1]).upper() 
   aBid = aBids[pairs_nr]
   aAsk = aAsks[pairs_nr]
   avg = avg_AB[pairs_nr]
   price_max = from_price[pairs_nr]
   if (price > price_max ):
        price  = price_max
        print '| price => price_max =', round (price ,decimal_part), m2
   if (price  > aBid):
        price  = aBid-aBid/1000 
        print '| price = aBid-aBid/1000 :', round (price ,decimal_part), m2
   min_currency_B=checkFreeMin(currency_B_Free, min_currency_B)
   trade('buy', round (price,4), 0.999*min_currency_B/price, pair)
   print '|'
   print '|  Buy by rate', round (price,decimal_part) , m2,'/', m1, '   Quantity: ',  round(0.999*min_currency_B/price, decimal_part), m1 
   print '|________________________________________________________|'  
   get_status(pairs_nr)
   print
   return 0

def getStringPair(nr):
   str =''
   if (nr ==0):
      str= 'BTC/USD'
   elif (nr ==1):
      str= 'ETH/USD'
   elif (nr ==2):
      str= 'BTC/RUB'
   elif(nr ==3):
      str= 'ETH/RUB'
   elif(nr ==4):
      str= 'ETH/BTC'
   elif(nr ==5):
      str= 'USD/RUB' 

   return str 

# Cмена пар в зависимости от цены BTC
def checkMinMaxBTC(pairs_nr):
#Проверка и смена пар только без установки уровней (коридора) 
    if (level_up>0) and (level_down>0):
       return pairs_nr

    if (pairs_nr == nETH_BTC and btcPrice > btcPriceMin):
       print '>> change' , getStringPair(pairs_nr), 'to', getStringPair(globalNr), 'cause btcPrice >', btcPriceMin, 'USD'
       pairs_nr =globalNr 

    if (pairs_nr == nUSD_RUB and btcPrice < btcPriceMax):
       print '>> change' , getStringPair(pairs_nr), 'to', getStringPair(nBTC_USD), 'cause btcPrice <', btcPriceMax, 'USD'
       pairs_nr =globalNr 

    if (pairs_nr < nETH_BTC and btcPrice > btcPriceMax):
       print '>> change' , getStringPair(pairs_nr), 'to', getStringPair(nUSD_RUB), 'cause btcPrice >', btcPriceMax, 'USD'
       pairs_nr =nUSD_RUB 

    if (pairs_nr < nETH_BTC and btcPrice < btcPriceMin):
       print '>> change' , getStringPair(pairs_nr), 'to', getStringPair(nETH_BTC), 'cause btcPrice <', btcPriceMin, 'USD'
       pairs_nr =nETH_BTC

    return pairs_nr

def cal_from_to_price(pairs_nr, avg, diff_sell_buy):
    global to_price 
    global from_price 
    from_price[pairs_nr] = avg - diff_sell_buy 
    to_price[pairs_nr] = avg + diff_sell_buy 
    return 0

def calStartValues (pairs_nr):

    global zone 
    global diff_sell_buy
    global startPreis
    i=pairs_nr
    startPreis[i] = getStartPrice(pairs[i], i)
    diff_sell_buy[i] = min_diff*startPreis[i]
    zone [i]= getZone(i) 
    cal_from_to_price(i, startPreis[i], diff_sell_buy[i])
    return 0

# Инициализация, проверки и выставление ордеров на покупку и продажу
def run (pairs_nr):
    #global to_price 
    #global to_price 
    #global from_price 
    global zone 
    global btcPrice
    global decimal_part
    global diff_sell_buy
    global startPreis
    print
    print '>> run', getStringPair(pairs_nr)
    
# Расчет начальной цены и максимально/минимальных цен для всех пара
    i = 0
    get_statistics(pairs[i],i) 
    btcPrice = getStartPrice(pairs[i], i)
    # print current date and time
    print '>>', (time.strftime("%d.%m.%Y %H:%M:%S"))
    print '>> 1 BTC =', btcPrice, 'USD'
    print '>> run: ', getStringPair(pairs_nr)
    #Смена пар только при отсутствии свободной валюты 
    if (checkFreeCurrency() < 1):
       pairs_nr = checkMinMaxBTC(pairs_nr)
    print '>> run: ', getStringPair(pairs_nr)
    mm=getPairName(pairs_nr)
    m1=mm[0] 
    m2=mm[1]
    m1=m1.upper()
    m2=m2.upper()
    if (pairs_nr == nETH_BTC):
       decimal_part =4
    i = pairs_nr
    get_statistics(pairs[i],i) 

    calStartValues(i)

    print '|---------------------------------------------|' 
    print '| fromPrice : 1',m1, ' =', round (from_price[i], decimal_part), m2, '           ' 
    print '| toPrice   : 1',m1, ' =', round (to_price[i], decimal_part), m2, '           '
    print '| startPreis: 1',m1, ' =', round (startPreis[i], decimal_part), '+/-', round (diff_sell_buy[i], decimal_part) , m2 
    if (level_up > 0) :
       print '| level_up  : 1',m1, ' =', round(level_up, decimal_part), m2
    if (level_down > 0):
       print '| level_down: 1',m1, ' =', round(level_down, decimal_part), m2
    print '|---------------------------------------------|' 

    get_status(pairs_nr) 
#Зона и рассчет цен
    analysis_Pair(pairs_nr) 
    printMinFreeCurrency(pairs_nr)
#Покупка, если достаточно Фиата
    if (currency_B_Free >= min_currency_B):
        #Aктуальная цена ETH должна находиться в корридоре 
        if (check_corridor()==1):
           print
           print '|--------------------------------------------------------|' 
           print '| Start Buy', m1, '[', m2, ']                                  |'
           setBuy_Currency(pairs_nr)
#Продажа, если достаточно Крипты
    if (currency_A_Free >= min_currency_A):
        #Aктуальная цена ETH должна находиться в корридоре 
        if (check_corridor()==1):
          print
          print '|--------------------------------------------------------|' 
          print '| Start Sell', m1, '[', m2, ']                                 |'
          setSell_Currency(pairs_nr)
    return pairs_nr


#Печать всех зон и зоны актуальных продаж для выбранной пары
def analysis_Pair(pairs_nr):
  global high
  global avg
  global low
  z=zone[pairs_nr]
  print
  print getStringPair(pairs_nr), ': Zone ', z 
  if (saveZoneMax[pairs_nr] > high[pairs_nr]):
      print 'Max DOWN: old', round(saveZoneMax[pairs_nr],decimal_part+2), '>', round(high[pairs_nr],decimal_part+2)
  else:
      print 'Max UP: old', round(saveZoneMax[pairs_nr],decimal_part+2), '<=', round(high[pairs_nr],decimal_part+2)
  print '    _________________________'
  if (z==5):
     print '    |xxxxxxxxxx Zone 5 xxxxxxxxx|'
  else:
     print '    |       Zone 5          |'
  print 'high|-----------------------|-', round (high[pairs_nr],decimal_part)
  if (z==4):
     print '    |xxxxxxx Zone 4 xxxxxxxx|'
  else:
     print '    |       Zone 4          |'
  print '    |-----------------------|-', round(high[pairs_nr]-(avg[pairs_nr]-low[pairs_nr])*0.5, decimal_part)
  if (z==3):
     print '    |xxxxxx Zone 3 xxxxxxxxx|'
  else:
     print '    |       Zone 3          |'
  print 'avg-|-----------------------|-', round (avg[pairs_nr],decimal_part)
  if (z==2):
     print '    |xxxxxx Zone 2 xxxxxxxxx|'
  else:
     print '    |       Zone 2          |'
  print '    |-----------------------|-', round(low[pairs_nr]+(avg[pairs_nr]-low[pairs_nr])*0.5, decimal_part)
  if (z==1):
     print '    |xxxxxx Zone 1 xxxxxxxxx|'
  else:
     print '    |       Zone 1          |'
  print 'low-|-----------------------|-', round(low[pairs_nr],decimal_part)
  if (z==0):
     print '    |xxxxxxx Zone 0 xxxxxxxx|'
  else:
     print '    |       Zone 0          |'
  print '    |_______________________|'
 
  print
  if (saveZoneMin[pairs_nr] > low[pairs_nr]):
     print 'Min DOWN: old', round(saveZoneMin[pairs_nr],decimal_part+2), '>', round(low[pairs_nr],decimal_part+2)
  else:
      print 'Min UP: old', round(saveZoneMin[pairs_nr],decimal_part+2), '>', round(low[pairs_nr],decimal_part+2)
      print
  return

def printAllFreeCurrency():
    print
    print 'btcFree =', round(btcFree,4),'BTC', 
    print 'usdFree =', round (usdFree,2),'USD',
    print 'ethFree =', round(ethFree,4),'ETH',
    print 'rubFree =', round (rubFree,2),'RUB'
    return 0  
  
def checkFreeCurrency():
   if (btcFree < am_min_BTC) and (ethFree<am_min_ETH) and (usdFree < am_min_USD) and (rubFree < am_min_RUB):
      result =0
   else:
      printAllFreeCurrency()
      result =1
   return result
#Сохранения последнего максимума и минимума актуальной пары, пока только для инфо
def save_min_max_Price(pairs_nr):
    global saveZoneMax
    global saveZoneMin
    saveZoneMin[pairs_nr] = xPrice[0]# low
    saveZoneMax[pairs_nr] = xPrice[4]# high
    return 0

#Изменение пары в случаях достижения минимума или максимума значения БТС
#Торговля в фиате в случае высоких цен БТС (вся крипта продана, начало продажи фиата с фиатом ) 
#Торговля в крипте в случае нихких цен БТС ( крипта закуплена, начало продажи крипты с криптой ) 
def checkPairsNr(pairs_nr):
    i=nBTC_USD
    get_statistics(pairs[i],i) 
    btcPrice = getStartPrice(pairs[i], i)
    nPairs_nr = checkMinMaxBTC(pairs_nr)
    return nPairs_nr

#Проверка, находится ли актуальная цена БТС в корридоре, если режим проверки корридора выбран ((level_up>0) или (level_down>0)
def check_corridor( ):
    result =1# обычный режим продажи (без кооридора)
    i=globalNr
    get_statistics(pairs[i],i) 
    ethPrice = getStartPrice(pairs[i], i)
    if (level_up>0) and (level_down>0):
      if (globalNr==nETH_RUB) and ((ethPrice>level_up) or (ethPrice<level_down)):
          print 'ethPrice=',ethPrice, 'out of corridor ', time.sleep(10)
          result =0
      if (globalNr==nBTC_USD) and ((btcPrice>level_up) or (btcPrice<level_down)):
          print 'btcPrice=', btcPrice, 'out of corridor ', time.sleep(10)
          result =0
 
    return result

def ptintTotalCurrency():
    i=0
    for p in pairs:
       get_statistics(p,i)
       #print 'i', i,p
       i=i+1
    print
    print 'Currancy Total:', round (btcTotal, 4), 'BTC   ', round (usdTotal, 2), 'USD   ', round (ethTotal, 4), 'ETH   ', round(rubTotal,2), 'RUB'
    return 0 

def printMinFreeCurrency(pairs_nr):
    mm=getPairName(pairs_nr)
    m1=mm[0] 
    m2=mm[1]
    m1=m1.upper()
    m2=m2.upper() 
    min_currency_B= avg_AB[pairs_nr] * min_currency_A
    print 'currency A: min=', round(min_currency_A, decimal_part), m1, 'free=', round(currency_A_Free, decimal_part), m1
    print 'currency B: min=', round(min_currency_B, decimal_part), m2, 'free=', round(currency_B_Free, decimal_part), m2
    return 0

#Увеличение счетчика + печать инфо и сохранение ммаксимумов и минимумов актуальной цены пары
def inc_checkCount(countPrint, pairs_nr):
    countPrint = countPrint +1
    if (countPrint==5):
         save_min_max_Price(pairs_nr)
    if (countPrint==50):
         ptintTotalCurrency() 
    if (countPrint==1000):
         countPrint=0
         run(pairs_nr)
    return countPrint

#Запрос всех данных 
def read_data_API(pairs_nr):
   #print 'get_depth:        OK'
   #запросить стакан
   depth=get_depth(pairs[pairs_nr],pairs_nr)
   #print 'get_statistics:   OK' 
   #Запросить статистику
   get_statistics(pairs[pairs_nr], pairs_nr)
   #print 'get_status:       OK'
   #запросить остатки валют
   balance=get_status(pairs_nr)
   #print 'get_my_orders     OK' 
   return 0

######################################################################################
#                                                                                    #
#                                                                                    #
#                                    Старт программы                                 #
#                                                                                    #
#                                                                                    #
######################################################################################
def bot():
    global pairs
    global startUp
     # Одно соединение при старте
    if (startUp==1):
      startUp =2
      reset_con()
    countPrint =0
    print
    print 'Bot is ready...'
    print
    pairs_nr = globalNr
    pairs_nr=run(pairs_nr)
    print 
    #бесконечный цикл:
    while True:
        try:
            #задержка чтоб не превысить лимит обращений по АПИ
            time.sleep(1.0)
            read_data_API (pairs_nr)
            #запросить мои ордера
            my_orders=get_my_orders()
            mm=getPairName(pairs_nr)
            m1=mm[0] 
            m2=mm[1]
            m1=m1.upper()
            m2=m2.upper() 
            if (checkFreeCurrency() < 1):
                 #Смена валюты в зависимости от цена BTC; в режиме "коридора" не происходит, к примеру btcPriceMin =9600 btcPriceMax =11999
                 #Проверка курса BTC и смена пары при достижении максимума или минимума
                 pairs_nr=checkPairsNr(pairs_nr)
                 time.sleep(1.0)
                 #Увеличение счетчика, обновление информация для вывода на экран, сохранения максимума/минимума актульной пары
                 countPrint=inc_checkCount(countPrint, pairs_nr)
                 print '.',
            else: # свободная валюта обнаружена
                print
                #Пересчет  минимально возможной цены ордера в валюте А
                min_currency_B= avg_AB[pairs_nr] * min_currency_A 
                #проверка актуальной валюты
                #print 'min_currency_A:', round(min_currency_A,decimal_part), m1
                #print 'min_currency_B:', round(min_currency_B,decimal_part), m2
                if (currency_B_Free >= min_currency_B) or (currency_A_Free >= min_currency_A):
                    print 
                    run(pairs_nr) 
                #Варинт работы без задания уровней  (нормальный режим)
                elif (level_up < 0) and (level_down < 0):
                    print 'change pairs_nr:' , getStringPair(pairs_nr)
                    #Смена пары Крипта/Крипта из за наличия фиата
                    #Выбирается "глобальная" пара globalNr
                    if (pairs_nr == nETH_BTC) and (globalNr!=pairs_nr):
                        if (usdFree>am_min_USD):
                           print 'change' , getStringPair(pairs_nr), 'to', getStringPair(globalNr), 'cause usdFree >', am_min_USD , 'USD'
                           pairs_nr = nBTC_USD
                           run(pairs_nr) 
                        if (rubFree > am_min_RUB):
                           print 'change' , getStringPair(pairs_nr), 'to', getStringPair(globalNr), 'cause rubFree >', am_min_RUB , 'RUB'
                           pairs_nr = nETH_RUB
                           run(pairs_nr)

                    #смена пары Крипта/Фиат  на другую пару Крипта/Фиат из за наличия соотв. валюты
                    if (globalNr ==nBTC_USD):
                         pairs_nr =nETH_RUB
                         print 'change' , getStringPair(globalNr), 'to', getStringPair(pairs_nr),
                         if (ethFree > am_min_ETH):
                             print  'cause ethFree >', am_min_ETH, 'ETH' 
                         elif (rubFree > am_min_RUB):
                             print 'cause rubFree >', am_min_RUB , 'RUB'
                         run(pairs_nr)
                    #смена пары Крипта/Фиат  на другую пару Крипта/Фиат из за наличия соотв. валюты
                    if (globalNr ==nETH_RUB):
                         pairs_nr =nETH_BTC
                         print 'change' , getStringPair(globalNr), 'to', getStringPair(pairs_nr),
                         if(btcFree > am_min_BTC): 
                             print 'cause btcFree >', am_min_BTC, 'BTC'
                         elif (usdFree > am_min_USD):
                             print 'cause usdFree >', am_min_USD , 'USD'
                         run(pairs_nr)
                    #смена пары Крипта/Фиат  на другую пару Крипта/Фиат из за наличия соотв. валюты
                    if (globalNr == nBTC_RUB):
                         pairs_nr = nETH_USD
                         print 'change' , getStringPair(globalNr), 'to', getStringPair(pairs_nr), 
                         if (ethFree > am_min_ETH):
                             print 'cause ethFree >', am_min_ETH , 'ETH or usdFree >',am_min_USD , 'USD'
                         elif (usdFree > am_min_USD):
                             print 'cause usdFree >', am_min_USD , 'USD'
                         run(pairs_nr)
                    #смена пары Крипта/Фиат  на другую пару Крипта/Фиат из за наличия соотв. валюты
                    if (globalNr == nETH_USD):
                         pairs_nr =nBTC_RUB
                         print 'change' , getStringPair(globalNr), 'to', getStringPair(pairs_nr),
                         if (btcFree > am_min_BTC):
                             print 'cause btcFree >', am_min_BTC , 'BTC'  
                         elif(rubFree > am_min_RUB):
                             print 'cause rubFree >', am_min_RUB , 'RUB'
                         run(pairs_nr)
                continue 
        except:
            print 'bot() Fehler ',
            time.sleep(2)
            reset_con()



