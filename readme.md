Students:
- Virgile BRIAN
- Quentin AVARE
- Clément RIIVERE

There are few steps that need to be done as prerequisites in order to run the code :

- Have access to an Internet Connexion
- You have to be situated in the right folder i.e "windfinder_api"
- Go in the config.py file in the flask_api folder and change the chromium path with your personal one (line 4) following the exemple that is given.
- There are few packages that are needed to run the app.py file. In order to make sure the environment is well defined, please proceed to this step considering the case you use conda or pip:
    1] If you use conda, write in your terminal the following command: 
        $ conda env create -f api_env.yml
    2] If you use pip, write in your terminal the following command: 
        $ pip install -r /path/to/requirements.txt
- You then need to activate the environment by writing the follow command:
        $ conda activate api-env
-  You can run execute the api through the command: 
        $ python ./flask_api/app.py
        
As an additional feature, you are able to execute SQL queries in the test_sql.ipynb file. For instance, you are able to execute queries and filter the data based on some parameters such as the wind speed or the temperature.
# Python-Scrapper-Windguru
# Python-Scrapper-Windguru
