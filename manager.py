import glob
import json
import operator
import os

from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client, Settings
from zeep.cache import SqliteCache
from zeep.helpers import serialize_object
from zeep.transports import Transport

import utils
from shared_vars import (DEFAULT_B2B_VERSION, DEFAULT_DATASET, WSDL_PROXY,
						 WSLD_PREOPS_MAIN, get_dataset)

# NOTE : plutôt envoyer un **kwargs en param des méthodes. Puis, itérer sur les kwargs.
# si présence de clé dans _default_params_for_queries et pas de val...

class Manager():

	def __init__(
		self, 
		version=DEFAULT_B2B_VERSION, 
		service_group="FlightServices", 
		dataset=DEFAULT_DATASET,
		how_to_auth='proxy',
		*args, **kwargs
		):
		
		self.base_url = ''
		self.service_group = service_group
		self.available_services = []
		self.available_operations = {}		
		self._default_params_for_queries = {
			'dataset':                  get_dataset(dataset),
			'trafficType':              'LOAD',
			'includeProposalFlights':   True, 
			'includeForecastFlights':   True,
			'sendTime':                 utils.sendTime(),
		}
		self.session = Session()

		# ------------- certificat ou proxy ? ------------- #
		if how_to_auth == 'cert': 
			# Si authentification par certificat			
			self.session.cert = (glob.glob("cert/crt.pem")[0], glob.glob("cert/key.pem")[0])
			self.base_url = WSLD_PREOPS_MAIN
		elif how_to_auth == 'proxy': 
			# Si authentification via proxy (défaut)
			NM_B2B_API_KEY_ID = os.environ.get('NM_B2B_API_KEY_ID')  # default is None
			NM_B2B_API_SECRET = os.environ.get('NM_B2B_API_SECRET')  # default is None
			if not NM_B2B_API_KEY_ID or not NM_B2B_API_SECRET:
				print(f"Impossible de définir un couple clé/pass pour le proxy b2b.\
					Vérifiez que NM_B2B_API_KEY_ID et NM_B2B_API_SECRET sont bien définis dans votre environnement.")
				exit(1)
			self.base_url = WSDL_PROXY
			self.session.auth = HTTPBasicAuth(NM_B2B_API_KEY_ID, NM_B2B_API_SECRET)
		else:
			print("Le mode d'authentification que vous avez spécifié n'existe pas (pour l'instant : 'cert' ou 'proxy').")
			exit(1)
		
		self.wsdl = self.base_url + service_group + "_PREOPS_" + version + ".wsdl"
		self.cache = SqliteCache(path='./data/sqlite.db')
		self.transport = Transport(session=self.session, cache=self.cache)        
		self.conf = {
			'wsdl':         self.wsdl,
			'transport':    self.transport
		}		
		self.tmp_data = None
	

	# -----------------------------------------------------------------------------------------
	def get_wsdl_file(self):
		
	
	# -----------------------------------------------------------------------------------------
	def set_available_services(self):
		self.available_services = []
		client = Client(**self.conf)
		for service in client.wsdl.services.values():
			self.available_services.append(service.__str__().split()[1])

	def show_available_services(self):
		if not self.available_services:
			self.set_available_services()
		print("Les services disponibles via {} sont : ".format(self.service_group)),
		for service in self.available_services:
			print('  * ', service)
	
	# -----------------------------------------------------------------------------------------
	def set_operations_of_service(self, service_name):
		if not self.available_services:
			self.set_available_services()
		if not service_name in self.available_services:
			raise Exception(f"Le service {service_name} n'est pas disponible.")
		client = Client(**self.conf, service_name=service_name)
		operations = [op for op in client.service.__dir__() if not op.startswith('__')]
		self.available_operations[service_name] = operations
	
	def show_operations_of_service(self, service_name):
		if not service_name in self.available_operations:
			self.set_operations_of_service(service_name=service_name)
		print(f"Les opérations disponibles pour {service_name} sont : ")
		for operation in self.available_operations[service_name]:
			print('  * ', operation)
	
	# -----------------------------------------------------------------------------------------
	def convert_data_to_json(self, obj):
		return serialize_object(self.tmp_data)

	# -----------------------------------------------------------------------------------------
	def queryFlightsByAirspace(
		self, 
		airspace, 
		startTime, 
		endTime, 
		requestedFlightFields=  [],
		dataset=                None,
		trafficType=            None,
		includeProposalFlights= None,
		includeForecastFlights= None,
		sendTime=               None,
		):

		dataset = self._default_params_for_queries['dataset'] if not dataset else dataset
		trafficType = self._default_params_for_queries['trafficType'] if not trafficType else trafficType
		includeProposalFlights = self._default_params_for_queries['includeProposalFlights'] if not includeProposalFlights else includeProposalFlights
		includeForecastFlights = self._default_params_for_queries['includeForecastFlights'] if not includeForecastFlights else includeForecastFlights
		sendTime = self._default_params_for_queries['sendTime'] if not sendTime else sendTime
		trafficWindow = {'wef': startTime, 'unt': endTime}

		client = Client(**self.conf, service_name='FlightManagementService')
		self.tmp_data = client.service.queryFlightsByAirspace(
			airspace=airspace, 
			dataset=dataset, trafficType=trafficType,
			includeProposalFlights=includeProposalFlights, includeForecastFlights=includeForecastFlights, 
			trafficWindow=trafficWindow, requestedFlightFields=requestedFlightFields, sendTime=sendTime)
		return self.tmp_data
	
	def queryFlightsByAerodrome(
		self, 
		aerodrome,
		aerodromeRole,
		startTime, 
		endTime, 
		requestedFlightFields=  [],
		dataset=                None,
		trafficType=            None,
		includeProposalFlights= None,
		includeForecastFlights= None,
		sendTime=               None,
		):

		dataset = self._default_params_for_queries['dataset'] if not dataset else dataset
		trafficType = self._default_params_for_queries['trafficType'] if not trafficType else trafficType
		includeProposalFlights = self._default_params_for_queries['includeProposalFlights'] if not includeProposalFlights else includeProposalFlights
		includeForecastFlights = self._default_params_for_queries['includeForecastFlights'] if not includeForecastFlights else includeForecastFlights
		sendTime = self._default_params_for_queries['sendTime'] if not sendTime else sendTime
		trafficWindow = {'wef': startTime, 'unt': endTime}

		client = Client(**self.conf, service_name='FlightManagementService')
		self.tmp_data = client.service.queryFlightsByAerodrome(
			aerodrome=aerodrome, aerodromeRole=aerodromeRole, 
			dataset=dataset, trafficType=trafficType,
			includeProposalFlights=includeProposalFlights, includeForecastFlights=includeForecastFlights, 
			trafficWindow=trafficWindow, requestedFlightFields=requestedFlightFields, sendTime=sendTime)
		return self.tmp_data
	
	def queryFlightsByTrafficVolume(
		self, 
		trafficVolume, 
		startTime, 
		endTime, 
		requestedFlightFields=  [],
		dataset=                None,
		trafficType=            None,
		includeProposalFlights= None,
		includeForecastFlights= None,
		sendTime=               None,
		**kwargs
		):

		dataset = self._default_params_for_queries['dataset'] if not dataset else dataset
		trafficType = self._default_params_for_queries['trafficType'] if not trafficType else trafficType
		includeProposalFlights = self._default_params_for_queries['includeProposalFlights'] if not includeProposalFlights else includeProposalFlights
		includeForecastFlights = self._default_params_for_queries['includeForecastFlights'] if not includeForecastFlights else includeForecastFlights
		sendTime = self._default_params_for_queries['sendTime'] if not sendTime else sendTime
		trafficWindow = {'wef': startTime, 'unt': endTime}

		client = Client(**self.conf, service_name='FlightManagementService')
		self.tmp_data = client.service.queryFlightsByTrafficVolume(
			trafficVolume=trafficVolume, 
			dataset=dataset, trafficType=trafficType,
			includeProposalFlights=includeProposalFlights, includeForecastFlights=includeForecastFlights, 
			trafficWindow=trafficWindow, requestedFlightFields=requestedFlightFields, sendTime=sendTime,
			**kwargs)
		return self.tmp_data
