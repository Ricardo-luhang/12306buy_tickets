from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.views.generic import View
import requests
from json import loads, dumps
from .cons import station_message
from .discaptcha import get_captcha, send_erorr
from django.template import loader, Context

# Create your views here.

s = requests.session()
headers = {
    'User - Agent': 'Mozilla / 5.0(Windows NT 6.1;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome / 65.0'
                    ' .3325.146Safari / 537.36'
}


class Checkticket(View):
    def get(self, request):
        return render(request, '12306.html')

    def post(self, request):
        start_station = request.POST.get('start_station', '')
        end_station = request.POST.get('end_station', '')
        start_time = request.POST.get('start_time', '')
        end_time = request.POST.get('end_time', '')

        station_alias = station_message()
        train_date = start_time
        try:
            from_station = station_alias[start_station]
            to_station = station_alias[end_station]
            url = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={0}&leftTicketDTO.from_station' \
                  '={1}&leftTicketDTO.to_station={2}&purpose_codes=ADULT'.format(train_date, from_station, to_station)
            response = s.get(url, headers=headers)
            messages = loads(response.text)
            trans_mes = messages['data']['result']
            global mes_list
            mes_list = []
            for i in trans_mes:
                res1 = i.split('|')
                is_first = 'no'
                is_end = 'no'
                if res1[4] == res1[6]:
                    is_first = 'yes'
                if res1[5] == res1[7]:
                    is_end = 'yes'
                mes = {'train_no': res1[2], 'train_num': res1[3], 'from_station': start_station,
                       'to_station': end_station, 'start_time': res1[8], 'end_time': res1[9],
                       'times': res1[10], 'depart_time': res1[13], 'business_class': res1[32],
                       'soft_sleeper': res1[21], 'first_class': res1[31], 'seconde_class': res1[30],
                       'Still_lie': res1[33], 'soft_lie': res1[23], 'hard_lie': res1[28],
                       'hard_seat': res1[29], 'no_seat': res1[26], 'is_first': is_first, 'is_end': is_end,
                       'from_station_no': res1[16], 'to_station_no': res1[17], 'seat_type': res1[35]
                       }
                for key in mes:
                    if mes[key] == '':
                        mes[key] = '-'
                mes_list.append(mes)
        except KeyError:
            print('车站信息有误')
        return render(request, '12306.html', {'mes_list': mes_list})


class Stopstation(View):
    def get(self, request):
        tran_no = request.GET.get('train_no', '')
        from_station = request.GET.get('from_station', '')
        to_station = request.GET.get('to_station', '')
        pre_depart_time = request.GET.get('depart_time', '')
        train_num = request.GET.get('train_num', '')
        depart_time = pre_depart_time[:4] + '-' + pre_depart_time[4:6] + '-' + pre_depart_time[6:8]
        station_alias = station_message()
        tran_no = tran_no
        from_station = station_alias[from_station]
        to_station = station_alias[to_station]
        depart_time = depart_time
        url = 'https://kyfw.12306.cn/otn/czxx/queryByTrainNo?train_no={0}&from_station_telecode={1}&' \
              'to_station_telecode={2}&depart_date={3}'.format(tran_no, from_station, to_station, depart_time)
        response = s.get(url, headers=headers).text
        mes = loads(response)
        mes1 = mes['data']['data']
        mes_list = []
        for i in mes1:
            mes_dic = {
                'station_no': i['station_no'],
                'station_name': i['station_name'],
                'arrive_time': i['arrive_time'],
                'start_time': i['start_time'],
                'stopover_time': i['stopover_time'],
                'tran_num': train_num
            }
            mes_list.append(mes_dic)
        my_list = dumps(mes_list, ensure_ascii=False)
        return HttpResponse(my_list)


class Price(View):
    def get(self, request):
        train_no = request.GET.get('train_no', '')
        from_station_no = request.GET.get('from_station_no', '')
        to_station_no = request.GET.get('to_station_no', '')
        seat_type = request.GET.get('seat_type', '')
        if seat_type == '1431':  #通过实验，有时会返回1431，所以做此步操作
            seat_type = '1413'
        pre_depart_time = request.GET.get('train_data', '')
        depart_time = pre_depart_time[:4] + '-' + pre_depart_time[4:6] + '-' + pre_depart_time[6:8]
        url = 'https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice?train_no={0}&from_station_no={1}&to_station_' \
              'no={2}&seat_types={3}&train_date={4}'.format(train_no, from_station_no, to_station_no, seat_type,
                                                            depart_time)
        response = requests.get(url, headers=headers).text
        message = loads(response)['data']
        price_mes = {}
        if seat_type == '1413':
            price_mes = {'hard_seat': message.get('A1', ''), 'hard_sleeper': message.get('A3', ''), 'soft_sleeper': message.get('A4', ''),
                         'none_seat': message.get('A1', '')}
        elif seat_type == '14163' or seat_type == '14613':
            price_mes = {'hard_seat': message.get('A1', ''), 'hard_sleeper': message.get('A3', ''), 'soft_sleeper': message.get('A4', ''),
                         'none_seat': message.get('A1', ''), 'advanced_soft_sleeper': message.get('A6', '')}
        elif seat_type == 'O9MO' or seat_type == 'O9OM':
            price_mes = {'first_class_seat': message.get('M', ''), 'seconde_class_seat': message.get('O', ''),
                         'business_class': message.get('A9', ''), 'none_seat': message.get('O', '')}
        elif seat_type == 'OM9' or seat_type == 'O9M':
            price_mes = {'first_class_seat': message.get('M', ''), 'seconde_class_seat': message.get('O', ''),
                         'business_class': message.get('A9', '')}
        elif seat_type == 'OMP':
            price_mes = {'first_class_seat': message.get('M', ''), 'seconde_class_seat': message.get('O', ''),
                         'principal_seat': message.get('P', '')}
        elif seat_type == 'OO4':
            price_mes = {'soft_sleeper': message.get('A4', ''), 'seconde_class_seat': message.get('O', ''), 'none_seat': message.get('O', '')}
        elif seat_type == 'F4':
            price_mes = {'soft_sleeper': message.get('A4', ''), 'sleeper': message.get('F', '')}
        elif seat_type == 'OMO' or seat_type == 'OOM':
            price_mes = {'first_class_seat': message.get('M', ''), 'seconde_class_seat': message.get('O', ''),
                         'none_seat': message.get('O', '')}
        else:
            print(seat_type)
        owgs = {
            'train_no': train_no,
            'seat_type': seat_type,
            'price_mes': price_mes
        }

        return JsonResponse(owgs)


class Login(View):
    def post(self, request):
        mes = ''
        username = request.POST.get('username', '')
        print(username)
        password = request.POST.get('password', '')
        train_no = request.POST.get('train_no', '')
        train_data = request.POST.get('train_data', '')
        from_data = request.POST.get('from_data', '')
        from_station = request.POST.get('from_station', '')
        times = request.POST.get('times', '')
        to_data = request.POST.get('to_data', '')
        to_station = request.POST.get('to_station', '')
        seat_type = request.POST.get('seat_type', '')
        para = {
            'train_no': train_no, 'train_data': train_data, 'from_data': from_data,
            'from_station': from_station, 'times': times, 'to_data': to_data,
            'to_station': to_station, 'seat_type': seat_type
        }
        url = 'https://kyfw.12306.cn/passport/captcha/captcha-check'
        url1 = 'https://kyfw.12306.cn/passport/captcha/captcha-image' \
               '?login_site=E&module=login&rand=sjrand&0.8630462336106017'
        image_res = s.get(url1, headers=headers).content
        print('获取验证码')
        with open('code.png', 'wb+') as f:
            f.write(image_res)

        print('验证码验证')
        code, pic_id = get_captcha()
        data = {
            'answer': code,
            'login_site': 'E',
            'rand': 'sjrand',
        }
        cap_res = s.post(url, headers=headers, data=data).text
        cap_rul = loads(cap_res)
        if cap_rul['result_message'] == '验证码校验失败':
            send_erorr(pic_id)
            mes = '验证码校验失败'
            return HttpResponse(mes)
        url_login = 'https://kyfw.12306.cn/passport/web/login'
        data_login = {
            'username': username,
            'password': password,
            'appid': 'otn'
        }
        first_res = s.post(url_login, headers=headers, data=data_login).text
        result = loads(first_res)
        print(result['result_message'])
        if result['result_message'] != '登录成功':
            mes = '密码输入错误，错误超过5次，用户将被锁定'
            return HttpResponse(mes)
        url2 = 'https://kyfw.12306.cn/otn/login/userLogin'
        data = {
            '_json_att': ''
        }
        s.post(url2, headers=headers, data=data)
        url3 = 'https://kyfw.12306.cn/otn/passport?redirect=/otn/login/userLogin'
        s.get(url3, headers=headers)
        url4 = 'https://kyfw.12306.cn/passport/web/auth/uamtk'
        data = {
            'appid': 'otn'
        }
        res = s.post(url4, headers=headers, data=data).text
        res_para = loads(res)
        try:
            tk = res_para['newapptk']
            url5 = 'https://kyfw.12306.cn/otn/uamauthclient'
            data = {
                'tk': tk
            }
            response = s.post(url5, headers=headers, data=data).text
            response = loads(response)
            print(response['result_message'])
            if response['result_message'] == '验证通过':
                para = Context(para)
                html = loader.get_template('buy_ticket.html').render({'para': para})
                return HttpResponse(html)
            else:
                mes = '验证未通过。'
        except KeyError as ex:
            print('未知错误')
        return HttpResponse(mes)


class Buyticket(View):
    def get(self, request):
        train_no = request.GET.get('train_no', '')
        train_data = request.GET.get('train_data', '')
        from_data = request.GET.get('from_data', '')
        from_station = request.GET.get('from_station', '')
        times = request.GET.get('times', '')
        to_data = request.GET.get('to_data', '')
        to_station = request.GET.get('to_station', '')
        seat_type = request.GET.get('seat_type', '')
        kwgs = {
            'train_no': train_no,
            'train_data': train_data,
            'from_data': from_data,
            'from_station': from_station,
            'times': times,
            'to_data': to_data,
            'to_station': to_station,
            'seat_type': seat_type,
        }
        return render(request, 'buy_ticket.html', kwgs)

    def post(self, request):
        pass
