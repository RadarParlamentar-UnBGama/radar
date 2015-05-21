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
import re

# A classe realiza a exportacao dos dados das biografias das deputadas para
# 		uma planilha na conta inserida no console
# WARNING: a planilha que sera alterada deve conter o nome especifico 'timeline_deputadas'
# 		e a aba deve ter o nome 'timeline'
# TODO: colocar mais dados na biografia
# TODO: colocar mais peridos de legislatura de uma mesma deputada
# TODO: metodo para evitar configurar a primeira linha toda vez
# TODO: modularizar melhor?
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
	def __init__(self, email, senha, file_dir):
		self.gd_client = gdata.spreadsheet.service.SpreadsheetsService()
		self.gd_client.email = email
		self.gd_client.password = senha
		self.gd_client.source = 'Exportador para criar tabela timeline google spreadsheet'
		self.gd_client.ProgrammaticLogin()
		self.curr_key = ''
		self.wksht_id = ''
		self.xml_tree = etree.parse(file_dir)
		self.root_tree = self.xml_tree.getroot()

	# Procura pelo documento "timeline_deputadas" dentro da conta inserida
	# Sempre captura a primeira ocorrencia do nome
	def __get_spreadsheet(self):
		print 'Searching for your spreadsheet...'
		has_timeline_deputadas = False
		feed = self.gd_client.GetSpreadsheetsFeed()
		for i, entry in enumerate(feed.entry):
			if entry.title.text == "timeline_deputadas":
				has_timeline_deputadas = True
				id_part = feed.entry[i].id.text.split('/')
				self.curr_key = id_part[len(id_part) - 1]
				print self.OKGREEN + 'Spreadsheet %s encontrado!' % entry.title.text + self.ENDC

		if not has_timeline_deputadas:
			print self.FAIL + 'Nao existe Spreadsheet com o nome "timeline_deputadas"!'
			print 'Por favor tenha certeza de que existe um arquivo na conta "%s"' % self.gd_client.email + self.ENDC
			exit(2)

	# Procura pelo worksheet "timeline" do spreadsheet
	def __get_worksheet(self):
		print 'Buscando worksheet...'
		feed = self.gd_client.GetWorksheetsFeed(self.curr_key)
		for i, entry in enumerate(feed.entry):
			if entry.title.text == "timeline":
				id_part = feed.entry[i].id.text.split('/')
				self.wksht_id = id_part[len(id_part) - 1]
				print self.OKGREEN + 'Worksheet %s encontrado!' % entry.title.text + self.ENDC

	# Configura spreadsheet inicial para timeline
	# Adiciona a primera linha com os identificadores da coluna
	def __set_worksheet_timeline(self):
		print 'Configurando spreadsheet para a timeline'
		col_label = ["startdate", "enddate", "headline",
		"text", "media", "mediacredit", "mediacaption",
		"mediathumbnail", "type", "tag"]
		for i in range(1,11): # Percorre a lista col_label
			self.__update_cell(1, i, col_label[i-1])
		print 'Configuracao completa!'

	# Update celula especifica
	def __update_cell(self, row, col, inputValue):
		entry = self.gd_client.UpdateCell(row=row, col=col, inputValue=inputValue, key=self.curr_key, wksht_id=self.wksht_id)
		print self.WARNING + '::UPDATING:: Row - %s and Column - %s' % (row, col) + self.ENDC
		if isinstance(entry, gdata.spreadsheet.SpreadsheetsCell):
			print self.OKBLUE + '::UPDATE:: Value - %s' % inputValue + self.ENDC
		else:
			print self.FAIL + '::FAIL:: Value - %s' % inputValue + self.ENDC

	# Adiciona em cada linha as biografias
	# A biografia contem: Nome da parlamentar, mandato, partido
	def __set_biography(self):

		print self.WARNING + 'Procurando por Deputadas...' + self.ENDC
		has_deputada = False
		for data_record in self.root_tree.findall('DATA_RECORD'):
			try:
				if data_record.find('INDSEXO').text == "F":
					has_deputada		= True

					id_cadastro			= data_record.find('IDECADASTRO').text
					mandato 			= data_record.find('MANDATOSCD').text
					nome_parlamentar	= data_record.find('TXTNOME').text
					sig_partido			= data_record.find('SIGPARTIDO').text

					legislatura	= data_record.find('LEGISLATURAS').text
					dates 		= self.__split_date(legislatura)
					start_date 	= self.__search_start_date(mandato)
					end_date	= '1/1/' + dates[1]

					row_data	= 'startdate='+start_date+';enddate='+end_date+';headline='+nome_parlamentar+';text=Partido: '+ sig_partido + ' Mandato: ' + mandato
					self.__insert_row(row_data, id_cadastro)

			except AttributeError:
				print self.FAIL + '::FAIL:: ID ' + data_record.find('IDECADASTRO').text + ' - Doent have INDSEXO! Moving on...' + self.ENDC
				pass
		if not has_deputada:
			print self.WARNING + 'Nao existe Deputada!' + self.ENDC

	# Insere uma linha nova, caso nao encontre nenhuma vazia, com os dados 'row_data'
	def __insert_row(self, row_data, debug_id_cadastro):
		dictionary = self.__dictionary_maker(row_data)
		if not self.__is_inserted(dictionary["headline"]):
			entry = self.gd_client.InsertRow(dictionary, self.curr_key, self.wksht_id)
			if isinstance(entry, gdata.spreadsheet.SpreadsheetsList):
				print self.OKBLUE + '::INSERT:: ID > ' + debug_id_cadastro + self.ENDC
		else:
			print '::DUPLICADO:: ID > ' + debug_id_cadastro 

	# Procura dentro de mandato a data de posse
	def __search_start_date(self, mandato):
		date = re.search('([0]?[1-9]|[1|2][0-9]|[3][0|1])[./-]([0]?[1-9]|[1][0-2])[./-]([0-9]{4}|[0-9]{2})',mandato)
		return date.group(0)

	# Separa os periodos das legislaturas
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

	# Monta um dicionario no formato de insercao dos dados no spreadsheet
	def __dictionary_maker(self,row_data):
		dict = {}
		for param in row_data.split(';'):
			temp = param.split('=')
			dict[temp[0]] = temp[1]
		return dict

	# Retorna verdadeiro se uma parlamentar ja existe na planilha
	def __is_inserted(self, headline):
		feed = self.gd_client.GetCellsFeed(self.curr_key, self.wksht_id)
		result = False
		for i,entry in enumerate(feed.entry):
			if entry.content.text.decode('utf-8') == headline:
				result = True
		return result

	# Metodo responsavel pela sequencia de execucao da classe
	def run(self):
		self.__get_spreadsheet()
		self.__get_worksheet()
		# self.__set_worksheet_timeline()
		self.__set_biography()

def main():
	# Linha de comando para o terminal
	try:
		opts, args = getopt.getopt(sys.argv[1:], "", ["user=", "pw=", "file="])
	except getopt.error, msg:
		print 'python spreadsheetExample.py --user [username] --pw [password] --file [file_dir]'
		sys.exit(2)

	user 		= ''
	password	= ''
	file_dir	= ''

	# Processando opcoes inseridas no console
	for opcao, atributo in opts:
		if opcao == "--user":
			user = atributo
		elif opcao == "--pw":
			password = atributo
		elif opcao == "--file":
			file_dir = atributo

	if user == '' or password == '' or file_dir == '':
		print 'python spreadsheetExample.py --user [username] --pw [password] --file [file_dir]'
		sys.exit(2)

	exportar = ExportadorGoogleSpreadsheet(user, password, file_dir)
	exportar.run()

if __name__ == '__main__':
  main()