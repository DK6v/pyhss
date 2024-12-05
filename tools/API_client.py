#!/usr/bin/env python3

import sys
import logging
import requests
import json

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log= logging.getLogger("API:G")

base_url = 'http://localhost:5000'

supported_calls = ["IMS"]

class IMS:
    def generate(self):

        prefix = str(input("Enter IMSI prefix (default: 25080):\t") or "25080")
        start = int(input("Enter MSISDN start (default: 1):\t").strip() or 1)
        count = int(input("Enter number of records (default: 1):\t").strip() or 1)

        template_data = {}
        template_data['scscf'] = \
            str(input("Template data - SCSCF (default: TEMPLATE_SCSCF_DOMAIN):\t").strip() or
                "TEMPLATE_SCSCF_DOMAIN")

        for imsi in range(start, start + count):
            imsi = prefix + str(imsi).zfill(15 - len(prefix))
            
            template_data["imsi"] = imsi
            template_data["msisdn"] = imsi
            template_data["msisdn_list"] = imsi
            
            self.create(template_data)


    def create(self, data):
        headers = {"Content-Type": "application/json"}
        r = requests.put(str(base_url) + '/ims_subscriber/', data=json.dumps(data), headers=headers)
        if r.status_code == 200:
            if r.json() != None:
                log.info("IMS record created: imsi={}, ims_subscriber_id={}" \
                .format(str(r.json()["imsi"]), str(r.json()["ims_subscriber_id"])))
            else:
                log.info("IMS Record already exists or invalid, IMSI: {} ".format(data["imsi"]))
        else:
            log.error("Failed to create record, IMSI: {} ".format(data["imsi"]))
            

print("Generate Database records")
print("-------------------------")

while True:
    request = input("Enter record type:\t")

    if request == "IMS":
        IMS().generate()

    else:
        print("Invalid input, valid entries are:")
        for keys in supported_calls:
            print(keys)
