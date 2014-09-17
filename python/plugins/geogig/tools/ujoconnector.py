import requests
from geogig.gui import executor
from repodecorator import UjoRepository
import json
from geogig import config

UJO_URL = "http://ujo.dev.boundlessgeo.com/"

def endpoint():
    url = config.getConfigValue(config.GENERAL, config.UJO_ENDPOINT)
    if not url.endswith("/"):
        url = url + "/"
    return url

def getUjoRepositories(user, password):
    def _getRepos():                
        r = requests.get(endpoint() + "users/%s/repos?type=all" % user, 
                         auth=(user, password))
        try:
            r.raise_for_status()
        except Exception, e:
            if "not found" in e.args[0].lower():
                if "User has no repos" in r.json()["message"].lower():
                    return []
                else:
                    raise AuthenticationException()
            else:
                raise e               
        repos = r.json()  
        if repos:        
            return [UjoRepository(repo["apiUrl"].replace("/api/", endpoint() ), 
                              user, password, repo) for repo in repos["repos"]]
        else:
            return []
    return executor.execute(_getRepos, "Retrieving Ujo repositories")


def createUjoRepository(user, password, name, title, description):
    def _createUjo():        
        data = {"name": name, "title": title, "description": description}
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post(endpoint()  + "users/%s/repos" % user, 
                          data=json.dumps(data), headers=headers, auth=(user, password))
        r.raise_for_status()
        r = requests.get(endpoint()  + "repos/%s/%s" % (user, name), auth=(user, password))
        r.raise_for_status()
        return UjoRepository(endpoint()  + "repos/%s/%s" % (user, name), user, password, r.json())
    return executor.execute(_createUjo, "Creating Ujo repository")


class AuthenticationException(Exception):
    pass