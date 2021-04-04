import requests
import random
import string
from bs4 import BeautifulSoup as bs
import json
import threading
from flask import request
from flask import Blueprint
from flask_cors import CORS

linkvertise_cors_bypasser = Blueprint('linkvertise_cors_bypasser', __name__)

class Sessions:
    def __init__(self):
        #Init sessions
        self.sessions = {}
    
    def session_runner(self, name):
        #Run the session function
        function = self.sessions[name]['function']['function']
        args = self.sessions[name]['function']['args']
        self.sessions[name]['data'] = function(*args)
        self.sessions[name]['status'] = 'Finished'
    
    def create_session(self, name, function, args):
        #Check if session already exists
        if name in self.sessions:
            return 'Session already exists'
        #Create session
        self.sessions[name] = {}
        self.sessions[name]['function'] = {'function' : function, 'args' : args}
        self.sessions[name]['status'] = 'Stopped'
        return 'Session created'
            
    def start_session(self, name):
        #Check if session exists
        if (name in self.sessions) == False:
            return 'Session does not exist'
        #Check if session already started
        elif self.sessions[name]['status'] == 'Started':
            return 'Session already started'
        #Check if session already finished
        elif self.sessions[name]['status'] == 'Finished':
            return 'Session already finished'
        #Start session using session runner
        self.sessions[name]['status'] = 'Started'
        self.sessions[name]['runner'] = threading.Thread(target = self.session_runner, args = (name,))
        self.sessions[name]['runner'].start()
        return 'Session started'
    
    def wait_for_session(self, name):
        #Check if session exists
        if (name in self.sessions) == False:
            return 'Session does not exist'
        #Check if session started
        elif self.sessions[name]['status'] == 'Stopped':
            return 'Session has not been started'
        #Wait until session status is finsihed
        while self.sessions[name]['status'] != 'Finished':
            pass
        return 'Session has finished'
        
    def remove_session(self, name):
        #Check if session exists
        if (name in self.sessions) == False:
            return 'Session does not exist'
        #Remove session
        del self.sessions[name]
        return 'Session removed'
        
    def session_data(self, name):
        #Check if session exists
        if (name in self.sessions) == False:
            return 'Session does not exist'
        #Check if has data
        if 'data' in self.sessions[name]:
            return self.sessions[name]['data']
        else:
            return None
            
    def session_status(self, name):
        #Check if session exists
        if (name in self.sessions) == False:
            return 'Session does not exist'
        #Return status
        return self.sessions[name]['status']

    def start_sessions(self):
        #Check if has sessions
        if len(self.sessions)<1:
            return 'No sessions'
        #For every session do start_session
        for i in self.sessions.keys():
            name=i
            self.start_session(name)
        return 'Started all sessions'

    def wait_for_sessions(self):
        #Check if has sessions
        if len(self.sessions)<1:
            return 'No sessions'
        #For every session do wait_for_session
        for i in self.sessions.keys():
            name=i
            self.wait_for_session(name)
        return 'Sessions have finished'
    
    def sessions_data(self):
        #Check if has sessions
        if len(self.sessions)<1:
            return 'No sessions'
        #For every session do session_data
        datas={}
        for i in self.sessions.keys():
            name=i
            data=self.session_data(name)
            datas[name]=data
        return datas
        
    def sessions_status(self):
        #Check if has sessions
        if len(self.sessions)<1:
            return 'No sessions'
        #For every session do session_status
        statuses={}
        for i in self.sessions.keys():
            name=i
            status=self.session_status(name)
            statuses[name]=status
        return statuses

class ProxyCorsBypasser:
    #Requires Sessions
    
    def legal_number(self, number):
        if (number/1.0).is_integer() == False:
            return False
        if number<=0:
            return False
        return True
        
    def division(self, number, divider):
        rem = number
        counter = 0
        while (rem>=divider):
            counter += 1
            rem -= divider
        return [counter, number-counter*divider]
    
    def get_free_proxies(self):
        #Fetch and parse proxy list
        proxy_list_url = "https://free-proxy-list.net/"
        proxy_list_html = bs(requests.get(proxy_list_url).content, "html.parser")
        
        #Locate table element
        proxy_table = proxy_list_html.find("table", {"id": "proxylisttable"})
        
        #Convert table element into list
        proxies = []
        for table_row in proxy_table.findAll("tr"):
            table_cells = table_row.findAll("td")
            try:
                proxy_ip = table_cells[0].text.strip()
                proxy_port = table_cells[1].text.strip()
                proxy_host = proxy_ip+':'+proxy_port
                proxies.append(proxy_host)
            except:
                continue
        return proxies
    
    def proxy_fetch(self, method, proxy, url, data=None, parse_check=False):   
        #Configure proxy
        proxy_config = {"http": proxy, "https": proxy, "ftp": proxy}
        
        #Print
        print ('Making '+method+' request using '+proxy)
        
        #Try to make a get or post request
        try:
            if method == 'get':
                response = requests.get(url, proxies=proxy_config, timeout=2)
            if method == 'post':
                response = requests.post(url, proxies=proxy_config, data=data, timeout=2)
        
            #Try to parse response if needed
            if parse_check == True:
                try:
                    parsed = json.loads(response.text)
                    return ['Success',response.text]
                except:
                    return ['Parse error',None]
                    
            else:
                return ['Success',response.text]
                
        
        except requests.exceptions.ProxyError:
            return ['Proxy error',None]
        except requests.exceptions.ConnectTimeout:
            return ['Conection error',None]
        except requests.exceptions.Timeout:
            return ['Timeout error',None]
        except:
            return ['Unknown error',None]
    
    def multithread_proxies_fetch(self, method, proxies, url, data=None, parse_check=False):
        #Create responses
        responses = Sessions()
        
        #Add each proxy_fetch to the responses sessions
        for i in range(len(proxies)):
            responses.create_session(i, self.proxy_fetch, (method, proxies[i], url, data, parse_check,))
        
        #Start sessions
        responses.start_sessions()
        
        #Wait for sessions to finish
        responses.wait_for_sessions()
        
        #Print
        print ('Multithreaded '+str(len(proxies))+' '+method+' requests')
        
        #Return responses data
        return responses.sessions_data()
        
    def attempt_proxies_fetch(self, method, proxies, attempt_amount, multithread_amount, url, data=None, parse_check=False):
        #Get attempts
        if attempt_amount == 'all':
            attempts = self.division(len(proxies),multithread_amount)[0]
        else:
            attempts = attempt_amount

        for i in range(attempts):
            #Get multithread proxies
            multithread_proxies=[]
            for j in range(multithread_amount):
                random_proxy = random.choice(proxies)
                multithread_proxies.append(random_proxy)
                proxies.remove(random_proxy)
                
            responses = self.multithread_proxies_fetch(method, multithread_proxies, url, data, parse_check)
            
            #Check for success result
            for j in responses.keys():
                response = responses[j]
                if response[0] == 'Success':
                    
                    #Print
                    print ('Did '+str(i+1)+' '+method+' multithread requests and got success')
                    
                    return [True, responses, response[1]]
        #Print            
        print ('Did '+str(i+1)+' '+method+' multithread requests and got no success')
        
        return [False, responses]

    def proxy_cors_bypasser(self, method, proxies, attempt_amount, multithread_amount, url, data=None, parse_check=False):
        #Create the proxy cors data
        proxy_cors={'status':None,'result':None}

        #Check if amount legal
        if attempt_amount == 'all':
            if self.legal_number(multithread_amount) == False:
                proxy_cors['status']='Invalid amount number'
                return proxy_cors
        elif self.legal_number(attempt_amount) == True:
            if self.legal_number(multithread_amount) == False:
                proxy_cors['status']='Invalid amount number'
                return proxy_cors
        else:
            proxy_cors['status']='Invalid amount number'
            return proxy_cors
        
        #Check if proxies legal
        if proxies == 'auto':
            try:
                proxies = self.get_free_proxies()
            except:
                proxy_cors['status']='Proxy list fetch error'
            if isinstance(proxies, list)==False:
                proxy_cors['status']='Proxy list fetch error'
        elif isinstance(proxies, list)==False:
            proxy_cors['status']='Invalid proxy data'
        
        #Check if enough proxies for amount
        if attempt_amount == 'all':
            if len(proxies) < multithread_amount:
                proxy_cors['status']='Not enough proxies'
                return proxy_cors
        else:
            if len(proxies) < attempt_amount * multithread_amount:
                proxy_cors['status']='Not enough proxies'
                return proxy_cors
                
        #Check if method legal
        if not (method == 'get' or method == 'post'):
            proxy_cors['status']='Invalid method'
            return proxy_cors
            
        #Attempt to fetch results
        results = self.attempt_proxies_fetch(method, proxies, attempt_amount, multithread_amount, url, data, parse_check)
        
        #Check results
        if results[0]==False:
        
            #Check for all Unknown error
            j=0
            for i in results[1].keys():
                if results[1][i][0] == 'Unknown error':
                    j+=1
            if j==len(results[1]):
                proxy_cors['status']='Unknown error'

            #If no all Uknown then No data 
            else:
                proxy_cors['status']='No data'
        
        else:
            proxy_cors['status']='Success'
            proxy_cors['result']=results[2]
        print ('Proxy cors finished with status '+proxy_cors['status'])
        return proxy_cors
    
@linkvertise_cors_bypasser.route('/')
def index():
    url = request.args.get('url')
    data = request.args.get('data')
    if (url != None) and (data == None):
        response = ProxyCorsBypasser().proxy_cors_bypasser('get', 'auto', 5, 20, url, None, True)
        return json.dumps(response)
    if (url != None) and (data != None):
        response = ProxyCorsBypasser().proxy_cors_bypasser('post', 'auto', 5, 20, url, json.loads(data), True)
        return json.dumps(response)
    return 'Welcome to the api...'
