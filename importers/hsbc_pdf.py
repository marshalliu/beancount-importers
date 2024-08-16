
"""Importer for 汇丰银行 (Hongkong and Shanghai Banking)
"""
__copyright__ = "Copyright (C) 2924 Marshal Liu"
__license__ = "GNU GPLv2"

import logging
import re
import datetime
from os import path
from typing import Dict

from datetime import datetime, timedelta
from beancount.core import data, flags
from beancount.core.amount import Amount
from beancount.core.number import D
from beancount.ingest import importer
from dateutil.parser import parse as dateparse
# from smart_importer import PredictPayees, PredictPostings
import camelot
import pandas as pd

class HsbcPDFImporter(importer.ImporterProtocol):
    """An importer for hsbc .pdf files."""

    def __init__(self, account='Liabilities:Life:CreditCard:HSBC', expenseDict: Dict=None):
        # print(file_type)
        self.account_name: str = account
        self.default_set = frozenset({"HSBC"})
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
        dfas = []
        index = 0
        tables = camelot.read_pdf(
            file.name, 
            flavor='stream', pages="1-end", 
            split_text=True, strip_text='\n'
        )

        for t in tables[1:tables.n-3]:
            dfas.append(t.df)


        dfa=pd.concat([pd.DataFrame(el) for el in dfas], ignore_index=True)

        # Rename column as first row 
        dfa.columns = dfa.iloc[1]

        # Remove first two row and last row
        dfa = dfa[2:]
        dfa = dfa[:len(dfa.index)-1]
        dfa.reset_index(drop=True)

        print(dfa.to_csv)

        for index, df in enumerate(dfa.values):
            if df[0][:2] != "卡号" and df[0]!="交易日期" and df[0]!="" :
                flag = flags.FLAG_WARNING
                payee = df[2]
                price = re.sub('[^0-9.]+', '', df[3])
                #price = df[3].lstrip("￥")
                process_date = datetime.strptime("2024/"+df[0], "%Y/%m/%d")
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
                        "settleDate": "2024/"+df[0],
                        "source": "汇丰银行信用卡",
                        "tradeCurrency": currency,
                        "tradeAmt": price
                        }
                )
        
                txn = data.Transaction(
                    meta,
                    process_date.date(),
                    flag,
                    payee,
                    "",
                    self.default_set,
                    data.EMPTY_SET,
                    postings,
                )

                entries.append(txn)        

        return entries

# @PredictPostings()
# @PredictPayees()
# class SmartWechatImporter(WechatImporter):
#     pass

        

