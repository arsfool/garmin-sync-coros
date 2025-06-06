import urllib3
import json
import hashlib

import certifi


from coros.region_config import REGIONCONFIG
from coros.sts_config import STS_CONFIG

class CorosClient:
    
    def __init__(self, email, password) -> None:
        
        self.email = email
        self.password = password
        self.req = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        self.accessToken = None
        self.userId = None
        self.regionId = None
        self.teamapi = None
    
    ## 登录接口
    def login(self):
        ## default use com login url
        login_url = "https://teamcnapi.coros.com/account/login"

        login_data = {
            "account": self.email,
            "pwd": hashlib.md5(self.password.encode()).hexdigest(), ##MD5加密密码
            "accountType":2,
        }
        headers = {
          "Accept":       "application/json, text/plain, */*",
          "Content-Type": "application/json;charset=UTF-8",
          "User-Agent":   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.39 Safari/537.36",
          "referer": "https://teamcnapi.coros.com/",
          "origin": "https://teamcnapi.coros.com/",
        }

        login_body = json.dumps(login_data)
        response = self.req.request('POST', login_url, body=login_body, headers=headers)

        login_response = json.loads(response.data)
        login_result = login_response["result"]
        if login_result != "0000":
            raise CorosLoginError("Coros login anomaly, the reason for the anomaly is:" + login_response["message"])

        accessToken = login_response["data"]["accessToken"]
        userId =  login_response["data"]["userId"]
        regionId =  login_response["data"]["regionId"]
        self.accessToken = accessToken
        self.userId = userId
        self.regionId = regionId
        self.teamapi = REGIONCONFIG[self.regionId]['teamapi']

    ## 上传运动
    def uploadActivity(self, oss_object, md5, fileName, size):
        ## 判断Token 是否为空
        if self.accessToken == None:
            self.login()

        upload_url = f"{self.teamapi}/activity/fit/import"

        headers = {
          "Accept":       "application/json, text/plain, */*",
          "accesstoken": self.accessToken,
        }
     
        try:
          bucket = STS_CONFIG[self.regionId]["bucket"]
          serviceName = STS_CONFIG[self.regionId]["service"]
          data = {"source":1,"timezone":32,"bucket":f"{bucket}","md5":f"{md5}","size":size,"object":f"{oss_object}","serviceName":f"{serviceName}","oriFileName":f"{fileName}"}
          json_data = json.dumps(data)
          json_str = str(json_data)
          print(json_str)
          response = self.req.request(
              method = 'POST',
              url=upload_url,
              fields={ "jsonParameter": json_str},
              headers=headers
          )
          upload_response = json.loads(response.data)
          print(upload_response)
          if upload_response["data"].get("status") == 2 and  upload_response["result"] == "0000":
             return True
          else:
             return False
        except Exception as err:
            exit() 

    def getActivities(self, size:int, page:int):
        self.checkToken()
        activitys_url = f"{self.teamapi}/activity/query?size={size}&pageNumber={page}"
        headers = {
          "Accept":       "application/json, text/plain, */*",
          "accesstoken": self.accessToken,
        }
        try:
          response = self.req.request(
              method = 'GET',
              url=activitys_url,
              headers=headers
          )
          response = json.loads(response.data)
          return response
        except Exception as err:
            exit() 
     ## 获取所有运动
    def getAllActivities(self): 
      all_activities = []
      size = 200
      page = 1
      while(True):
        activities = self.getActivities(size, page)
        totalPage = activities['data']['totalPage']
        if totalPage >= page:
          all_activities.extend(activities['data']['dataList'])
        else:
          return all_activities
        page += 1
    

    def downloadActivitie(self, id, sport_type):
       self.checkToken()
       ## 文件下载链接
       get_activity_download_url = f"{self.teamapi}/activity/detail/download?labelId={id}&sportType={sport_type}&fileType=4"
       headers = {
          "Accept":       "application/json, text/plain, */*",
          "accesstoken": self.accessToken,
       }
       try:
          get_activity_download_url_response = self.req.request(
              method = 'POST',
              url=get_activity_download_url,
              headers=headers
          )
          get_activity_download_url_response_json = json.loads(get_activity_download_url_response.data)
          download_url = get_activity_download_url_response_json['data']['fileUrl']
          return self.req.request(
              method = 'GET',
              url=download_url,
              headers=headers
          )
       except Exception as err:
            exit() 
       pass

    ## 检查token是否有效
    def checkToken(self):
        ## 判断Token 是否为空
        if self.accessToken == None:
            self.login()
class CorosLoginError(Exception):

    def __init__(self, status):
        """Initialize."""
        super(CorosLoginError, self).__init__(status)
        self.status = status

class CorosActivityUploadError(Exception):

    def __init__(self, status):
        """Initialize."""
        super(CorosActivityUploadError, self).__init__(status)
        self.status = status