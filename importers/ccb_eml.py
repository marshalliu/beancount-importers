
"""Importer for 建设银行 (China Construction Bank)
"""
__copyright__ = "Copyright (C) 2023  Marshal Liu"
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


class CcbEmlImporter(importer.ImporterProtocol):
    """An importer for CCB .eml files."""

    def __init__(self, account='Liabilities:Life:CreditCard:CCB', expenseDict: Dict=None):
        # print(file_type)
        self.account_name: str = account
        self.default_set = frozenset({"CCB"})
        self.expenseDict = expenseDict
        self.currency = "CNY"
        pass

    def identify(self, file):
        # Match if the filename is as downloaded and the header has the unique
        # fields combination we're looking for.
        return (
            re.match(r"中国建设银行信用卡电子账单", path.basename(file.name)) and
            re.search(r"eml", path.basename(file.name))
        )

    def file_name(self, file):
        return 'ccb.{}'.format(path.basename(file.name))

    def file_account(self, _):
        return self.account_name

    def extract(self, file, existing_entries=None):
        # Open the eml file and create directives.
        entries = []
        index = 0
        with open(file.name, 'rb') as f:
            eml = parser.BytesParser(policy=policy.default).parse(fp=f)
            b = eml.get_payload()[0].get_payload(decode=True).decode("UTF8")
            d = BeautifulSoup(b, "lxml")
            date_range = d.findAll(text=re.compile(
                '\d{4}\/\d{1,2}\/\d{1,2}-\d{4}\/\d{1,2}\/\d{1,2}'))[0]
            transaction_date = dateparse(
                date_range.split('-')[1].split('(')[0]).date()
            
            balance = d.find('td', width="62%").find_all("tr")[3].find_all("td")[1].text
            txn_balance = data.Balance(
                account=self.account_name,
                amount=-Amount(D(balance), 'CNY'),
                meta=data.new_metadata(".", 1000),
                tolerance=None,
                diff_amount=None,
                date=transaction_date + timedelta(days=1)
            )
            entries.append(txn_balance)
            logging.warning("balance=%s", balance)

            # 第1个875宽度的table为账单总金额 
            #balance = d.find('table', width="875").find_all("tr")[1].find_all("td")[2].text
            #txn_balance = data.Balance(
            #    account=self.account_name,
            #    amount=-Amount(D(balance), 'CNY'),
            #    meta=data.new_metadata(".", 1000),
            #    tolerance=None,
            #    diff_amount=None,
            #    date=transaction_date + timedelta(days=1)
            #)
            #entries.append(txn_balance)

            # 第2个875宽度的table为账单明细列表 
            lists = d.find_all('table', width="875")[1]
            trs = lists.find_all('tr')
            for tr in trs:
                cols=tr.find_all('td')
                cols=[x.text.strip() for x in cols]
                trade_date = cols[0]
                try:
                    dt = datetime.strptime(trade_date, "%Y-%m-%d")
                except:
                    continue

                flag = flags.FLAG_WARNING
                payee = cols[3]
                price = cols[7]
                currency = cols[6]
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
                        "source": "建设银行",
                        "cardNo": cols[2],
                        "tradeCurrency": cols[4],
                        "tradeAmt": cols[5]
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
