#!/usr/bin/env python3
import argparse, json, re
import pandas as pd

class NewSystemAccount():
    def __init__(self, old_system_data:dict):
        self._data = old_system_data
        self._type = self.__calc_type()

    @property
    def data(self):
        return self.get_formatted_data()

    @property
    def type(self):
        return self._type

    def __data_exists(self, key:str) -> bool:
        return key in self._data and self._data[key] != ''

    def __calc_type(self) -> str:
        if self.__data_exists('ibanNumber'):
            return 'iban'
        if self.__data_exists('sortCode') and self.__data_exists('accountNumber'):
            return 'gbDomestic'
        if self.__data_exists('unstructuredAccountNumber'):
            return 'unstructured'
        return 'invalid'

    def get_account_number(self) -> str:
        account_numbers = {
            'iban': self._data['ibanNumber'],
            'gbDomestic': self._data['sortCode'].replace('-', '') + self._data['accountNumber'],
            'unstructured': self._data['unstructuredAccountNumber']
        }
        return account_numbers.get(self.type, 'invalid')
    
    def get_bank_details(self) -> tuple[str, str]:
        bank_details = re.match('([^\s]+.*[^\s])\s*-\s*([A-Z]{2})', self._data['bankName'])
        bank_name, branch_country_code = bank_details[1], bank_details[2]
        return bank_name, branch_country_code

    def get_names(self, name1_length:int=30, name2_length:int=20) -> tuple[str, str]:
        concat_name = f'{self._data["name1"]}{self._data["name2"]}'
        name1, name2 = concat_name[:name1_length], concat_name[name1_length:name1_length+name2_length]
        return name1, name2

    def get_notes_as_ascii(self, max_length:int=30) -> str:
        notes_as_ascii = self._data['notes'].encode('ascii', 'ignore').decode('utf-8').strip()
        return re.sub(' +', ' ', notes_as_ascii)[:max_length]

    def get_formatted_data(self) -> dict[str, str]:
        bank_name, branch_country_code = self.get_bank_details()
        name1, name2 = self.get_names()
        return {
            'accountNumber': self.get_account_number(),
            'accountNumberType': self.type,
            'bankName': bank_name,
            'branchCountry': branch_country_code,
            'name1': name1,
            'name2': name2,
            'userComments': self.get_notes_as_ascii()
        }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', type=str, help='path/to/input_file.json')
    parser.add_argument('output_file', type=str, help='path/to/output_file.csv')
    args = parser.parse_args()

    with open(args.input_file, encoding='utf-8') as input_file:
        old_system_data = json.load(input_file)
        new_accounts = (NewSystemAccount(entry) for entry in old_system_data)
    
    new_account_data = []
    for account in new_accounts:
        if account.type == 'invalid': print(f'invalid account, skipping...')
        else: new_account_data.append(account.data)

    account_data_frame = pd.DataFrame(new_account_data)
    account_data_frame.to_csv(args.output_file, index=False)