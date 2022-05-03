import json
import re
import os
import time
import urllib
import requests
import execjs
from pytz import timezone
from bs4 import BeautifulSoup
from collections import namedtuple
import datetime
import ddddocr

encrypt_js_script = "encrypt.js"
agent = "Mozilla/5.0 (Linux; Android 12; M2007J1SC Build/SKQ1.220213.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/100.0.4896.127 Mobile Safari/537.36 cpdaily/9.0.15 wisedu/9.0.15"
urls = {
	"login": "https://authserver.nju.edu.cn/authserver/login?service=http%3A%2F%2Fehallapp.nju.edu.cn%2Fxgfw%2Fsys%2Fyqfxmrjkdkappnju%2Fapply%2FgetApplyInfoList.do",
	"health_history": "http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/getApplyInfoList.do",
	"check_in": "http://ehallapp.nju.edu.cn/xgfw//sys/yqfxmrjkdkappnju/apply/saveApplyInfos.do",
	"captcha": "https://authserver.nju.edu.cn/authserver/captcha.html"
}

def encrypt(password, encrypt_salt):
	with open(encrypt_js_script, 'r') as f: 
		script = ''.join(f.readlines())
	context = execjs.compile(script)
	return context.call('encryptAES', password, encrypt_salt)

def readcode(session):
	r = session.get(urls['captcha'])
	ocr = ddddocr.DdddOcr(show_ad=False)
	res = ocr.classification(r.content)
	return res


def login(session, username, password):
	code = readcode(session)
	r = session.get(urls['login'])
	soup = BeautifulSoup(r.text, 'html.parser')
	input_boxes = soup.find_all('input')
	
	input_info = {}
	for i in input_boxes:
		name, value = i.get('name'), i.get('value')
		if name not in ["username", "password", "captchaResponse", None]:
			input_info[name] = value 
	
	pattern = re.compile(r"var pwdDefaultEncryptSalt = (.*?);", re.MULTILINE | re.DOTALL)
	encrypt_script = str(soup.find("script", text=pattern))
	pwdDefaultEncryptSalt = re.search('pwdDefaultEncryptSalt = "(.*?)";', encrypt_script).group(1)
	headers = {
		'User-Agent': agent,
		'Origin': "https://authserver.nju.edu.cn",
		'Referer': urls['login'],
		'Content-Type': 'application/x-www-form-urlencoded'
	}

	data = {
		'username': username,
		'password': encrypt(password, pwdDefaultEncryptSalt),
		'captchaResponse': code,
		'lt': input_info["lt"],
		'dllt': input_info["dllt"],
		'execution': input_info["execution"],
		'_eventId': input_info["_eventId"],
		'rmShown': input_info["rmShown"]
	}
	session.post(urls['login'], data=urllib.parse.urlencode(data), headers=headers)
	

def check_login(session, location):
	r = session.get(urls['health_history'])
	try:
		history = json.loads(r.text)
		assert history['code'] == '0'
	except:
		# assert 0, "Fail to login"
		return None, location, False

	print("Log in Successfully")
	wid = history['data'][0]['WID']
	if location == 'default':
		location = history['data'][1]['CURR_LOCATION']
	return wid, location, True


def checkin(session, checkin_info):
	info_t = namedtuple('Checkin_Info', 
		['WID', 'CURR_LOCATION', 'IS_TWZC', 'IS_HAS_JKQK', 'JRSKMYS', 'JZRJRSKMYS', 'SFZJLN', 'ZJHSJCSJ']
	)
	info = info_t._make(checkin_info)
	checkin_url = urls['check_in']+'?'
	for key, value in info._asdict().items():
		checkin_url += f'{key}={value}&'
	checkin_url = checkin_url[:-1]  # drop last &

	r = session.get(checkin_url)
	result = json.loads(r.text)

	cur_time = datetime.datetime.now()
	if result['code'] == '0' and result['msg'] == '成功':
		print(f"successfully, {cur_time}")
		return True 
	else: 
		print(f"failed, {cur_time}")
		return False
	
def get_zjhs_time(method='YESTERDAY'):
    today = datetime.datetime.now(timezone('Asia/Shanghai'))
    yesterday = today + datetime.timedelta(-1)
    if method == 'YESTERDAY':
        return yesterday.strftime("%Y-%m-%d %-H")
    else:
        eval_method = method
        try:
            start_time = datetime.datetime.strptime(
                eval_method['last_RNA'], "%Y-%m-%d").date()
            interval = int(eval_method['interval'])
            covid_test_time = today - \
                datetime.timedelta((today.date()-start_time).days % interval)
        except ValueError as e:
            covid_test_time = yesterday
        #     log.error(e)
        #     log.error("设置核酸检测时间为昨日")
        # log.info(f"最近核酸检测时间为{covid_test_time}")
        return covid_test_time.strftime("%Y-%m-%d %-H")


def main():
	with open("config.json", "r", encoding='utf-8') as f:
		info = json.load(f)
	info["student_id"]=os.getenv('NJU_USERNAME')
	info["password"]=os.getenv('NJU_PASSWORD')
	info["location"]=os.getenv('CURR_LOCATION')
	info["interval"]="5"
	info["last_RNA"]=os.getenv('COVID_TEST_METHOD')
	
	session = requests.Session()
	session.cookies = requests.cookies.RequestsCookieJar()
	session.headers["User-Agent"] = "Mozilla/5.0 (Linux; Android 12; M2007J1SC Build/SKQ1.220213.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/100.0.4896.127 Mobile Safari/537.36 cpdaily/9.0.15 wisedu/9.0.15"
	session.headers["Accept"] = "application/json, text/plain, */*"
	session.headers["Accept-Encoding"] = "gzip, deflate"
	session.headers["X-Requested-With"] = "X-Requested-With: com.wisedu.cpdaily.nju"
	session.headers["Referer"] = "http://ehallapp.nju.edu.cn/xgfw/sys/mrjkdkappnju/index.html"



	assert 'student_id' in info, "Expected infomation `student_id` not found. Check config.json"
	assert "password" in info, "Expected infomation `password` not found. Check config.json"

	login(session, username=info['student_id'], password=info['password'])
	wid, location, status = check_login(session, info['location'])
	if not status:
		return False
	info['last_RNA']=get_zjhs_time(info)
	health_status = (
		wid,                            # WID
		location,                       # 地点
		info['body_temp_ok'],           # 体温正常
		info['health_status'],          # 健康状况
		info['my_health_code_color'],   # 本人苏康码颜色
		info['fam_mem_health_code_color'],   # 家人苏康码颜色
		info['leave_Nanjing'],			# 14天是否离宁
		info['last_RNA']				# 上次核酸时间
	)
	return checkin(session, health_status)
	

if __name__ == '__main__':
	result = main()
	# print(result)
	while(not result):
		time.sleep(60)
		result = main()
