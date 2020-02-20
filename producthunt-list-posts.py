
# ---
# name: producthunt-list-posts
# deployed: true
# title: Product Hunt List Posts
# description: Returns a list of producthunt posts for today
# params:
#   - name: properties
#     type: array
#     description: The properties to return (defaults to all properties). See "Returns" for a listing of the available properties.
#     required: false
# returns:
#   - name: id
#     type: string
#     description: The id for the product post
#   - name: name
#     type: string
#     description: The name of the product being featured
#   - name: url
#     type: string
#     description: The url of the product being featured
#   - name: tagline
#     type: string
#     description: The tagline of the product being featured
#   - name: description
#     type: string
#     description: A description of the product being featured
#   - name: createdAt
#     type: string
#     description: The date the product post was created
#   - name: featuredAt
#     type: string
#     description: The date the product was featured
# examples:
#   - '"*"'
#   - '"id, name, url, tagline"'
# ---

import json
import requests
import urllib
import itertools
from datetime import *
from decimal import *
from cerberus import Validator
from collections import OrderedDict

# main function entry point
def flexio_handler(flex):

    # get the api key from the variable input
    auth_token = dict(flex.vars).get('producthunt_connection',{}).get('access_token')
    if auth_token is None:
        flex.output.content_type = "application/json"
        flex.output.write([[""]])
        return

    # get the input
    input = flex.input.read()
    try:
        input = json.loads(input)
        if not isinstance(input, list): raise ValueError
    except ValueError:
        raise ValueError

    # define the expected parameters and map the values to the parameter names
    # based on the positions of the keys/values
    params = OrderedDict()
    params['properties'] = {'required': False, 'validator': validator_list, 'coerce': to_list, 'default': '*'}
    input = dict(zip(params.keys(), input))

    # validate the mapped input against the validator
    # if the input is valid return an error
    v = Validator(params, allow_unknown = True)
    input = v.validated(input)
    if input is None:
        raise ValueError

    # map this function's property names to the API's property names
    property_map = OrderedDict()
    property_map['id'] = 'id'
    property_map['name'] = 'name'
    property_map['createdAt'] = 'createdAt'
    property_map['featuredAt'] = 'featuredAt'
    property_map['url'] = 'url'
    property_map['tagline'] = 'tagline'
    property_map['description'] = 'description'

    try:

        # make the request
        # see here for more info: https://api.producthunt.com/v2/docs

        url = 'https://api.producthunt.com/v2/api/graphql'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + auth_token,
            'Host': 'api.producthunt.com'
        }
        columns = list(property_map.values())
        data = { "query": "query { posts { edges { node {" + " ".join(columns) + " } } } }" }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        response.raise_for_status()
        content = response.json()

        # get the properties to return and the property map
        properties = [p.lower().strip() for p in input['properties']]

        # if we have a wildcard, get all the properties
        if len(properties) == 1 and properties[0] == '*':
            properties = list(property_map.keys())

        # build up the result
        result = []
        result.append(properties)

        edges = content.get('data',{}).get('posts',{}).get('edges',[])
        for item in edges:
            row = [item.get('node').get(property_map.get(p,'')) or '' for p in properties]
            result.append(row)

        flex.output.content_type = "application/json"
        flex.output.write(result)

    except:
        flex.output.content_type = 'application/json'
        flex.output.write([['']])

def validator_list(field, value, error):
    if isinstance(value, str):
        return
    if isinstance(value, list):
        for item in value:
            if not isinstance(item, str):
                error(field, 'Must be a list with only string values')
        return
    error(field, 'Must be a string or a list of strings')

def to_string(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (Decimal)):
        return str(value)
    return value

def to_list(value):
    # if we have a list of strings, create a list from them; if we have
    # a list of lists, flatten it into a single list of strings
    if isinstance(value, str):
        return value.split(",")
    if isinstance(value, list):
        return list(itertools.chain.from_iterable(value))
    return None
