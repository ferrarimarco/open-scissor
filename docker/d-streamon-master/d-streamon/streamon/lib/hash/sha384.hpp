/*
 * @file    sha384.hpp
 * @author  Fabrizio Nuccilli
 * @version 1.0
 *
 * @section LICENSE
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of
 * the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details at
 * http://www.gnu.org/copyleft/gpl.html
 *
 * @section DESCRIPTION
 *
 * The class represents the SHA224 function
 *
 */

#ifndef SHA384_HPP_
#define SHA384_HPP_

#include "hash.hpp"
#define dgstlen384 48


namespace bm {

class SHA384 : public HASH
{


public:

    SHA384():HASH(dgstlen384){}

    /*
     * this method compute the digest of a key
     * @param key is the key that is to be hashed
     * @param len is the key length
     * @param output is the array where the message digest is stored
     */
    virtual void compute(const unsigned char key[], int len, unsigned char output[]);

    /*
     * this method hashes a file
     * @param filepath the file path
     * @param output is the array where the message digest is stored
     */
    virtual void computeFile(const char *filepath, unsigned char output[]);

    /*
     * HMAC
     * this method implements a message authentication code (MAC)
     * involving SHA384 in combination with a secret key
     * @param key is the key
     * @param keylen is the key length
     * @param input is the original message
     * @param ilen is the length of the original message
     * @param output is the array where the message digest is stored
     */
    virtual void compute(const unsigned char *key, int keylen, const unsigned char *input, int ilen,
                unsigned char output[]);


};

}

#endif