# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Important

The AWS SDKs sign API requests for you using the access key that you specify when you
configure the SDK. When you use an SDK, you don’t need to learn how to sign API requests.
We recommend that you use the AWS SDKs to send API requests, instead of writing your own code.

The following example is a reference to help you get started if you have a need to write
your own code to send and sign requests. The example is for reference only and is not
maintained as functional code.
"""

# AWS Version 4 signing example

# DynamoDB API (CreateTable)

# See: http://docs.aws.amazon.com/general/latest/gr/sigv4_signing.html
# This version makes a POST request and passes request parameters
# in the body (payload) of the request. Auth information is passed in
# an Authorization header.
import sys, os, datetime, hashlib, hmac, json
import requests

def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def getSignatureKey(key, date_stamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

def aws_post(method, service, path, body, access_key, secret_key, region="us-east-1", host=None, endpoint=None):
    if not host:
        host = f"{service}.{region}.amazonaws.com"
    if not endpoint:
        endpoint = f"https://{host}{path}"
            
    content_type = 'application/x-amz-json-1.0'
    # DynamoDB requires an x-amz-target header that has this format:
    #     DynamoDB_<API version>.<operationName>
    amz_target = 'DynamoDB_20120810.CreateTable'

    # Request parameters for CreateTable--passed in a JSON block.
    request_parameters = body

    # Create a date for headers and the credential string
    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope


    # ************* TASK 1: CREATE A CANONICAL REQUEST *************
    # http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html

    # Step 1 is to define the verb (GET, POST, etc.)--already done.

    # Step 2: Create canonical URI--the part of the URI from domain to query 
    # string (use '/' if no path)
    canonical_uri = path

    ## Step 3: Create the canonical query string. In this example, request
    # parameters are passed in the body of the request and the query string
    # is blank.
    canonical_querystring = ''

    # Step 4: Create the canonical headers. Header names must be trimmed
    # and lowercase, and sorted in code point order from low to high.
    # Note that there is a trailing \n.
    canonical_headers = 'content-type:' + content_type + '\n' + 'host:' + host + '\n' + 'x-amz-date:' + amz_date + '\n'

    # Step 5: Create the list of signed headers. This lists the headers
    # in the canonical_headers list, delimited with ";" and in alpha order.
    # Note: The request can include any headers; canonical_headers and
    # signed_headers include those that you want to be included in the
    # hash of the request. "Host" and "x-amz-date" are always required.
    # For DynamoDB, content-type and x-amz-target are also required.
    signed_headers = 'content-type;host;x-amz-date'

    # Step 6: Create payload hash. In this example, the payload (body of
    # the request) contains the request parameters.
    payload_hash = hashlib.sha256(request_parameters.encode('utf-8')).hexdigest()

    # Step 7: Combine elements to create canonical request
    canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash


    # ************* TASK 2: CREATE THE STRING TO SIGN*************
    # Match the algorithm to the hashing algorithm you use, either SHA-1 or
    # SHA-256 (recommended)
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = date_stamp + '/' + region + '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' +  amz_date + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    # ************* TASK 3: CALCULATE THE SIGNATURE *************
    # Create the signing key using the function defined above.
    signing_key = getSignatureKey(secret_key, date_stamp, region, service)

    # Sign the string_to_sign using the signing_key
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()


    # ************* TASK 4: ADD SIGNING INFORMATION TO THE REQUEST *************
    # Put the signature information in a header named Authorization.
    authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

    # For DynamoDB, the request can include any headers, but MUST include "host", "x-amz-date",
    # "x-amz-target", "content-type", and "Authorization". Except for the authorization
    # header, the headers must be included in the canonical_headers and signed_headers values, as
    # noted earlier. Order here is not significant.
    # # Python note: The 'host' header is added automatically by the Python 'requests' library.
    headers = {'Content-Type':content_type,
            'X-Amz-Date':amz_date,
            'Authorization':authorization_header}

    return requests.post(endpoint, data=request_parameters, headers=headers)

def send_email(destination, body, subject, source, region, access_key, secret_key):
    method = "POST"
    service = "ses"
    path = "/v2/email/outbound-emails"
    body = json.dumps({
        "Content": { 
            "Simple": { 
                "Body": {
                    "Text": { 
                        "Charset": "UTF-8",
                        "Data": body
                    }
                },
                "Subject": { 
                    "Charset": "UTF-8",
                    "Data": subject
                }
            }
        },
        "Destination": {
            "ToAddresses": [ destination ]
        },
        "FromEmailAddress": source
    })
    status = -1
    text = "Unknown Error"
    try:
        r = aws_post(method, service, path, body, access_key, secret_key, region, host=f"email.{region}.amazonaws.com")
        status = r.status_code
        text = r.text
        assert status == 200
    except:
        raise RuntimeError(f"Failed to send email: {status} ({text})")
    
