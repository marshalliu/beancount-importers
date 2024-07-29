
"""Importer for 汇丰银行 (Hongkong and Shanghai Banking)
"""
__copyright__ = "Copyright (C) 2924 Marshal Liu"
__license__ = "GNU GPLv2"


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
import camelot
import pandas as pd

class HsbcPDFImporter(importer.ImporterProtocol):
    """An importer for CCB .eml files."""

    def __init__(self, account='Liabilities:Life:CreditCard:HSBC', expenseDict: Dict=None):
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
            re.match(r"0001-0000850556", path.basename(file.name)) and
            re.search(r"pdf", path.basename(file.name))
        )

    def file_name(self, file):
        return 'hsbc.{}'.format(path.basename(file.name))

    def file_account(self, _):
        return self.account_name

    def extract(self, file, existing_entries=None):
        # Open the eml file and create directives.
        entries = []
        index = 0
        tables = camelot.read_pdf(
            file.name, 
            flavor='stream', pages="1-end", table_areas=['50,696,465,96'],
            split_text=True, strip_text='\n'
        )

        dfa = pd.concat([t.df.rename(columns=t.df.iloc[0]).drop([0])
                        for t in tables[1:3]], ignore_index=True)
        print(dfa)
#       
#
#       dfa["交易日期"] = pd.to_datetime(dfa["交易日期"]).dt.date
#       entries = [
#           data.Transaction(
#               meta=data.new_metadata(file.name, lineno=index),
#               date=tdate,
#               flag=self.FLAG,
#               payee=payee,
#               narration=narration,
#               tags=data.EMPTY_SET,
#               links=data.EMPTY_SET,
#               postings=[
#                   data.Posting(
#                       self.account_name,
#                       Amount(D(amount), self.currency),
#                       None, None, None, None
#                   )
#               ]
#           )
#           for index, tdate, payee, narration, amount in
#           zip(dfa.index, dfa["交易日期"], dfa["交易说明"], "", dfa["入账币种/金额"].lstrip("￥"))
#       ]
        entries.append(
           data.Balance(
               account=self.account_name,
               amount=Amount(
                   D(dfa.iloc[-1]["账户余额"]), self.currency),
               date=dfa.iloc[-1]["交易时间"] + timedelta(days=1),
               tolerance=None,
               diff_amount=None,
               meta=data.new_metadata(file.name, lineno=9999),
           )
        )
        return entries

#            txn_balance = data.Balance(
#                account=self.account_name,
#                amount=-Amount(D(balance), 'CNY'),
#                meta=data.new_metadata(".", 1000),
#                tolerance=None,
#                diff_amount=None,
#                date=transaction_date + timedelta(days=1)
#            )
#            entries.append(txn_balance)
#
#            # 第2个875宽度的table为账单明细列表 
#            lists = d.find_all('table', width="875")[1]
#            trs = lists.find_all('tr')
#            for tr in trs:
#                cols=tr.find_all('td')
#                cols=[x.text.strip() for x in cols]
#                trade_date = cols[0]
#                try:
#                    dt = datetime.strptime(trade_date, "%Y-%m-%d")
#                except:
#                    continue
#
#                flag = flags.FLAG_WARNING
#                payee = cols[3]
#                price = cols[7]
#                currency = cols[6]
#                amount = -Amount(D(price), currency)
#
#                account_2 = None
#                for asset_k, asset_v in self.expenseDict.items():
#                    if asset_k.find(",") > -1:
#                        for asset_k1 in asset_k.split(","):
#                            if asset_k1 in payee:
#                                account_2 = asset_v
#                                flag = flags.FLAG_OKAY
#                    elif asset_k in payee:
#                        account_2 = asset_v
#                        flag = flags.FLAG_OKAY
#
#                if (account_2 != None):
#                    postings = [data.Posting(self.account_name, amount, None, None, None, None),
#                                data.Posting(account_2, -amount, None, None, None, None)]
#                else: 
#                    postings = [data.Posting(self.account_name, amount, None, None, None, None)]
#
#                meta = data.new_metadata(
#                    file.name, index, kvlist={
#                        "method": payee,
#                        "settleDate": cols[1],
#                        "source": "建设银行",
#                        "cardNo": cols[2],
#                        "tradeCurrency": cols[4],
#                        "tradeAmt": cols[5]
#                        }
#                )
#                #logging.warn("%s:%s:%s", payee, narration, account_2)
#
#                txn = data.Transaction(
#                    meta,
#                    dt.date(),
#                    flag,
#                    payee,
#                    "",
#                    self.default_set,
#                    data.EMPTY_SET,
#                    postings,
#                )
#
#                entries.append(txn)
#        # Insert a final balance check.
#
#        return entries


# @PredictPostings()
# @PredictPayees()
# class SmartWechatImporter(WechatImporter):
#     pass

        

