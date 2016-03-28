# -*- coding: utf-8 -*-
import scrapy
from op_scraper.models import LobbyRegisterEntry, LobbyRegisterPerson
from parlament.resources.extractors.lobbyregister import *


class LobbyRegisterSpider(scrapy.Spider):
    name = 'lobbyregister'
    titel = 'Lobby Register Spider'
    
    start_urls = ['http://www.lobbyreg.justiz.gv.at/edikte/ir/iredi18.nsf/liste!OpenForm&subf=r&RestrictToCategory=A1', 'http://www.lobbyreg.justiz.gv.at/edikte/ir/iredi18.nsf/liste!OpenForm&subf=r&RestrictToCategory=B']
    
    def parse(self, response):

        lobbies = LOBBIES.xt(response)
        
        oldest_date = None
        
        for lobby in lobbies:
            
            lobbyists = lobby.pop('lobbyists')
            
            entry, created = LobbyRegisterEntry.objects.update_or_create(
                register_number=lobby['register_number'], 
                defaults=lobby)
            
            if not oldest_date:
                oldest_date = entry.last_seen
            
            for name in lobbyists:
                LobbyRegisterPerson.objects.get_or_create(
                    entry=entry, 
                    name=name)
                
        LobbyRegisterEntry.objects.filter(last_seen__lt = oldest_date).delete()
        LobbyRegisterPerson.objects.filter(last_seen__lt = oldest_date).delete()
