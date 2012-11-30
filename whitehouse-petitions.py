# -*- coding: utf-8 -*-
import requests
import lxml.html
import sys
import csv
import json
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="filename to write to (csv)", metavar="FILE")
parser.add_option("-u", "--url", dest="petition_url",
                  help="URL of petition", metavar="URL")
(options, args) = parser.parse_args()

if options.petition_url is None:
	print "\nYou must provide a URL to the petition\n"
	parser.print_help()
	exit(-1)

if options.filename is None:
	print "\nYou must provide a filename to save to\n"
	parser.print_help()
	exit(-1)

response_petition_url = 'https://petitions.whitehouse.gov/signatures/more/%s/%s/%s'

def process_response(response,page):
	root = lxml.html.fromstring (response)
	data = []
	record = {}
	if page == 1:
		creator = root.xpath('div[@class="entry entry-creator "]/div')
		record['name'] = creator[1].text
		record['location'] = creator[2].text
		record['date'] = creator[2][0].tail
		record['nr'] = creator[2][1].tail.strip().replace('Signature # ','')
		data.append(record)
		record = {}
	end_of_line_registrants = root.xpath('div[@class="entry entry-reg last"]')
	for registrant in end_of_line_registrants:
		record['name'] = registrant[0].text
		record['location'] = registrant[2].text
		record['date'] = registrant[2][0].tail
		record['nr'] = registrant[2][1].tail.strip().replace('Signature # ','')
		data.append(record)
		record = {}
	registrants = root.xpath('div[@class="entry entry-reg "]')
	for registrant in registrants:
		record['name'] = registrant[0].text
		record['location'] = registrant[2].text
		record['date'] = registrant[2][0].tail
		record['nr'] = registrant[2][1].tail.strip().replace('Signature # ','')
		data.append(record)
		record = {}
	try:
		arg = root.xpath('//a[@class="load-next no-follow"]')[0].attrib['rel']
		last_id = root.xpath('//div[@id="last-signature-id"]')[0].text_content()
		print 'Found',len(data),'signatures on result page',page
		return arg,last_id,data
	except:
		# Done
		print 'Found', len(data),'signatures on result page',page
		return '','',data

def get_response(arg,page,last_id):
	response = requests.get(response_petition_url % (arg,page,last_id)).text
	json_response = json.loads(response)
	new_arg,new_last_id,data = process_response(json_response['markup'],page)
	return new_arg,new_last_id,data

csv_keys = ['name', 'location', 'date', 'nr']
page = 1
#get first page
petition_html = requests.get(options.petition_url).text
root = lxml.html.fromstring (petition_html)
try:
	total_signatures = str(root.xpath('//span[@class="total-count"]')[0].text)
	print 'total signatures: ', total_signatures
except Exception,e:
	print 'Something went wrong! Could it be that the URL you provided is not correct?'
	print
	parser.print_help()
	exit(-1)
arg = root.xpath('//a[@class="load-next no-follow active"]')[0].attrib['rel']
last_id = root.xpath('//div[@id="last-signature-id"]')[0].text_content()
f = open(options.filename, 'wb')
dict_writer = csv.DictWriter(f, csv_keys)
dict_writer.writer.writerow(csv_keys)
if last_id:
	next = True
while next == True:
	if last_id != '':
		arg,last_id,data = get_response(arg,page,last_id)
		#save to file
		dict_writer.writerows(data)
		page = page+1
	else:
		print 'Done processing petition. Fetched',page-1, 'pages.'
		print 'Wrote to file "',options.filename,'"'
		f.close()
		next = False

