INTRODUCTION
---------------------

This package allows access to Knowledge stream's data via Knowledge hub(KHub) API's. You can use this package to view KHub catalog, to determine the type
of data you want to download. The catalog consists of various measure group data, dimensional data etc. Using this package's in-built functions, you can download
the required datasets into a dataframe.


REQUIREMENTS
---------------------

This model requires the following modules:-
1.pandas(https://pypi.org/project/pandas/)
2.json(built-in module)
3.requests(https://pypi.org/project/requests/)


INSTALLATION
---------------------

1.Place the folder in your root directory.
    C:\Python\Python38\Lib
2.Open command Prompt, and navigate to your root folder.
    C:\Python\Python38\Lib\o9knowledgehub
3.Run the command
    pip install .  


EXAMPLES  
---------------------

1. o9knowledgehub.get_catalog(): Returns the catalog file as a dataframe. No arguments required.

2. o9knowledgehub.get_measuregrp('Measure group name'): Returns measure group data as a dataframe. Measure group name is the function argument.

3. o9knowledgehub.get_dim('Dimension name'):Returns dimensional data as a datframe. Dimension name is the function argument


In[1]: import o9knowledgehub as gc
 ....: df = gc.get_catalog()
 ....: print(df)

Out[5]:
    ContentCategory ContentSource                                    ContentItem             ContentMeasureName ContentGeoCountry    ContentMeasureGroup  ...
0            Events        Google                              Academic Sessions                           None               USA                   None  ...
1            Events        Google  Academic Sessions - Semester Exams, Vacations                           None               NLD                   None  ...
2          Industry          FRED   Advanced Retail Sales (Nonfood) for USA, NSA  AdvancedRetailSalesNonfoodNSA               USA     RetailSalesMonthly  ...
3          Industry          FRED    Advanced Retail Sales (Nonfood) for USA, SA   AdvancedRetailSalesNonfoodSA               USA     RetailSalesMonthly  ...
4          Industry          FRED     Advanced Retail Sales (Total) for USA, NSA    AdvancedRetailSalesTotalNSA               USA     RetailSalesMonthly  ...
..              ...           ...                                            ...                            ...               ...                    ...


In[10]: df = gc.get_measuregrp('RetailSalesMonthly')
 .....: print(df.head())

Out[12]:
        Month        Version Name  ... RetailSalesTotalNSA  RetailSalesTotalSA
0  1990-01-01  CurrentWorkingView  ...                 NaN                 NaN
1  1990-01-01  CurrentWorkingView  ...                 NaN                 NaN
2  1990-02-01  CurrentWorkingView  ...                 NaN                 NaN
3  1990-02-01  CurrentWorkingView  ...                 NaN                 NaN
4  1990-03-01  CurrentWorkingView  ...                 NaN                 NaN


## Filtering Capabilities

Pass single or multiple filters. In the below example, measure group "WeatherDaily" is filtered at "City" and "Day" grain. You can also pass multiple cities and dates.
															   eg.gc.get_measuregrp('WeatherDaily',{'City':['Cold Bay : AK Aleutians East Borough','Dutch Harbor : AK Aleutians West Census Area']}) 



In[2]: df_filtered = gc.get_measuregrp('WeatherDaily',{'City':['Cold Bay : AK Aleutians East Borough'] , 'Day':['2016-01-05']})
.....: print(df_filtered)

Out[4]:
Version Name        Location         			   Day         City  					   HUMIDITYFC  PRCP  ...  TAVGFC  TMAX 
                                                                                                                                                                                    
CurrentWorkingView  Cold Bay : AK Aleutians East Borough   2016-01-05  Cold Bay : AK Aleutians East Borough         NaN        3.8   ...   NaN    1.1     
