#!/usr/bin/env python 
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 18 19:42:26 2016

@author: anthonymunnelly

https://www.propertypriceregister.ie/website/npsra/pprweb.nsf/page/ppr-home-en
http://www.ossiansmyth.ie/eircode-routing-keys/

"""


import pandas as pd
import json
import unicodecsv as csv
import googlemaps
import datetime
import pickle

class Raw(list):
    
    def __init__(self, houses_url):
        self.houses_url = houses_url
        self.houses_list = self.create_houses_list(self.houses_url)

    def create_houses_list(self, houses_url):
        """
        Reads a .csv file from disk, creates a list from the file
        and then returns that list.
        """
        houses_original = []
        with open(houses_url, 'r') as f:
            reader = csv.reader(f, encoding = 'latin-1')
            for r in reader:
                houses_original.append(r)
        print "There are {:,} rows.".format(len(houses_original))
        
        return houses_original
        
class GeoCode(object):
    
    def __init__(self, houses_url):
        self.address_list = Raw(houses_url).houses_list
        with open("api.json", 'r') as f:
            self.__myKey = json.load(f)

        self.gmaps = googlemaps.Client(key=self.__myKey['mapper'])
        self.house_data = self.get_geodata()
        
        self.houses = pd.DataFrame(self.house_data[0], columns = ["Date",
                                                      "Address",
                                                      "PostCode",
                                                      "County",
                                                      "Price",
                                                      "FullMarketPrice",
                                                      "VAT",
                                                      "Description",
                                                      "Size",
                                                      "Lat",
                                                      "Lon",
                                                      "gCheck"])
    
        self.bad_add = pd.DataFrame(self.house_data[1], columns = ["Date",
                                                      "Address",
                                                      "PostCode",
                                                      "County",
                                                      "Price",
                                                      "FullMarketPrice",
                                                      "VAT",
                                                      "Description",
                                                      "Size",
                                                      "gCheck"])
                                                      
        self.geodata = self.house_data[2]
        
        

    def coordinate_finder(self, anAddress):
        """
        A test function to see if the gmaps.geocode() method has 
        returned a valid result. The function returns -1 if it hasn't,
        and the result if it has.
        """
        result = self.gmaps.geocode(anAddress)
        if len(result) > 0:
            return result[0]
        else:
            return -1
        
    def address_components_searcher(self, component_list, sought_item):
        """
        Iterates through the component list dictionaries to see if the 
        dictionaries have a sought_item key. If they do, that
        item is returned by the fuction. If not, the function
        returns the empty string.
        """
        returnValue = ''
        for c in component_list:
            if sought_item in c['types']:
                returnValue = c['short_name']
        
        return returnValue
    
    def check_geometry(self, lat, lon):
        """
        Checks to see if the latitudinal and longitudinal co-ordinates
        returned by a call to the gmaps.geocode() method are within
        a generous definition of the Dublin city limits. Returns a list
        where the first element is True/False and the second the reason
        for success or failure.
        """

        north = (53.680770, -6.237062) # laytown
        south = (53.200922, -6.110912) # bray
        west = (53.371680, -6.514402) # leixlip amenities
        east = (53.329053, -5.341059) # middle of the Irish sea
        if lat > north[0] or lat < south[0]:
            return [False, 'BadLat']
        elif lon < west[1] or lon > east[1]:
            return [False, 'BadLon']
        else:
            return [True, 'Good']


    def get_geodata(self):
        '''
        The workhorse of the Geocode class. The function iterates through
        the list of addresses in self.address list and categorizes them
        as good or bad addresses. The list being done, the function
        returns a tuple of three values - the good addresses, the bad
        addresses, and all the geocode data returned from the gmaps
        object. The function also prints the index+1 for every 100th
        element as a sanity-checker, as the program can take a long time
        to process over ten thousand addresses.
        '''
        houses_list = []
        bad_addresses_list = []
        geodata_list = []
        
        for item in self.address_list:
            sanity_checker = self.address_list.index(item)+1
            if sanity_checker % 100 == 0:
                print '\nThis is item {:5} of {:,}.'.format(sanity_checker, len(self.address_list))
            try:
                geocode = self.coordinate_finder(item[1])
                if geocode == -1:
                    item.append('NoResponse')
                    bad_addresses_list.append(item)
                    continue
                address = geocode['formatted_address']
                latitude = geocode['geometry']['location']['lat']
                longitude = geocode['geometry']['location']['lng']
                gCheck = self.check_geometry(latitude, longitude)
                if gCheck[0]:
                    postcode = self.address_components_searcher(geocode['address_components'], 'postal_code')
                    
                    clean_line = [item[0],
                                  address,
                                  postcode,
                                  item[3],
                                    item[4],
                                    item[5],
                                    item[6],
                                    item[7],
                                    item[8],
                                    latitude,
                                    longitude,
                                    gCheck[1]]
                    
                    houses_list.append(clean_line)
                    geodata_list.append(geocode)
                else:
                    item.append(gCheck[1])
                    bad_addresses_list.append(item)
                    
            except:
                print 'exception'
                item.append('Exception')
                bad_addresses_list.append(item)
                continue
    
        return (houses_list, bad_addresses_list, geodata_list)

class Ferment(GeoCode):
    
    def __init__(self, geodata, location, year):
        self.geodata = [geodata.houses, geodata.bad_add, geodata.geodata]
        self.bad_add_filename = 'pickle/' + '_'.join(['bad_add', location, year, 'pickle'])
        self.houses_df_filename = 'pickle/' + '-'.join(['houses', location, year, 'pickle'])
        self.geodata_filename = 'pickle/' + '_'.join(['geodata', location, year, 'pickle'])
        self.filenames = [self.houses_df_filename,
                          self.bad_add_filename,
                          self.geodata_filename]
        self.ferment()
                          
    def ferment(self):
        """
        pickles the three data frames one by one,with each named appropriately.
        """
        for i in range(3):
            with open(self.filenames[i], 'w') as f:
                pickle.dump(self.geodata[i], f)
                
        return

if __name__ == '__main__':
    print datetime.datetime.now()

    myUrl = '/Users/anthonymunnelly/Documents/TECH/Python/House_price_analysis/Presentation/PPR/PPR-2016-Dublin.csv'
    myHouses = GeoCode(myUrl)

    print datetime.datetime.now()

    ready2pickle = Ferment(myHouses, 'dublin', '2016')