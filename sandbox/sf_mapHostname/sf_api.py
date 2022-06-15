import logging
from pprint import pprint
from typing import List, Dict, Tuple

import flask
import simple_salesforce


from utils import format_sf_custom_field, simplify_ordered_dict, sort

log = logging.getLogger(__name__)


class SalesforceError(BaseException):
    pass


class SFAPI:
    def __init__(self, username: str, password: str, security_token):

        self.sf = simple_salesforce.Salesforce(username=username,
                                               password=password, security_token=security_token)
        pass

    @classmethod
    def from_app_config(cls, config: flask.Config):
        o = cls(
            instance=config['BBUI_SF_INSTANCE'],
            username=config['BBUI_SF_USERNAME'],
            password=config['BBUI_SF_PASSWORD'],
            security_token=config['BBUI_SF_TOKEN']
        )
        return o

    def quick_search(self):
        query_response = self.sf.quick_search('011226')
        print(query_response)

    def circuit_query(self):
        query = ''' 
        SELECT Id, Customer_Circuit_ID__c, Carrier_Circuit_1__c FROM Circuit__c
    
        WHERE Carrier_Circuit_1__c.name != null
        LIMIT 10
        '''

        query_response = self.sf.query_all(query)
        # query_response = sf.bulk.Circuit__c.query('SELECT Id, Customer_Circuit_ID__c FROM Circuit__c LIMIT 10')

        pprint(query_response)

    def get_all_tid_circuits(self) -> "List[Circuit]":

        tid_filter = ' OR '.join(f'{tid} != null' for tid in soql_filters.tid_fields)

        slot_filter = ' OR '.join(f'{slot} != null' for slot in soql_filters.slot_fields)

        query_text = f'SELECT Id FROM Circuit__c WHERE ({tid_filter}) OR ({slot_filter})'

        query_text = query_text.replace('TID_2__c', 'T__c')

        query_results = self.sf.query_all(query_text)['records']
        query_results = simplify_ordered_dict(query_results)

        return [Circuit(Id=item['Id']) for item in query_results]

    def get_all_records_tid_data(self) -> List[Dict]:

        tid_filter = ' OR '.join(f'{tid} != null' for tid in soql_filters.tid_fields)

        slot_filter = ' OR '.join(f'{slot} != null' for slot in soql_filters.slot_fields)

        tid_select = ', '.join(soql_filters.tid_fields)
        slot_select = ', '.join(soql_filters.slot_fields)
        hostname_select = ', '.join(soql_filters.hostname_fields)
        interface_select = ', '.join(soql_filters.interface_fields)

        query_text = f'SELECT Id, Name, RecordTypeId, Customer_Circuit_ID__c, {tid_select}, {slot_select},' \
                     f' {hostname_select}, {interface_select} FROM Circuit__c WHERE ({tid_filter}) OR ({slot_filter}) '

        query_results = self.sf.query_all(query_text)['records']
        query_results = simplify_ordered_dict(query_results)
        return query_results

    def get_all_records_layout_data(self) -> List[Dict]:

        hn_filter = ' OR '.join(f'{hostname} != null' for hostname in soql_filters.hostname_fields)

        ifce_filter = ' OR '.join(f'{interface} != null' for interface in soql_filters.interface_fields)

        hostname_select = ', '.join(soql_filters.hostname_fields)
        interface_select = ', '.join(soql_filters.interface_fields)

        query_text = f'SELECT Id, Name, RecordTypeId, {hostname_select}, {interface_select} FROM Circuit__c WHERE ' \
                     f'({hn_filter}) OR ({ifce_filter})'

        query_results = self.sf.query_all(query_text)['records']
        query_results = simplify_ordered_dict(query_results)
        return query_results

    def get_record_layout_data(self, Id: str) -> Dict:
        def _get(Id):
            hostname_select = ', '.join(soql_filters.hostname_fields)
            interface_select = ', '.join(soql_filters.interface_fields)

            query_text = f'SELECT Id, {hostname_select}, {interface_select} FROM Circuit__c ' \
                         f'WHERE Id = \'{Id}\''

            query_results = self.sf.query_all(query_text)['records'][0]
            query_results = simplify_ordered_dict(query_results)
            results = simplify_layout_data(query_results)
            return results

        return _get(Id)

    def get_records_including_switch(self, switch_hostname: str) -> Dict:
        def _get(switch_hostname):
            hostname_select = ', '.join(soql_filters.hostname_fields)
            interface_select = ', '.join(soql_filters.interface_fields)

            hn_filter = ' OR '.join(f'{hostname} = \'{switch_hostname}\'' for hostname in soql_filters.hostname_fields)
            soql = SoqlFilter()
            query_text = f'SELECT Id, Name, Circuit_ID__c, Order_Status__c, {hostname_select}, {interface_select}, VLAN_IDs__c FROM Circuit__c ' \
                         f'WHERE ({hn_filter}) AND {soql.bad_status_filter}'

            query_results = self.sf.query_all(query_text)['records']
            query_results = simplify_ordered_dict(query_results)
            return query_results
            # return self.sf.query_all(query_text)

        return _get(switch_hostname)

    def get_all_records_vlan_data(self) -> List[Dict]:

        vlan_select = ', '.join(soql_filters.vlan_fields)
        # Can't filter on vlan_fields directly because 'VLAN_IDs__c' is a text area, and those can't be used in
        #   filters
        query_text = f'Select Id, Name, RecordTypeId, Circuit_ID__c, Order_Status__c, {vlan_select} FROM Circuit__c '

        query_results = self.sf.query_all(query_text)['records']

        query_results = [
            result for result in query_results
            if any(result.get(key) is not None for key in soql_filters.vlan_fields)
        ]

        # noinspection PyTypeChecker
        query_results = simplify_ordered_dict(query_results)
        return query_results

    def cached_all_records_vlan_data(self) -> Tuple[List[Dict], int]:
        f = self.get_all_records_vlan_data
        log.info(f'calling all records vlan data')
        if self.cache is None:
            return f()
        f = self.cache.timed_wrapper(f)
        rslt, cache_store_time = f()
        return rslt, cache_store_time


class Circuit:
    # noinspection PyPep8Naming,PyUnusedLocal
    def __init__(self, Id, sfapi: SFAPI, **kwargs):
        if Id is None:
            raise SalesforceError(f'Cannot have Salesforce Record ID of `None`')
        self.id = self.Id = Id
        self.sf = sfapi.sf
        self._data = None

    @property
    def data(self) -> Dict:
        if self._data is None:
            data = self.sf.Circuit__c.get(self.id)
            self._data = simplify_ordered_dict(data)
        return self._data

    @property
    def sfid(self) -> str:
        return self.data.get('Name')

    @property
    def cfn_cid(self) -> str:
        return self.data.get('Customer_Circuit_ID__c')

    @property
    @sort
    def carrier_circuit_sfids(self) -> List[str]:
        return [
            carrier_circuit.sfid
            for carrier_circuit in self.carrier_circuits
        ]

    @property
    def cc_entries(self) -> List[str]:
        return [
            self.data.get(f'CC{n}__c')
            for n in range(1, 9)
            if self.data.get(f'CC{n}__c')
        ]

    @property
    @sort
    def carrier_circuit_ids(self) -> List[str]:
        return [
            self.data.get(f'Carrier_Circuit_{n}__c')
            for n in range(1, 9)
        ]

    @property
    def carrier_circuits(self) -> List['Circuit']:
        return [
            Circuit(carrier_circuit_id)
            for carrier_circuit_id in self.carrier_circuit_ids
            if carrier_circuit_id is not None
        ]

    @property
    @sort
    def customer_circuit_sfids(self) -> List[str]:
        return [
            customer_circuit.sfid for customer_circuit in self.customer_circuits
        ]

    @property
    @sort
    def customer_circuit_ids(self) -> List[str]:
        field = "{Id}"

        circuit_filter = ' OR '.join(f'{cc} = {field}' for cc in soql_filters.carrier_circuit_fields)

        status_clause = soql_filters.bad_status_filter
        where_clause = f'({circuit_filter}) AND {status_clause}'

        query_text = f'SELECT Id FROM Circuit__c WHERE {where_clause}'
        query = simple_salesforce.format_soql(query_text, Id=self.Id)

        query_results = self.sf.query_all(query)['records']
        query_results = simplify_ordered_dict(query_results)

        return [row['Id'] for row in query_results]

    @property
    def customer_circuits(self) -> List['Circuit']:
        return [
            self.__class__(Id=Id) for Id in self.customer_circuit_ids
        ]

    @classmethod
    def from_sfid(cls, sfid: str, sfapi: SFAPI) -> 'Circuit':
        query = simple_salesforce.format_soql("SELECT Id, Name FROM Circuit__c where Name = {sfid}", sfid=sfid)
        query_results = sfapi.sf.query_all(query)
        if len(query_results['records']) != 1:
            # noinspection SpellCheckingInspection
            raise SalesforceError(f'Couldn\'t find exactly one response when looking for {sfid}.  '
                                  f'Got: {query_results=}')

        circuit_dict = query_results['records'][0]
        return cls(circuit_dict['Id'])

    def __getattr__(self, attr):
        data = self.data
        attr_names = format_sf_custom_field(attr, multiple=True)
        for name in attr_names:
            try:
                return data[name]
            except KeyError:
                pass

        raise AttributeError(f'{self.__class__.__name__!r} object has no attribute {attr!r}.  '
                             f'Also tried {attr_names!r}') from None

    def __repr__(self) -> str:
        cname = self.__class__.__name__
        keys = ['Id', 'sfid', 'cfn_cid', 'attention', 'order_status']
        # keys = ['Id']
        kv_pairs = [(key, getattr(self, key)) for key in keys]

        attr_string = ', '.join(f'{key}={value!r}' for key, value in kv_pairs)
        return f'{cname}({attr_string})'


class SoqlFilter:
    @property
    def tids(self) -> List[str]:
        rslt = [
            f'TID_{n}' for n in range(1, 13)
        ]
        rslt[1] = 'T'  # what should be 'TID_2__c' is 'T__c' in salesforce itself
        return rslt

    @property
    def tid_fields(self) -> List[str]:
        return [f'{tid}__c' for tid in self.tids]

    @property
    def slots(self) -> List[str]:
        return [
            f'Slot_Port_{n}' for n in range(1, 13)
        ]

    @property
    def slot_fields(self) -> List[str]:
        return [f'{slot}__c' for slot in self.slots]

    @property
    def hostnames(self) -> List[str]:
        return [
            f'Host_Name_{n}' for n in range(1, 11)
        ]

    @property
    def hostname_fields(self) -> List[str]:
        return [f'{hostname}__c' for hostname in self.hostnames]
    
    @property 
    def interfaces(self) -> List[str]:
        return[
            f'Interface_{n}' for n in range(1, 11)
        ]

    @property
    def interface_fields(self) -> List[str]:
        return [f'{interface}__c' for interface in self.interfaces]

    @property
    def bad_status(self) -> List[str]:
        return [
            'Canceled',
            'Disconnected',
            'Disconnected-Verify Billing'
        ]

    @property
    def bad_status_filter(self) -> str:
        status_text = ', '.join(f'\'{status}\'' for status in self.bad_status)
        return f'Order_Status__c Not In ({status_text})'

    @property
    def carrier_circuit_fields(self) -> List[str]:
        return [
            f'Carrier_Circuit_{n}__c' for n in range(1, 9)
        ]

    vlan_fields = [
        'VLAN_IDs__c',
        # 'VLAN_ID__c'
    ]

    filterable_vlan_fields = [
        'VLAN_ID__c'
    ]


soql_filters = SoqlFilter()

# noinspection SpellCheckingInspection
record_type_ids = {
            '01240000000URZWAA4': 'Cust',
            '01240000000URZgAAO': 'Carrier',
            '0121W000000UgcVQAS': 'CustXC',
            '01240000000URZbAAO': 'XC',
            '01240000000MJ5pAAG': 'BGP',
            None: 'Other'
        }


def get_circuit(sfid: str) -> Circuit:
    return Circuit.from_sfid(sfid=sfid)


def get_circuit_ids_with_carrier_circuits(carrier_sfids: List[str]) -> List[str]:
    carrier_circuits = [Circuit.from_sfid(sfid) for sfid in carrier_sfids]
    
    rslt = set()
    for carrier_circuit in carrier_circuits:
        _circuit_ids = carrier_circuit.customer_circuit_ids
        if not rslt:
            rslt.update(_circuit_ids)
        else:
            rslt.intersection_update(_circuit_ids)

    return list(rslt)


def get_circuits_with_carrier_circuits(carrier_sfids: List[str]) -> List[Circuit]:
    return [
        Circuit(Id=Id) for Id in get_circuit_ids_with_carrier_circuits(carrier_sfids)
    ]


def simplify_layout_data(record: Dict) -> List[Tuple]:
    rslt = {}
    for n in range(1, 11):
        hn = record[f'Host_Name_{n}__c']
        ifce = record[f'Interface_{n}__c']
        if any((hn, ifce)):
            rslt[hn] = ifce
    return rslt

sf = SFAPI(username="cfnengops@apcela.com", password="9c+;52gH@Sav:GgYF&cjH", security_token="g2VZM05jhUT7oBVThwpDpnIr")

