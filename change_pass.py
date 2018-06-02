#!/usr/local/bin/python3
import configparser
import os
import requests
import string
from random import choices

config = configparser.ConfigParser()
dir_path = os.path.dirname(os.path.realpath(__file__))
config.read(f'{dir_path}/config.ini')
router_ip = config['ROUTER']['ip']
router_username = config['ROUTER']['username']
router_password = config['ROUTER']['password']
wifi_ssid = config['WIFI']['ssid']
wifi_password_length = int(config['WIFI']['password_length'])

new_pass = ''.join(choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=wifi_password_length))

two_four_band_dict = {'RadioWlanInterface': 0}

password_dict = {'PrimaryNetworkEnable': 1,
                 'ServiceSetIdentifier': wifi_ssid,
                 'ClosedNetwork': 0,
                 'BssModeRequired': 0,
                 'WpaPskAuth': 0,
                 'Wpa2PskAuth': 1,
                 'WpaEncryption': 2,
                 'WpaPreSharedKey': new_pass,
                 'PlainTextKey': '',
                 'EncryptedKey': '',
                 'WpaRekeyInterval': 0,
                 'GenerateWepKeys': 0,
                 'WepKeysGenerated': 0,
                 'commitwlanPrimaryNetwork': 1,
                 'AutoSecurity': 1}


try:
    response = requests.post(f'http://{router_ip}/goform/wlanRadio',
                             data=two_four_band_dict,
                             auth=(router_username, router_password))
    assert response.status_code == 200
    response = requests.post(f'http://{router_ip}/goform/wlanPrimaryNetwork',
                             data=password_dict,
                             auth=(router_username, router_password))
    assert response.status_code == 200
    assert new_pass in response.content.decode("utf-8")
    config['WIFI']['password'] = new_pass
    with open(f'{dir_path}/config.ini', 'w') as f:
        config.write(f)
    print(f'Wifi password was successfully altered')
except AssertionError:
    print(f'Wifi password could not be changed, received a {response.status_code} from the router POST')
except requests.exceptions.Timeout:
    print(f'The request to change the Wifi password timed out')
except requests.exceptions.TooManyRedirects:
    print(f'The request to change the Wifi password redirected too many times and was not able to complete')
except requests.exceptions.RequestException:
    print(f'The request to change the Wifi password incurred an unknown error')

try:
    with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'r') as f:
        lines = f.readlines()
        for index, line in enumerate(lines):
            if f'ssid="{wifi_ssid}"' in line:
                break
        update_index = index + 1
        lines[update_index] = f'\tpsk="{new_pass}"\n'
    with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as f:
        for line in lines:
            f.write(line)
except NameError as e:
    print(e)
