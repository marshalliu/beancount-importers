
"""Importer for 民生银行 (Commercial Merchandise Bank of China)
"""
__copyright__ = "Copyright (C) 2024  Marshal Liu"
__license__ = "GNU GPLv2"

import base64
import datetime
import logging
import re
from email import parser, policy
from os import path
from datetime import datetime, timedelta
from typing import Dict

from beancount.core import data, flags
from beancount.core.amount import Amount
from beancount.core.number import D
from beancount.ingest import importer
from bs4 import BeautifulSoup
from dateutil.parser import parse as dateparse
# from smart_importer import PredictPayees, PredictPostings


class CmbcEmlImporter(importer.ImporterProtocol):
    """An importer for CMBC .eml files."""

    def __init__(self, account='Liabilities:Life:CreditCard:CMBC', expenseDict: Dict=None):
        # print(file_type)
        self.account_name: str = account
        self.default_set = frozenset({"CMBC"})
        self.expenseDict = expenseDict
        self.currency = "CNY"
        pass

    def identify(self, file):
        # Match if the filename is as downloaded and the header has the unique
        # fields combination we're looking for.
        return (
            re.match(r"民生信用卡\d{4}年\d{2}月电子对账单", path.basename(file.name)) and
            re.search(r"eml", path.basename(file.name))
        )

    def file_name(self, file):
        return 'cmbc.{}'.format(path.basename(file.name))

    def file_account(self, _):
        return self.account_name

    def extract(self, file, existing_entries=None):
        # Open the eml file and create directives.
        entries = []
        index = 0
        with open(file.name, 'rb') as f:
            msg = parser.BytesParser(policy=policy.default).parse(fp=f)

            for part in msg.walk():
                if part.is_multipart():
                    continue
                
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" in content_disposition:
                    # Handle attachments
                    filename = part.get_filename()
                    # You can save the attachment or process it as needed
                else:
                    # Handle the content
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset()
                    if charset:
                        if charset == "gb2313" or charset == "gbk" :
                            charset = "gb18030"
                        payload = payload.decode(charset)
            #print(payload)
            

            d = BeautifulSoup(payload, "html.parser")
            #print(d.prettify())
            balance_date = d.findAll(text=re.compile(
                    '\d{4}\/\d{1,2}\/\d{1,2}'))[0]
            transaction_date = dateparse(balance_date).date()
            
            balance = d.find('div', attrs={'style': 'word-wrap: break-word;text-align:center;color:#ff0000;line-height:110%;valign:bottom;'}).text
            txn_balance = data.Balance(
                account=self.account_name,
                amount=-Amount(D(balance), 'CNY'),
                meta=data.new_metadata(".", 1000),
                tolerance=None,
                diff_amount=None,
                date=transaction_date + timedelta(days=1)
            )
            entries.append(txn_balance)

            # span id 为 loopBand3 账单明细列表 
            list = d.find('span', id="loopBand3")
            spans = list.find_all('span', id="fixBand9")
            
            process_year = str(datetime.now().year)

            for span in spans:
                cols=span.find_all('div')
                cols=[x.text.strip() for x in cols]

                trade_date = process_year+"/"+cols[0]
                try:
                    dt = datetime.strptime(trade_date, "%Y/%m/%d")
                except:
                    continue
                flag = flags.FLAG_WARNING
                payee = cols[2]
                price = cols[3]
                currency = 'CNY'
                amount = -Amount(D(price), currency)
                account_2 = None
                for asset_k, asset_v in self.expenseDict.items():
                    if asset_k.find(",") > -1:
                        for asset_k1 in asset_k.split(","):
                            if asset_k1 in payee:
                                account_2 = asset_v
                                flag = flags.FLAG_OKAY
                    elif asset_k in payee:
                        account_2 = asset_v
                        flag = flags.FLAG_OKAY
                if (account_2 != None):
                    postings = [data.Posting(self.account_name, amount, None, None, None, None),
                                data.Posting(account_2, -amount, None, None, None, None)]
                else: 
                    postings = [data.Posting(self.account_name, amount, None, None, None, None)]
                meta = data.new_metadata(
                    file.name, index, kvlist={
                        "method": payee,
                        "settleDate": cols[1],
                        "source": "民生银行",
                        "cardNo": cols[4],
                        "tradeCurrency": currency,
                        "tradeAmt": price
                        }
                )
                #logging.warn("%s:%s:%s", payee, narration, account_2)
                txn = data.Transaction(
                    meta,
                    dt.date(),
                    flag,
                    payee,
                    "",
                    self.default_set,
                    data.EMPTY_SET,
                    postings,
                )
                entries.append(txn)
        # Insert a final balance check.

        return entries


# @PredictPostings()
# @PredictPayees()
# class SmartWechatImporter(WechatImporter):
#     pass
