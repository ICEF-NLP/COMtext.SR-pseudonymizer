from comtext_sr_pseudonymizer.entities.adr import AddressAnonymizer
from comtext_sr_pseudonymizer.entities.com import CompanyAnonymizer
from comtext_sr_pseudonymizer.entities.contact import ContactAnonymizer
from comtext_sr_pseudonymizer.entities.court import CourtAnonymizer
from comtext_sr_pseudonymizer.entities.date import DateAnonymizer
from comtext_sr_pseudonymizer.entities.idcom import CompanyIDAnonymizer
from comtext_sr_pseudonymizer.entities.idper import PersonIDAnonymizer
from comtext_sr_pseudonymizer.entities.idtax import TaxIDAnonymizer
from comtext_sr_pseudonymizer.entities.money import MoneyAnonymizer
from comtext_sr_pseudonymizer.entities.numacc import AccountNumberAnonymizer
from comtext_sr_pseudonymizer.entities.numcar import CarNumberAnonymizer
from comtext_sr_pseudonymizer.entities.numdoc import DocumentNumberAnonymizer
from comtext_sr_pseudonymizer.entities.numplot import PlotNumberAnonymizer
from comtext_sr_pseudonymizer.entities.orgoth import OtherOrgAnonymizer
from comtext_sr_pseudonymizer.entities.per import PersonAnonymizer
from comtext_sr_pseudonymizer.entities.top import ToponymAnonymizer

ENTITY_MAP = {
    'ADR':     {'class': AddressAnonymizer,     'deps': ['dm', 'lex']},
    'COM':     {'class': CompanyAnonymizer,     'deps': ['dm']},
    'CONTACT': {'class': ContactAnonymizer,     'deps': ['dm']},
    'COURT':   {'class': CourtAnonymizer,       'deps': ['dm', 'lex']},
    'DATE':    {'class': DateAnonymizer,        'deps': []},
    'IDCOM':   {'class': CompanyIDAnonymizer,   'deps': ['dm']},
    'IDPER':   {'class': PersonIDAnonymizer,    'deps': []},
    'IDTAX':   {'class': TaxIDAnonymizer,       'deps': []},
    'MONEY':   {'class': MoneyAnonymizer,       'deps': []},
    'NUMACC':  {'class': AccountNumberAnonymizer, 'deps': []},
    'NUMCAR':  {'class': CarNumberAnonymizer,   'deps': []},
    'NUMDOC':  {'class': DocumentNumberAnonymizer, 'deps': []},
    'NUMPLOT': {'class': PlotNumberAnonymizer,  'deps': []},
    'ORGOTH':  {'class': OtherOrgAnonymizer,    'deps': ['dm']},
    'PER':     {'class': PersonAnonymizer,      'deps': ['dm', 'lex']},
    'TOP':     {'class': ToponymAnonymizer,     'deps': ['dm', 'lex']},
}