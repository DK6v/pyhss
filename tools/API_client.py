#!/usr/bin/env python3

import sys
import logging
import requests
import json
import datetime

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log= logging.getLogger("API:C")

base_url = 'http://localhost:8080'

supported_calls = [
    "1: IMS_SUBSCRIBER",
    "2: AUC",
    "3: APN",
    "4: AUC+APN+SUBSCRIBER",
]

class IMS_SUBSCRIBER:

    name = 'IMS_SUBSCRIBER'
    template = {}

    def createTemplate(self, imsi_prefix = None):

        self.template = {
            "ifc_path": "IFC_PATH",
            "pcscf": "PCSCF",
            "pcscf_realm": "PCSCF_REALM",
            "pcscf_active_session": "PCSCF_ACTIVE_SESSION",
            "pcscf_peer": "PCSCF_PEER",
            "xcap_profile": '<Profile></Profile>',
            "sh_profile": '<Profile></Profile>',
            "scscf": "SCSCF",
            "scscf_realm": "SCSCF_REALM",
            "scscf_peer": "SCSCF_PEER",
            "sh_template_path": "SH_TEMPLATE_PATH",
        }

        print(str(datetime.datetime.now().isoformat(timespec='seconds')))

        print(f'\n{self.name} records template data:')

        self.template['scscf'] = \
            str(input("Template data - SCSCF (default: SCSCF):\t").strip() or "SCSCF")
    
        if imsi_prefix == None:
            self.template['imsi'] = \
                str(input('Enter IMSI prefix, ' \
                          'format <prefix><paddig><id> (default: 25080): ') or "25080")
        else:
            self.template['imsi'] = imsi_prefix

        return self

    def generate(self):
        
        print(f'\n{self.name} records generator:')
        start = int(input("Enter initial record <id> (default: 1): ").strip() or 1)
        count = int(input("Enter number of records (default: 1): ").strip() or 1)

        for id in range(start, start + count):
            self.create(id)

    def getById(self, id):
        return requests.get(str(base_url) + '/ims_subscriber/' + str(id)).json() or {}

    def getByImsi(self, imsi):
        return requests.get(str(base_url) + '/ims_subscriber/imsi/' + str(imsi)).json() or {}

    def create(self, id):

        data = self.template.copy()
        data['ims_subscriber_id'] = id
        data['imsi'] = self.template['imsi'] + str(id).zfill(15 - len(self.template['imsi']))

        ims_subscriber_id = self.getById(id).get('ims_subscriber_id')
        if ims_subscriber_id:
            log.info('{} Record already exists: id={}'.format(
                self.name, ims_subscriber_id))
            return ims_subscriber_id
      
        ims_subscriber_id = self.getByImsi(data['imsi']).get('ims_subscriber_id')
        if ims_subscriber_id:
            log.info('{} Record already exists: imsi={} '.format(
                self.name, data['imsi']))
            return ims_subscriber_id

        data["msisdn"] = data["imsi"]
        data["msisdn_list"] = data["imsi"]

        headers = {"Content-Type": "application/json"}
        r = requests.put(str(base_url) + '/ims_subscriber/', data=json.dumps(data), headers=headers)
        if r.json() != None:
            ims_subscriber_id = r.json().get('ims_subscriber_id')
            log.info("{} record created: id={}, imsi={}".format(
                self.name, ims_subscriber_id, str(r.json().get("imsi"))
            ))
        else:
            log.error("{} Failed to create record, imsi= {} ".format(
                self.name, data["imsi"]
            ))

        return ims_subscriber_id

class AUC: # Authentication Center (AUC)

    name = 'AUC'
    template = {}

    def createTemplate(self, imsi_prefix = None):

        self.template = {
            "ki": "KI",
            "opc": "OPC",
            "amf": "AMF",
            "sqn": 0,
            "batch_name": "BATCH_NAME",
            "sim_vendor": "SIM_VENDOR",
            "esim": False,
            "lpa": "LPA",
            "pin1": "PIN1",
            "pin2": "PIN2",
            "puk1": "PUK1",
            "puk2": "PUK2",
            "kid": "KID",
            "psk": "PSK",
            "des": "DES",
            "adm1": "ADM1",
            "misc1": "MISC1",
            "misc2": "MISC2",
            "misc3": "MISC3",
            "misc4": "MISC4"
        }

        print(f'\n{self.name} records template data:')

        self.template['ki'] = \
            str(input('Enter Authentication Key (KI) prefix, ' \
                      'format <prefix><padding><id> (default: 0..0): '))
    
        self.template['opc'] = \
            str(input('Enter Network Operators key OPc (OPC) prefix, ' \
                      'format <prefix><padding><id> (default: 0..0): '))
    
        self.template['amf'] = \
            str(input('Enter Authentication Management Field (AMF) ' \
                      '(default: 8000): ') or '8000')
    
        if imsi_prefix == None:
            self.template['imsi'] = \
                str(input('Enter IMSI prefix, ' \
                          'format <prefix><paddig><id> (default: 25080): ') or "25080")
        else:
            self.template['imsi'] = imsi_prefix

        return self

    def generate(self):
        
        print(f'\n{self.name} records generator:')
        start = int(input("Enter initial record <id> (default: 1): ").strip() or 1)
        count = int(input("Enter number of records (default: 1): ").strip() or 1)

        for id in range(start, start + count):
            self.create(id)


    def getById(self, id):
        return requests.get(str(base_url) + '/auc/' + str(id)).json() or {}

    def getByImsi(self, imsi):
        return requests.get(str(base_url) + '/auc/imsi/' + str(imsi)).json() or {}

    def create(self, id):

        data = self.template.copy()
        data['auc_id'] = id
        data['imsi'] = self.template['imsi'] + str(id).zfill(15 - len(self.template['imsi']))
        data['iccid'] = str(id)

        auc_id = self.getById(id).get('auc_id')
        if auc_id:
            log.info('{} Record already exists: id={}'.format(
                self.name, auc_id))
            return auc_id
      
        auc_id = self.getByImsi(data['imsi']).get('auc_id')
        if auc_id:
            log.info('{} Record already exists: imsi={} '.format(
                self.name, data['imsi']))
            return auc_id

        data['ki'] = self.template['ki'] + str(id).zfill(32 - len(self.template['ki']))
        data['opc'] = self.template['opc'] + str(id).zfill(32 - len(self.template['opc']))
        data['amf'] = self.template['amf']
        data['sqn'] = id

        headers = {"Content-Type": "application/json"}
        r = requests.put(str(base_url) + '/auc/', data=json.dumps(data), headers=headers)
        if r.json() != None:
            auc_id = r.json().get('auc_id')
            log.info("{} record created: id={}, imsi={}".format(
                self.name, auc_id, str(r.json()["imsi"])
            ))
        else:
            log.error("{} Failed to create record, imsi= {} ".format(
                self.name, data["imsi"]
            ))

        return auc_id

class APN: # Access Point Name (APN)

    name = 'APN'
    template = {}

    def createTemplate(self):

        self.template = {
            "apn": "APN",
            "ip_version": 0,
            "pgw_address": "127.0.0.1",
            "sgw_address": "127.0.0.1",
            "charging_characteristics": "0800",
            "apn_ambr_dl": 99999,
            "apn_ambr_ul": 99999,
            "qci": 9,
            "arp_priority": 4,
            "arp_preemption_capability": False,
            "arp_preemption_vulnerability": True,
            "charging_rule_list": "",
            "nbiot": False,
            "nidd_scef_id": "NIDD_SCEF_ID",
            "nidd_scef_realm": "NIDD_SCEF_REALM",
            "nidd_mechanism": 0,
            "nidd_rds": 0,
            "nidd_preferred_data_mode": 0
        }

        print(f'\n{self.name} records template data:')

        self.template['apn'] = \
            str(input('Enter APN short name prefix, ' \
                      'format <prefix><id> (default: APN): ') or 'APN')
        self.template['apn_ambr_dl'] = \
            int(input('Enter Downlink Maximum Bit Rate ' \
                      '(default: 99999): ').strip() or 99999)
        self.template['apn_ambr_ul'] = \
            int(input('Enter Uplink Maximum Bit Rate ' \
                      '(default: 99999): ').strip() or 99999)

        return self

    def generate(self):
        
        print(f'\n{self.name} records generator:')
        start = int(input("Enter initial record <id> (default: 1): ").strip() or 1)
        count = int(input("Enter number of records (default: 1): ").strip() or 1)

        for id in range(start, start + count):
            self.create(id)

    def getById(self, id):
        return requests.get(str(base_url) + '/apn/' + str(id)).json() or {}

    def create(self, id):

        data = self.template.copy()
        data['apn_id'] = id

        apn_id = self.getById(str(id)).get('apn_id')
        if apn_id != None:
            log.info('{} Record already exists: id={}'.format(self.name, apn_id))
            return apn_id

        data['apn'] += '_' + str(id)

        headers = {"Content-Type": "application/json"}
        r = requests.put(str(base_url) + '/apn/', data=json.dumps(data), headers=headers)
        if r.json() != None:
            apn_id = r.json().get('apn_id')
            log.info("{} record created: id={}".format(self.name, apn_id))
        else:
            log.error("{} Failed to create record, id={} ".format(self.name, id))

        return apn_id

class SUBSCRIBER: # Subscriber entry

    name = 'SUBSCRIBER'
    template = {}

    auc = AUC()
    apn = APN()

    def createTemplate(self, imsi_prefix = None):

        self.template = {
            "enabled": True,
            "apn_list": "",
            "ue_ambr_dl": 99999,
            "ue_ambr_ul": 99999,
            "nam": 0,
            "roaming_enabled": False,
            "roaming_rule_list": "",
            "subscribed_rau_tau_timer": 300,
            "serving_mme": "SERVING_MME",
            "serving_mme_realm": "SERVING_MME_REALM",
            "serving_mme_peer": "SERVING_MME_PEER"
        }

        print(f'\n{self.name} records template data:')

        if imsi_prefix == None:
            self.template['imsi'] = \
                str(input('Enter IMSI prefix, ' \
                          'format <prefix><paddig><id> (default: 25080): ') or "25080")
        else:
            self.template['imsi'] = imsi_prefix

        self.apn.createTemplate()
        self.auc.createTemplate(self.template['imsi'])

        return self

    def generate(self):
        print(f'\n{self.name} records generator:')
        start = int(input("Enter initial record <id> (default: 1): ").strip() or 1)
        count = int(input("Enter number of records (default: 1): ").strip() or 1)

        for id in range(start, start + count):
            self.create(id)

    def getById(self, id):
        return requests.get(str(base_url) + '/subscriber/' + str(id)).json() or {}

    def getByImsi(self, imsi):
        return requests.get(str(base_url) + '/subscriber/imsi/' + str(imsi)).json() or {}

    def create(self, id):

        data = self.template.copy()
        data['subscriber_id'] = id
        data['imsi'] = self.template['imsi'] + str(id).zfill(15 - len(self.template['imsi']))
        data['msisdn'] = data['imsi']

        subscriber_id = self.getById(id).get('subscriber_id')
        if subscriber_id:
            log.info('{} Record already exists: id={}'.format(
                self.name, subscriber_id))
            return subscriber_id

        subscriber_id = self.getByImsi(data['imsi']).get('subscriber_id')
        if subscriber_id:
            log.info('{} Record already exists: imsi={} '.format(
                self.name, data['imsi']))
            return subscriber_id

        apn_id = self.apn.create(id)
        if apn_id == None:
            return None

        auc_id = self.auc.create(id)
        if auc_id == None:
            return None

        data['auc_id'] = auc_id
        data['default_apn'] = apn_id
        data['apn_list'] = str(apn_id)           

        headers = {"Content-Type": "application/json"}
        r = requests.put(str(base_url) + '/subscriber/', data=json.dumps(data), headers=headers)
        if r.json() != None:
            subscriber_id = r.json().get('subscriber_id')
            log.info("{} record created: id={}, imsi={}".format(
                self.name, subscriber_id, data['imsi']))
        else:
            log.error("Failed to create record, imsi={}".format(self.name, data['imsi']))

        return subscriber_id


print("Generate Database records")
print("-------------------------")

while True:

    client = None
    request = input("\nEnter record type: ")

    if request in ("1", "IMS_SUBSCRIBER"):
        client = IMS_SUBSCRIBER()
    elif request in ("2", "AUC"):
        client = AUC()
    elif request in ("3", "APN"):
        client = APN()
    elif request in ("4", "AUC+APN+SUBSCRIBER"):
        client = SUBSCRIBER()
    else:
        print("Invalid input, valid entries are:")
        for keys in supported_calls:
            print(f"{keys}")
    
    if client != None:
        client.createTemplate()
        client.generate()

