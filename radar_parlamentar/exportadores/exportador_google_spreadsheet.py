#!/usr/bin/python

try:
	from xml.etree import ElementTree
except ImportError:
	from elementtree import ElementTree

import gdata.spreadsheet.service
import gdata.service
import atom.service
import gdata.spreadsheet
import atom
import getopt
import sys
import string

class ExportadorGoogleSpreadsheet:

	WARNING 	= '\033[93m'
	OKBLUE 		= '\033[94m'
	OKGREEN 	= '\033[92m'
	FAIL 		= '\033[91m'
	ENDC 		= '\033[0m'

	__gd_client 	= None
	__curr_key 		= None
	__wksht_id		= None
	__lista_feed	= None

	# Inicia a classe com os atributos default: senha, email
	def __init__(self, email, senha):
		self.gd_client = gdata.spreadsheet.service.SpreadsheetsService()
		self.gd_client.email = email
		self.gd_client.password = senha
		self.gd_client.source = 'Exportador para criar tabela timeline google spreadsheet'
		self.gd_client.ProgrammaticLogin()
		self.curr_key = ''
		self.wksht_id = ''
		self.lista_feed = None


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
		col_label = ["Start Date", "End Date", "Headline", "Text", "Media", "Media Credit", "Media Caption", "Media Thumbnail", "Type", "Tag"]
		for i in range(1,10):
			entry = self.gd_client.UpdateCell(row=1, col=i, inputValue=col_label[i], key=self.curr_key, wksht_id=self.wksht_id)
			if isinstance(entry, gdata.spreadsheet.SpreadsheetsCell):
				print self.OKBLUE + '::INSERT Label %s' % col_label[i] + self.ENDC
			else:
				print self.FAIL + '::FAIL Label %s' % col_label[i] + self.ENDC
		print 'Finish setting up!'

	# Metodo responsavel pela sequencia de execucao da classe
	def run(self):
		self.__get_spreadsheet()
		self.__get_worksheet()
		self.__set_worksheet_timeline()

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