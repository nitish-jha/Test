import json
import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from collections import defaultdict

pd.options.display.max_columns = None
pd.options.display.max_rows = None

class o9KnowledgeHub:
    
    def __init__(self,Authorization,cache_loc = None,tenant_url = None,tenant_key = None):
        self.Authorization =  "ApiKey "+str(Authorization)
        self.headers = {
                        'Authorization': self.Authorization,
                        'Content-Type': 'application/json'
                    }
        self.payload = {}
        self.cache_loc = cache_loc
        self.tenant_url = tenant_url
        self.tenant_key = tenant_key
        
        self.country_filter = None
        self.time_filter = None
        self.category_filter= None
        
        master_data = requests.get('https://marketintel.trial.o9solutions.com/api/v2/master/MarketIntel',headers= self.headers)
        self.att_dim = dict()
        if master_data.status_code == 200:
            for i in master_data.json():
                for x in  i.get('KeyAttributes',[]):
                    self.att_dim.update({x.get('Name'):x.get('DimensionName')})
        

        fact_data =requests.get('https://marketintel.trial.o9solutions.com/api/v2/fact/MarketIntel',headers= self.headers)
        self.mg_att = defaultdict(list)
        self.mg_att_name = defaultdict(list)
        if fact_data.status_code == 200:
            for i in fact_data.json():
                for x in  i.get('KeyAttributes',[]):
                    self.mg_att[i.get('ResourceName')].append(x.get('DimensionName'))
                    self.mg_att_name[i.get('ResourceName')].append(x.get("Name"))
                
        
        '''Caching Implementation'''
        
        self.cache = dict()
        self.path = 'KH_Cache1.json'

        if os.environ.get('TENANT_NAME') is None:
            if os.path.isfile(self.path):    
                try:
                    with open(self.path,'r') as cachefile:
                        self.cache = json.load(cachefile)  
                except:
                    pass
        else:
            if self.cache_loc is not None and self.tenant_url is not None and self.tenant_key is not None:
                Cache_URL = f"{self.tenant_url}/api/Upload/Download?fileID={self.cache_loc}"
                try:
                    response = requests.get(Cache_URL, headers={'Authorization': "ApiKey "+self.tenant_key,'Content-Type': 'application/json'})
                    self.cache = response.json()
                except:
                    pass
         
        
        self.default_time=24
        if len(self.att_dim) == 0:
            print('Unable to fetch any data from server!!')

    def add_filter(self,country=None,period=None,category=None):
        self.country_filter = country
        self.time_filter = period
        self.category_filter = category
        
        
    def hash_key(self, val):
        return hash(val)
    
    def add_cache(self, key, val):
        expire = datetime.now() + (timedelta(hours=self.default_time))
        # self.cache[self.hash_key(key)] = expire, val
        self.cache[key] = expire.strftime("%Y-%m-%d %H:%M:%S.%f"), val.to_json()
        
        
        
    def get_cache(self, key):
        # key = self.hash_key(key)
        if key in self.cache:
            if datetime.now() < datetime.strptime(self.cache[key][0],"%Y-%m-%d %H:%M:%S.%f"):
                return pd.read_json(self.cache[key][1])
            else:
                self.cache.pop(key)
        return None
    
    def purge_cache(self):
        cache_keys = list(self.cache.keys())
        for key in cache_keys:
            if key in self.cache:
                try:
                    if datetime.now() > datetime.strptime(self.cache[key][0],"%Y-%m-%d %H:%M:%S.%f"):
                        self.cache.pop(key)
                except:
                    pass

            
    
    def get_catalog(self,filters = None,caching = True):
        '''
        Input: It will take a dictionary as input which is optional
        
        Process: This function will make two api request.
                One to Catalog Dimension and one to CatalogProp MeasureGroup
                The both api request results are merged on the ContentItem column.
                We can filter the data frame based on any column present in the final dataframe.
                If we filter based on any of the attribute then filter is applied on the api request itself.
                if we filter based on measures then filter is applied on the dataframe inmemory.
        
        Output: Catalog data as a dataframe (filtered if any filter are applied)
        '''
        
        
        
        url1 = "https://marketintel.trial.o9solutions.com/api/v2/master/MarketIntel/Catalog"
        # url2 = "https://marketintel.trial.o9solutions.com/api/v2/fact/MarketIntel/CatalogProp"

        
        if self.get_cache(url1) is not None and caching:
            df1 = self.get_cache(url1)
        else:   
            response1 = requests.request("GET", url1, headers=self.headers, data=self.payload)
            c = response1.json()
            cs = c['Data']['Catalogs']
            df1 = pd.DataFrame(cs)
            self.add_cache(url1,df1)
            
        df2 = self.get_measuregrp('CatalogProp',filters = filters,caching = caching)
        if not df2.empty:
            df1.reset_index(drop=True, inplace=True)
            df2.reset_index(drop=True, inplace=True)
            df = df1.merge(df2, on='ContentItem', how='inner')
                    
            '''Converting Date columns in the dataframe so that we can filter the dataframe based on dates'''

            df["ContentStartDate"] =  pd.to_datetime(df["ContentStartDate"], format="%Y/%m/%d")
            df["ContentEndDate"] =  pd.to_datetime(df["ContentEndDate"], format="%Y/%m/%d")
        else:
            df = df2
            
        if caching:   
            self.cache_loc = self.save_cache() 
        return df
    
    def make_global_filter(self):
        global_filter = dict()
        if self.country_filter is not None and type(self.country_filter)== dict:
            for keys in self.country_filter.keys():
                if str(self.att_dim.get(keys)) == 'Geo':
                    global_filter.update({keys:self.country_filter[keys]})
        if self.time_filter is not None and type(self.time_filter)== dict:
            for keys in self.time_filter.keys():
                if str(self.att_dim.get(keys)) == 'Time':
                    global_filter.update({keys:self.time_filter[keys]})
        if self.category_filter is not None and type(self.category_filter)== dict:
            for keys in self.category_filter.keys():
                if str(self.att_dim.get(keys)) == 'Catalog':
                    global_filter.update({keys:self.category_filter[keys]})
                    
        if len(global_filter)!=0:
            return global_filter
        else:
            return None
                
    
    def get_measuregrp(self,mgname,filters=None, cols=None,caching = True):
        '''
        Input:It takes three inputs 1.MeasureGroup Name 2.List of Measurenames to be displayed (Optional) 3.List of Filters to be displayed (Optional)
        
        Process:
        
        Output: MeasureGroup data as a Dataframe
        '''
        
        
        '''Preparing URL with filters'''

        if caching is False:
            self.cache  = dict()
        
        dfs = pd.DataFrame()
        final_filter = {}
        
        if filters and type(filters)==dict:
            url = f'https://marketintel.trial.o9solutions.com/api/v2/fact/MarketIntel/{mgname}?size=100000&filters=['
            MGfilters = []
            for key, value in filters.items():
                dimension = str(self.att_dim.get(key))
                if dimension != 'Time':
                    if dimension in self.mg_att.get(mgname) :
                        MGfilters.append('{"AttributeName" :"'+str(key)+'","Values":["'+'","'.join(value)+'"], "DimensionName" : "'+dimension+'"}')
                    else:
                        final_filter.update({key:value})
                else:
                    if len(value)==2:
                        MGfilters.append('{"AttributeName":"'+ str(key) +'","DateRanges":[{"op" : ">=", "value" : "' + str(value[0]) + '"}, {"op" : "<=", "value" : "' + str(value[1]) +'"}], "DimensionName" : "Time"}')
                    else:
                        print('Time filter must have 2 arguments, a start time and an end time')
                        return dfs
            
                   
            if len(MGfilters)!=0:
                url = url+','.join(MGfilters)
            url = url + "]"
            
        elif self.make_global_filter():
            global_filter = self.make_global_filter()
            url = f'https://marketintel.trial.o9solutions.com/api/v2/fact/MarketIntel/{mgname}?size=100000&filters=['
            MGfilters = []
            for key, value in global_filter.items():
                dimension = str(self.att_dim.get(key))
                if dimension != 'Time':
                    if dimension in self.mg_att.get(mgname) :
                        MGfilters.append('{"AttributeName" :"'+str(key)+'","Values":["'+'","'.join(value)+'"], "DimensionName" : "'+dimension+'"}')
                    else:
                        final_filter.update({key:value})
                else:
                    if len(value)==2:
                        MGfilters.append('{"AttributeName":"'+ str(key) +'","DateRanges":[{"op" : ">=", "value" : "' + str(value[0]) + '"}, {"op" : "<=", "value" : "' + str(value[1]) +'"}], "DimensionName" : "Time"}')
                    else:
                        print('Time filter must have 2 arguments, a start time and an end time')
                        return dfs
            
                   
            if len(MGfilters)!=0:
                url = url+','.join(MGfilters)
            url = url + "]"
            
        else:
            url = "https://marketintel.trial.o9solutions.com/api/v2/fact/MarketIntel/{}?size=100000".format(
                mgname)

        print(url)
        
        if self.get_cache(url) is not None and caching:
            dfs = self.get_cache(url)
        else:
            '''Parsing Response from API'''
            response = requests.request("GET", url, headers=self.headers, data=self.payload)
            
            if response.status_code == 200:
                x = response.json()
                xs = next(iter(x['Data'].values()))
                dfs = pd.DataFrame(xs)
                dfs.reset_index(drop=True, inplace=True)
                cursorKey = x.get('Cursor',None)


                '''Handling Pagination'''
                count = 0
                while cursorKey is not None:
                    count+=1
                    baseUrl = url + '&cursor=' + cursorKey
                    response = requests.request(
                        "GET", baseUrl, headers=self.headers, data=self.payload)
                    y = response.json()
                    if y.get('StatusCode') == 200:
                        ys = next(iter(y['Data'].values()))
                        ydfs = pd.DataFrame(ys)
                        ydfs.reset_index(drop=True, inplace=True)
                        dfs = pd.concat([dfs,ydfs])
                        cursorKey = y.get('Cursor',None)
                        
            dfs.reset_index(inplace=True)
            if caching:
                self.add_cache(url,dfs)
                    
        if dfs.empty:
            print('DataFrame is empty! Please check Measure group name and filters passed for errors. For further help, contact MarketIntel team.')
        
        
        
        
        ''' Filtering dataframe on columns that are not attribute'''
        
        query = ' & '.join([f'{k} in {v}' for k, v in final_filter.items() if k in dfs.columns])                                          
        try:
            dfs = dfs.query(query)
        except:
            pass
        
        
        
        '''Selecting Columns that are provided by the user'''
        
        if cols and type(cols)==list:
            dfs = dfs[[x for x in cols if x in dfs.columns]]
        if caching:
            self.cache_loc = self.save_cache()  
        return dfs
    
    
    
    def get_dim(self,dname, filters=None,caching = True):
        '''
        Input: Dimension name and Filters in an dictionary(optional)
        
        Process: Make an API request with filter if any filter is given as input.
        
        Output: Flattened view of the dimension data.
        '''
        
        
        
        '''Preparing URL with filters'''
        if caching is False:
            self.cache = dict()
        
        if filters and type(filters)==dict:
            url = f'https://marketintel.trial.o9solutions.com/api/v2/master/MarketIntel/{dname}?size=100000&filters=['
            DMfilters = []
            for key, value in filters.items():
                DMfilters.append('{"AttributeName" :"'+str(key)+'","Values":["'+'","'.join(value)+'"]}')
            if len(filters)!=0:
                url = url+','.join(DMfilters)
            url = url + "]"
            
        else:
            url = "https://marketintel.trial.o9solutions.com/api/v2/master/MarketIntel/{}?size=100000".format(
                dname)

        print(url)
        
        dfs = pd.DataFrame()
        
        if self.get_cache(url) is not None and caching:
            dfs = self.get_cache(url)
        else:
            response = requests.request("GET", url, headers=self.headers, data=self.payload)
            
            if response.status_code == 200:
                x = response.json()
                xs = next(iter(x['Data'].values()))
                dfs = pd.DataFrame(xs)
                dfs.reset_index(drop=True, inplace=True)
                cursorKey = x.get('Cursor',None)


                '''Handling Pagination'''
                while cursorKey is not None:
                    baseUrl = url + '&cursor=' + cursorKey
                    response = requests.request(
                        "GET", baseUrl, headers=self.headers, data=self.payload)
                    y = response.json()
                    if y.get('StatusCode') == 200:
                        ys = next(iter(y['Data'].values()))
                        ydfs = pd.DataFrame(ys)
                        ydfs.reset_index(drop=True, inplace=True)
                        dfs = pd.concat([dfs,ydfs])
                        cursorKey = y.get('Cursor',None)
                    else:
                        cursorKey = None
            if caching:
                self.add_cache(url,dfs)
                    
        if dfs.empty:
            print('DataFrame is empty! Please check Measure group name and filters passed for errors. For further help, contact MarketIntel team.')
        if caching:
            self.cache_loc = self.save_cache() 
        return dfs
    
    def save_cache(self):
        self.purge_cache()
        try:
            with open(self.path,'w') as cachefile:
                json.dump(self.cache,cachefile,default=str)

            if os.environ.get('TENANT_NAME') and self.tenant_url is not None and self.tenant_key is not None:
                updateurl = f"{self.tenant_url}/api/upload/v1/FileUpload/"
                files = {'upload_file': ('KH_Cache1.json', json.dumps(json.load(open('KH_Cache1.json','rb'))),'json')}
                response2 = requests.post(updateurl, headers={'Authorization':"ApiKey "+self.tenant_key},files=files)
                res = response2.json()

                try:
                    ret_var = res.get("files")[0]["fileId"]
                except:
                    ret_var = None
                
                return ret_var
        except:
            pass
        return None

    def get_cache_loc(self):
        return self.cache_loc
            