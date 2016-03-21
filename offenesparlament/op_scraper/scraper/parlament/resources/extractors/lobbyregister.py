# -*- coding: utf-8 -*-
from scrapy import Selector
from parlament.resources.extractors import SingleExtractor

class LOBBIES(SingleExtractor):

    XPATH = '//*[@id="ergebnisliste"]/table/tbody/tr'

    @classmethod
    def xt(cls, response):
        lobbies = []       
        
        rows = [Selector(text=row.extract())
                    for row in response.xpath(cls.XPATH)]
        
        for row in rows:
            lobby = {}
            lobby_name=row.xpath('//td[2]/text()').extract()[0]
            if lobby_name[-1] ==')' and lobby_name[-9]=='(':
                lobby['name']=lobby_name[0:(-9)]
                lobby['commercial_register_number']=lobby_name[-8:-1]
            else:
                lobby['name']=lobby_name
                lobby['commercial_register_number'] = ''
            lobby['register_number']=row.xpath('//td[3]/a/text()').extract()[0]   
            lobby['register_class']=row.xpath('//td[4]/text()').extract()[0]            
            lobby['lobbyists']=row.xpath('//td[5]/text()').extract()   
            lobby['last_change']=row.xpath('//td[6]/text()').extract()[0]    
            lobbies.append(lobby)
  
        return lobbies