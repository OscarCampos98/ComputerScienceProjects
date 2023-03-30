#!/usr/bin/env python3

##### IMPORTS

import argparse

from collections.abc import Callable

from multiprocessing import Pool
from os import cpu_count

from sys import exit, stdout

from time import time_ns
from typing import Iterator, Mapping, Optional, Union

# add any additional modules you need here

#libary used to generate a random n 
import secrets
import hashlib
import sys
import math

#Advice for Tut Wednesday 
# -one time pad (xor)
#- do we have to go from 0 and go from there, offset.


##### METHODS

def block_idx( block_size:int, offset:int = 0 ) -> Iterator[bytes]:
    """A generator for creating an arbitrary number of block indicies.   `

       PARAMETERS
       ==========
       block_size: The size of block to use, in bytes. Determines the maximum number 
         of blocks returned, as well.
       offset: The number this generator will start counting from. Defaults to zero.

       YIELDS
       ======
       Successive block indicies.
       """

    mask = (1 << (block_size*8)) - 1 # set an upper limit AND bitmask
    idx  = 0
    while idx <= mask:

        # adding the offset is slower, but the bookkeeping is easier
        output = (idx + offset) & mask
        yield output.to_bytes( block_size, 'big' )
        idx += 1

# semantic security, 
# one time function 
# which library (woodyrandom)
#one liner

def generate_iv( length:int ) -> bytes:
    """Generate an initialization vector for encryption. Must be drawn from a
       cryptographically-secure pseudo-random number generator.

       PARAMETERS
       ==========
       length: The length of the IV desired, in bytes.

       RETURNS
       =======
       A bytes object containing the IV.
       """   
    assert type(length) is int
    return secrets.token_bytes(length)

#notes from TA:
    # hash function, how big? 
    # n = is the block :  size m = digest size

# the use of the hashlib library was used to implement the Hasher function 
    #resource: https://docs.python.org/3/library/hashlib.html
class Hasher:
    """Encapsulates the hash function used for encryption. This is written as a
       class so that we have easy access to both the hash and hash's block size.

       EXAMPLES:

       > h = Hasher()
       > print( h.digest_size )
       32
       > h.hash( b'test value' )
       b'a byte object 32 characters long'

       """

    def __init__( self ):
        """Create a Hasher. This mostly exists to put the block size in place."""

# Uncomment the following line of code and substitute the hash's output block 
#  size.

    #double check, according to the interner this should be the ideal size (sha256)
        self.digest_size = 32

# Uncomment the following line of code and substitute the hash's ideal input 
#  block size. IMPORTANT: this is almost never the same size as the digest size!
# documentation on the web

        self.block_size = 64

# phyton library and 32 out and digest are a good enough size 
    def hash( self, data:bytes ) -> bytes:
        """Hash an arbitrary number of bytes into a 32-byte output. Hopefully this is
           done in a cryptographically-secure way.

           PARAMETERS
           ==========
           data: The bytes object to be hashed.

           RETURNS
           =======
           A bytes object containing 32 bytes of hash value.
           """
        assert type(data) is bytes
        return hashlib.sha256(data).digest()
    
        
 

# notes from TA:
    # where do we put the extra 0's at the end (little indian) 
    # byte to int and then int to byte
    # byte array 

def xor( a:bytes, b:bytes ) -> bytes:
    """Bit-wise exclusive-or two byte sequences. If the two bytes objects differ in
       length, pad with zeros.

       PARAMETERS
       ==========
       a, b: bytes objects to be XORed together.

       RETURNS
       =======
       A bytes object containing the results.
       """
    assert type(a) is bytes
    assert type(b) is bytes

    #check lenght of both a and b byte streams, who is shortest
    #length of a and b 
    bArray_a = bytearray(a)
    bArray_b = bytearray(b)

    #shorts, pad with 0 at end 
    if len(a) < len(b):
        add = len(b) - len(a)
        for x in range(add):
            bArray_a.append(0)
    if len(b) < len(a):
        add = len(a) - len(b)
        for x in range(add):
            bArray_b.append(0)
 
     #xor, byte to int and then int to byte
     #resource used for the xor computation: https://stackoverflow.com/questions/23312571/fast-xoring-bytes-in-python-3
     # 3rd answer from the post 
    
    #compute xor using two byte arrays of equal length
    input = bArray_a 
    #enumerate trough the byte array b
    for i, b in enumerate(bArray_b): 
        #compute xor computation with the corresponding index of the byte array
        input[i] = input[i] ^ b

    #convert the byte array to a sequence of bytes     
    result = bytes(input) 
    return result 



# documentation 4. piazza
# resources: https://datatracker.ietf.org/doc/html/rfc2104.html
def HMAC( data:bytes, key:bytes, hasher:Hasher ) -> bytes:
    """Perform HMAC with the given hash function . Be sure to read the HMAC spec carefully!

       PARAMETERS
       ==========
       data:   The bytes object to be hashed.
       key:    A bytes object to be used as a key.
       hasher: A Hasher instance.

       RETURNS
       =======
       A bytes object containing the digest.
       """
    assert type(data) is bytes
    assert type(key) is bytes

    #takes a message M containing blocks of length b bits
        #check that the key length is the same as block size
    if len(key) > hasher.block_size:
        padded_key = hasher.hash(key)
    else:
        padded_key = key

    #ipad = the byte 0x36 = \x36 repeated B times
    ipad = b'\x36' * hasher.block_size

    #opad = the byte 0x5c = \x5c repeated B times.
    opad = b'\x5c' *hasher.block_size
 
    #XOR (bitwise exclusive-OR) the padded key string with ipad 
        #append data
        # apply hash 
    input = hasher.hash(xor(ipad,padded_key) + data)
    
    # XOR2 (bitwise exclusive-OR) the padded key with opad
        #append previous hash from input to XOR computation 
        #hash XOR2 with input 
    result = hasher.hash(xor(padded_key, opad) + input)

    return result


#align to block and digest as possible.
#  always pad. 
# RFC5652. 1 byte size and add to the end  PK7 
# add as many lines as you can

#resource: https://www.rfc-editor.org/rfc/rfc5652#section-6.3
def pad( data:bytes, digest_size:int ) -> bytes:
    """Pad out the given bytes object with PKCS7 so it fits within the given 
       digest size. That size is guaranteed to be 255 bytes or less.

       PARAMETERS
       ==========
       data:        The bytes object to be padded.
       digest_size: The output length in bytes is 0 mod digest_size.

       RETURNS
       =======
       A bytes object containing the padded value.
       """
    assert type(data) is bytes
    assert type(digest_size) is int
    assert (digest_size > 1) and (digest_size < 256)

    # input shall be padded at the trailing end with
    # k-(lth mod k) octets all having value k-(lth mod k)
    # where lth is the length of the input.
    # The value of each added byte is the number of bytes that are added,

    padding_value = digest_size -  (len(data) % digest_size)
    padding = padding_value.to_bytes(1,'big') * padding_value
    return data + padding 


def unpad( data:bytes ) -> Optional[bytes]:
    """Remove PKCS7 from the given bytes object.

       PARAMETERS
       ==========
       data:       The bytes object to have any padding removed.

       RETURNS
       =======
       Either a bytes object containing the original value, or None if 
         no valid padding was found.
       """
    assert type(data) is bytes

    #check the last character of the byte string 
    padding_val = data[-1]
    padding_values = data[-padding_val:]
    
    #if 0 do nothing 
    if padding_val == 0:
        return None
    #check PKCS7 correct padding on the lasts corresponding bytes 
    else:
        for x in range(padding_val):
            if padding_values[x] != padding_val:
                return None 

    #remove the PKCS7 padding and return byte
    result = data[0:-padding_val]
    return result


# the documentaion itself for reference 
def encrypt( iv:bytes, data:bytes, key:bytes, hasher:Hasher, \
        block_ids:Callable[[int], Iterator[bytes]] ) -> bytes:
    """Encrypt the given data, with the given IV and key, using the given hash function.
       Assumes the data has already been padded to align with the digest size. Do not
       prepend the IV. The IV must have the same length as the hash function's block size.

       PARAMETERS
       ==========
       iv:        The initialization vector used to boost semantic security
       data:      The padded data to be encrypted.
       key:       A bytes object to be used as a key.
       hasher:    A Hasher instance.
       block_ids: A generator that generates block indexes of a specific size.
            (see block_idx())

       RETURNS
       =======
       A bytes object containing the encrypted value. Note that the return is not a list or
         generator.
       """
    assert type(iv) is bytes
    assert type(key) is bytes
    assert type(data) is bytes
    assert (len(data) % hasher.digest_size) == 0
    assert len(iv) == hasher.block_size

    #list to append all cipher blocks for joining 
    list_to_join = list()

    #create a generator from block_ids of size block size
    gen_blocks = block_ids(hasher.block_size)
    
    #number of blocks to itirate from provided data (whole blocks)
        #digest = size of the output block
    num_blocks = math.floor(len(data) / hasher.digest_size)

    #for each block 
    for x in range(num_blocks):
        #pull a block ID from the genrator 
        pull = next(gen_blocks)
        #XOR with the initial vector
        XOR1 = xor(pull, iv) 
        #feed as input into HMAC()
        HMAC1 = HMAC(XOR1, key, hasher)

        #find plaintext block for the XOR (L block= digest size)
        index = x * hasher.digest_size
        plaintext = data[index: index + hasher.digest_size]

        #XOR the output of HMAC() with the plaintext block to create a ciphrer block
        CipherBlock = xor(HMAC1,plaintext)
        #append to list 
        list_to_join.append(CipherBlock)

    #join all the ciphertext blocks into one continous byte sequence 
    Byte_sequence = b''.join(list_to_join)

    return Byte_sequence

# HCMAC() is plaintext
# Encrypt and then MAC is the recomended one 
def pad_encrypt_and_HMAC( plaintext:bytes, key_cypher:bytes, key_HMAC:bytes, hasher:Hasher, \
        block_ids:Callable[[int], Iterator[bytes]] ) -> bytes:
    """Encrypt a plaintext with your encryption function. Note the order of operations!
    
       PARAMETERS
       ==========
       plaintext: The bytes object to be encrypted. Not necessarily padded!
       key_cypher: The bytes object used as a key to encrypt the plaintext.
       key_HMAC: The bytes object used as a key for the keyed-hash MAC.
       hasher: A Hasher instance.
       block_ids: A generator that generates block indexes of a specific size.
            (see block_idx())

       RETURNS
       =======
       The cyphertext, as a bytes object. Note that the return is not a list or
         generator.
       """

    assert type(plaintext) is bytes
    assert type(key_cypher) is bytes
    assert type(key_HMAC) is bytes

    #HMAC() the combination using HMAC key, create a tag
    tag = HMAC(plaintext, key_cypher,hasher)
    generated_IV = generate_iv(hasher.block_size)
    
    #Pad the plaintext, then encrypt the padded plaintext with encryption key = ciphertext
    plaintext_pad = pad(plaintext, hasher.digest_size)
    cyphertext = encrypt(generated_IV, plaintext_pad, key_cypher, hasher, block_ids)
    
    #prepend the init vector to cyphertext 
    prepend = generated_IV + cyphertext

    #append the tag, final result, IV||CipherText||HMAC-tag
    result = prepend + tag

    return result 

# reverse, if everything passes 
def decrypt_and_verify( cyphertext: bytes, key_cypher: bytes, key_HMAC:bytes, hasher:Hasher, \
        block_ids:Callable[[int], Iterator[bytes]] ) -> Optional[bytes]:
    """Decrypt a plaintext that had been encrypted with the prior function.
       Also performs integrity checking to help ensure the original wasn't
       corrupted.
    
       PARAMETERS
       ==========
       cyphertext: The bytes object to be decrypted
       key_cypher: The bytes object used as a key to decrypt the plaintext.
       key_HMAC: The bytes object used as a key for the keyed-hash MAC.
       hasher: A Hasher instance.
       block_ids: A generator that generates block indexes of a specific size.
            (see block_idx())

       RETURNS
       =======
       If the cyphertext could be decrypted and validates, this returns a bytes 
         object containing the plaintext. Otherwise, it returns None.
       """

    assert type(cyphertext) is bytes
    assert type(key_cypher) is bytes
    assert type(key_HMAC) is bytes
    
    # Check that the length of ciphertext == IV(block size) + cypherT(digest) + HMAC(digest)
    # if passes continue if not return nothing 
    if len(cyphertext) < (hasher.block_size + hasher.digest_size + hasher.digest_size):
        return None
    
    # verify HMAC (32bytes) appended to the end of cypher text ==, since it cannot be reserver 
    mac = cyphertext[-hasher.digest_size:]

    # if both condition passes then we can continue with the decription 
    # decripton = M = C xor K
    iv = cyphertext[:hasher.block_size]
    encrypted = cyphertext[hasher.block_size : -hasher.digest_size]
    padded = encrypt(iv, encrypted, key_cypher,hasher,block_ids)
    plaintext = unpad(padded)
    
    if plaintext is none:
        return None
    
    #finaly we test MAC
    test = HMAC (plaintext,key_HMAC, hasher)
    
    if test != mac:
        return None
    else:
        return plaintext
##### MAIN

if __name__ == '__main__':

    # parse the command line args
    cmdline = argparse.ArgumentParser( description="Encrypt or decrypt a file." )

    methods = cmdline.add_argument_group( 'ACTIONS', "The three actions this program can do." )

    methods.add_argument( '--decrypt', metavar='FILE', type=argparse.FileType('rb', 0), \
        help='A file to be decrypted.' )
    methods.add_argument( '--encrypt', metavar='FILE', type=argparse.FileType('rb', 0), \
        help='A file to be encrypted.' )
    methods.add_argument( '--dump', action='store_true', \
        help='Dump a binary stream generated by the hash function to stdout. Handy for testing its quality.' )

    methods = cmdline.add_argument_group( 'OPTIONS', "Modify the defaults used for the above actions." )

    methods.add_argument( '--output', metavar='OUTPUT', type=argparse.FileType('wb', 0), \
        help='The output file. If omitted, print the decrypted plaintext or dump to stdout. The destination\'s contents are wiped, even on error.' )
    methods.add_argument( '--password', metavar='PASSWORD', type=str, default="swordfish", \
        help='The password to use as a key.' )
    methods.add_argument( '--reference', metavar='FILE', type=argparse.FileType('rb', 0), \
        help='If provided, check the output matches what is in this file.' )
    methods.add_argument( '--threads', type=int, default=0, \
        help='Number of threads to use with dump. Numbers < 1 implies all available.' )

    methods.add_argument( '--offset', type=int, default=0, \
        help='An offset into the sequence used during dump.' )

    args = cmdline.parse_args()

    if args.threads < 1:
        args.threads = cpu_count()

    if args.offset < 0:
        args.offset *= -1;

    h = Hasher()

    # which mode are we in?
    if args.decrypt:

        # hash the key to obscure it, then split that into two derived keys
        key       = h.hash( args.password.encode('utf-8') )
        key_enc   = key[:len(key)>>1]
        key_HMAC  = key[len(key)>>1:]

        plaintext = decrypt_and_verify( args.decrypt.read(), key_enc, key_HMAC, h, \
                block_idx )
        args.decrypt.close()

        if plaintext is None:
            print( "ERROR: Could not decrypt the file!" )
            exit( 1 )

        if args.reference:
            ref = args.reference.read()
            if ref != plaintext:
                print( "ERROR: The output and reference did not match!" )
                exit( 2 )

        if args.output:
            args.output.write( plaintext )
            args.output.close()

        else:
            try:
                print( plaintext.decode('utf-8') )
            except UnicodeError as e:
                print( "WARNING: Could not print out the encrypted contents. Was it UTF-8 encoded?" )
                exit( 3 )

    elif args.encrypt:

        key       = h.hash( args.password.encode('utf-8') )
        key_enc   = key[:len(key)>>1]
        key_HMAC  = key[len(key)>>1:]

        cyphertext = pad_encrypt_and_HMAC( args.encrypt.read(), key_enc, key_HMAC, h, \
                block_idx )

        if args.reference:
            ref = args.reference.read()
            if ref != cyphertext:
                print( "ERROR: The output and reference did not match!" )
                exit( 4 )

        if args.output:
            args.output.write( cyphertext )
            args.output.close()

        else:
            print( "As the cyphertext is binary, it will not be printed to stdout." )

    elif args.dump:

        generator = block_idx( h.block_size, args.offset )
        if args.threads > 1:
            with Pool(args.threads) as p:
                for output in p.imap( h.hash, generator, 64 ):
                    if args.output:
                        args.output.write( output )
                    else:
                        stdout.buffer.write( output )
        else:
            for output in map( h.hash, generator ):
                if args.output:
                    args.output.write( output )
                else:
                    stdout.buffer.write( output )

    else:

        print( "Please select one of encryption, decryption, or dumping." )
