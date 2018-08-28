import requests
from hashlib import md5
from .codes import codesuser, codespwd


class Chaojiying_Client(object):
    def __init__(self, username, password, soft_id):
        self.username = username
        password = password.encode('utf8')
        self.password = md5(password).hexdigest()
        self.soft_id = soft_id
        self.base_params = {
            'user': self.username,
            'pass2': self.password,
            'softid': self.soft_id,
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
        }

    def PostPic(self, im, codetype):
        """
        im: 图片字节
        codetype: 题目类型 参考 http://www.chaojiying.com/price.html
        """
        params = {
            'codetype': codetype,
        }
        params.update(self.base_params)
        files = {'userfile': ('ccc.jpg', im)}
        r = requests.post('http://upload.chaojiying.net/Upload/Processing.php', data=params, files=files,
                          headers=self.headers)
        return r.json()

    def ReportError(self, im_id):
        """
        im_id:报错题目的图片ID
        """
        params = {
            'id': im_id,
        }
        params.update(self.base_params)
        r = requests.post('http://upload.chaojiying.net/Upload/ReportError.php', data=params, headers=self.headers)
        return r.json()


def get_captcha():
    chaojiying = Chaojiying_Client(codesuser, codespwd, '896973')
    im = open('code.png', 'rb').read()
    response = chaojiying.PostPic(im, 9004)
    pic_id = response['pic_id']
    the_code = response['pic_str'].replace('|', ',')
    the_code = the_code.split(',')
    x_list = the_code[0::2]
    y_list = the_code[1::2]
    s = ''
    for i in zip(x_list, y_list):
        y = int(i[1]) - 30
        s += '%s,%s,'%(i[0], y)
    return s[:-1], pic_id


def send_erorr(pic_id):
    chaojiying = Chaojiying_Client(codesuser, codespwd, '896973')
    the_code = chaojiying.ReportError(pic_id)
    return the_code





