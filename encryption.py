from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA3_512
import sys


class encryption:
	# the constructor takes zero or one argument.  The argument can either be an RSA key or a file containing and RSA key.
	def __init__(self, key=None, keyFile=None):
		if key != None:  				# if a key was provided 
			self.key = RSA.import_key(key) 		# import the key
		elif keyFile != None:				# else if a file name was provided
			f = open(keyFile)			# open the file
			self.key = RSA.import_key(f.read())	# and parse the data into a key
			f.close()				# and close the file
		else:						# if no key or keyfile were provided
			self.key = RSA.generate(2048)		# generate a new RSA key that is 2058 bits long

	# write key will write the RSA key to file with the option of providing a password
	def writeKey(self, filename, password=None):	
		export_key = None				
		if password!=None:				# if a password is provided
			# create the export key with AES 128 encryption
			export_key = self.key.exportKey(passphrase=password, pkcs=8, protection="scryptAndAES128-CBC")
		else:
			#other wise create the export key
			export_key = self.key.exportKey()

		
		file_out = open(str(filename), "wb")		# create a file for write access
		file_out.write(export_key)			# write the export key to file
		file_out.close()				# close the file


	# read key will load an RSA key from a file. it takes a file name to open and the optional password for that file
	def readKey(self, filename, password=None):
		f = open(str(filename), "rb")		# open the file for reading
		import_key = f.read()			# read the data from the file
		if password != None:			# if a password was provided
			# import the key with a password
			self.key = RSA.import_key(encoded_key, passphrase=password)
		else:
			# else import the key without a password
			self.key = RSA.import_key(import_key)
		f.close()				# close the file.


	# encrypt data and write to file, takes the filename and the data to be encrypted
	def encrypt(self, filename, data):
		file_out = open(str(filename), "wb")		# open the file for writing

		session_key = get_random_bytes(16)		# create the session key to be used in the AES
								# encryption

		# Encrypt the session key with the public RSA key
		
		cipher_rsa = PKCS1_OAEP.new(self.key)		# first the session key is encrypted using the RSA public key

		file_out.write(cipher_rsa.encrypt(session_key))	# the encrypted session key is written to the file

		# Encrypt the data with the AES session key
		cipher_aes = AES.new(session_key, AES.MODE_EAX)		# using the session key create a new AES cipher
		ciphertext, tag = cipher_aes.encrypt_and_digest(data)	# get the encryption and the hash of the original data
		[ file_out.write(x) for x in (cipher_aes.nonce, tag, ciphertext) ]  # write the nonce, hash, and encrypted data to file
		file_out.close()

	# decrypt data from file, takes the name of the file to be decrypted
	def decrypt(self, filename):
		file_in = open(str(filename), "rb")		# open the file
		# load the encrypted session key, nonce, hash and encrypted data
		enc_session_key, nonce, tag, ciphertext = \
		   [ file_in.read(x) for x in (self.key.size_in_bytes(), 16, 16, -1) ]

		file_in.close()					# close the file
		# Decrypt the session key with the public RSA key
		cipher_rsa = PKCS1_OAEP.new(self.key)			# load the RSA private key
		session_key = cipher_rsa.decrypt(enc_session_key)	# decrypt the AES session key

		# Decrypt the data with the AES session key
		cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)  # load the AES session key
		data = cipher_aes.decrypt_and_verify(ciphertext, tag)	# decrypt the data
		
		return data  # return the data

# global function to hash data
def hashData(dataToHash):
	hash = SHA3_512.new()
	hash.update(dataToHash)
	hashed = hash.hexdigest()
	return hashed
