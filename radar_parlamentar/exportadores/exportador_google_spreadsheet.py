#!/usr/bin/python

try:
	import xml.etree.ElementTree as etree
except ImportError:
	from elementtree import ElementTree

import gdata.spreadsheet.service
import gdata.service
import gdata.spreadsheet
import getopt
import sys
import datetime
#import string

class ExportadorGoogleSpreadsheet:

	# Cores para imprimir no console :)
	WARNING 	= '\033[93m'
	OKBLUE 		= '\033[94m'
	OKGREEN 	= '\033[92m'
	FAIL 		= '\033[91m'
	ENDC 		= '\033[0m'

	# Variaveis private
	__gd_client 	= None
	__curr_key 		= None
	__wksht_id		= None
	__firt_date		= None
	__xml_tree		= None
	__root_tree		= None

	# Inicia a classe com os atributos default: senha, email
	def __init__(self, email, senha):
		self.gd_client = gdata.spreadsheet.service.SpreadsheetsService()
		self.gd_client.email = email
		self.gd_client.password = senha
		self.gd_client.source = 'Exportador para criar tabela timeline google spreadsheet'
		self.gd_client.ProgrammaticLogin()
		self.curr_key = ''
		self.wksht_id = ''
		self.xml_tree = etree.parse('dados/biografia/BIOGRAFIA 2901 - 7000.xml')
		self.root_tree = self.xml_tree.getroot()

	# Procura pelo documento "timeline_deputadas" dentro da conta inserida
	# Sempre captura a primeira ocorrencia do nome
	def __get_spreadsheet(self):
		print 'Searching for your spreadsheet...'
		feed = self.gd_client.GetSpreadsheetsFeed()
		for i, entry in enumerate(feed.entry):
			if entry.title.text == "timeline_deputadas":
				id_part = feed.entry[i].id.text.split('/')
				self.curr_key = id_part[len(id_part) - 1]
				print self.OKGREEN + 'Spreadsheet %s found!' % entry.title.text + self.ENDC

	# Procura pelo worksheet "timeline" do spreadsheet
	def __get_worksheet(self):
		print 'Searching for your worksheet...'
		feed = self.gd_client.GetWorksheetsFeed(self.curr_key)
		for i, entry in enumerate(feed.entry):
			if entry.title.text == "timeline":
				id_part = feed.entry[i].id.text.split('/')
				self.wksht_id = id_part[len(id_part) - 1]
				print self.OKGREEN + 'Worksheet %s found!' % entry.title.text + self.ENDC

	# Configura spreadsheet inicial para timeline
	def __set_worksheet_timeline(self):
		print 'Setting up spreadsheet for timeline'
		col_label = ["startdate", "enddate", "headline",
		"text", "media", "mediacredit", "mediacaption",
		"mediathumbnail", "type", "tag"]
		for i in range(1,11): # Percorre a lista col_label
			self.__update_cell(1, i, col_label[i-1])
		print 'Finish setting up!'

	# Update celula especifica
	def __update_cell(self, row, col, inputValue):
		entry = self.gd_client.UpdateCell(row=row, col=col, inputValue=inputValue, key=self.curr_key, wksht_id=self.wksht_id)
		print self.WARNING + '::UPDATING:: Row - %s and Column - %s' % (row, col) + self.ENDC
		if isinstance(entry, gdata.spreadsheet.SpreadsheetsCell):
			print self.OKBLUE + '::UPDATE:: Value - %s' % inputValue + self.ENDC
		else:
			print self.FAIL + '::FAIL:: Value - %s' % inputValue + self.ENDC

	# Adiciona em cada linha as biografias
	def __set_biography(self):
		try:
			for data_record in self.root_tree.findall('DATA_RECORD'):
				if data_record.find('INDSEXO').text == "F":
					mandato 			= data_record.find('MANDATOSCD').text
					nome_parlamentar	= data_record.find('TXTNOME').text
					sig_partido			= data_record.find('SIGPARTIDO').text

					legislatura	= data_record.find('LEGISLATURAS').text
					dates 		= self.__split_date(legislatura)
					start_date 	= '1/1/' + dates[0]
					end_date	= '1/1/' + dates[1]

					row_data	= 'startdate='+start_date

					self.__insert_row(row_data)

		except AttributeError:
			print self.WARNING + 'ID ' + data_record.find('IDECADASTRO').text + ' - Doent have INDSEXO! Moving on...' + self.ENDC


	def __insert_row(self, row_data):
	    entry = self.gd_client.InsertRow(self.__dictionary_maker(row_data),
	    	self.curr_key, self.wksht_id)
	    if isinstance(entry, gdata.spreadsheet.SpreadsheetsList):
	    	print 'Inserted!'

	# Separa os periodos das legislaturas
	# Atualmente apenas pega a primeira legislatura
	def __split_date(self, date):
		date = date.replace(" ","")
		if 'e' in date:
			date = date.split('e')
		elif ',' in date:
			date = date.split(',')

		if date is not list:
			dates = date.split('-')
		else:
			dates = date[0].split('-')

		return dates

	def __dictionary_maker(self,row_data):
		dict = {}
		for param in row_data.split():
			temp = param.split('=')
			dict[temp[0]] = temp[1]
		return dict

	# Metodo responsavel pela sequencia de execucao da classe
	def run(self):
		# self.__get_spreadsheet()
		# self.__get_worksheet()
		# self.__set_worksheet_timeline()
		self.__set_biography()

def main():
	# Linha de comando para o terminal
	try:
		opts, args = getopt.getopt(sys.argv[1:], "", ["user=", "pw="])
	except getopt.error, msg:
		print 'python spreadsheetExample.py --user [username] --pw [password] '
		sys.exit(2)

	user 		= ''
	password	= ''

	# Processando opcoes inseridas no console
	for opcao, atributo in opts:
		if opcao == "--user":
			user = atributo
		elif opcao == "--pw":
			password = atributo

	if user == '' or password == '':
		print 'python spreadsheetExample.py --user [username] --pw [password]'
		sys.exit(2)

	exportar = ExportadorGoogleSpreadsheet(user, password)
	exportar.run()

if __name__ == '__main__':
  main()