import requests
import json
from util import md5

PWD = 'password001'

def text_gen(xinput, xusername=''):
    xjson = dict()
    xjson['input'] = xinput
    xjson['username'] = xusername

    xcheck = xinput + PWD
    xcheck = md5(xcheck)
    xjson['check'] = xcheck

    res = requests.post('http://127.0.0.1:7777/api', json=xjson)
    xjson = json.loads(res.text)
    xouput = xjson['output']
    return xouput


if '__main__' == __name__:

    # xjson = dict()
    # xjson['input'] = '您好！怎么去八达岭？'
    # res = requests.post('http://127.0.0.1:7777/api', json=xjson)
    # xjson = json.loads(res.text)
    # print(xjson)

    xoutput = text_gen('我们的学习很有思意呀！')
    print('out:', xoutput)
