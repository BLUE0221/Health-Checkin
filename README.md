# Checkin


## 使用方法
1. 将本项目 Fork 到自己的仓库。
2. 打开自己 Fork 之后的仓库，因为没有填写账户信息，此时若触发打卡，一定会失败。
3. 进入 `Settings` 选项，点击 `Secret`，并选择 `New Repository Secret`。依次添加以下变量：
   - `username`: 学号
   - `password`: 南京大学统一认证的密码
   - `location`: 你希望打卡的地理位置。比如南京大学仙林校区可以填 `中国江苏省南京市栖霞区九乡河东路`
   - `method`: 上一次核酸时间，字典类型，`interval`为检测间隔，字符串或数字，`start_time`为检测开始时间，需要精确到天，例如`{"interval":"3","start_time":"2022-4-12"}`"2022-04-24+10"




**使用方法**

1. 在config.json中填写南大统一身份认证的学号和密码以及上次核酸时间
2. 确保依赖库安装完整，`pip install -r requirements.txt`
3. `python checkin.py`后台运行即可运行一次
4. 若要每天自动运行，请在`contab -e`中添加以下命令：
	`0 12 * * * cd /path/to/checkin && python checkin.py`
5. 或自行查找如何Windows下的定时任务

运行后立即完成一次打卡，此后每天00:35分自动打卡

:rotating_light:**请务必如实上报健康状况**，如有异地出行、身体状况变动、本人或家人健康码非绿色，请停止使用此脚本。

### 参考&感谢

[yp51md/NJUcheckin](https://github.com/yp51md/NJUcheckin)  
[Boris-code/feapder](https://github.com/Boris-code/feapder)
