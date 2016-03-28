Scraper: Lobby Register
==========================

General notes about the lobby register
--------------------------------------

Since 1st of January 2013 Austria has a mandatory lobby register:
http://www.lobbyreg.justiz.gv.at


What kind of information has to be disclosed depends on the lobby register class:

    Lobby register classes:
    A  Lobbying companies (A1) and their clients and fields of activity (A2, not public) - a.e. "Kovar & Partners GmbH"
    B  Companies that employ in-house lobbyists - a.e. "Bayer Austria Gesellschaft m.b.H."
    C  Self-governing bodies - a.e. "Architekten- und Ingenieurkonsulentenkammer für Steiermark und Kärnten"
    D  interest groups - a.e. "Interessenvertretung Gemeinnütziger Organisationen"

    Depending on the class the data set might include information like:
    -  Name
    -  Address
    -  Commercial register number
    -  Information on clients (not public)
    -  Information on spendings/costs/revenues
    -  Lobbyists (name, date of birth)
    -  Homepage
    -  …


Information on the registration and data acquisition process(German): 
http://www.lobbyreg.justiz.gv.at/edikte/ex/edparm3.nsf/h/ir_Leitfaden/$file/Leitfaden.pdf


Legal background(German):
https://www.ris.bka.gv.at/Dokumente/BgblAuth/BGBLA_2012_I_64/BGBLA_2012_I_64.pdf


Notes on www.lobbyreg.justiz.gv.at
----------------------------------

Only lobby register entries of class 'A1' and 'B' are scraped because 'C' and 'D' do not include informations on lobbyists.

For scraping the overview pages for class 'A1' and class 'B' are used:
 -  http://www.lobbyreg.justiz.gv.at/edikte/ir/iredi18.nsf/liste!OpenForm&subf=r&RestrictToCategory=A1
 -  http://www.lobbyreg.justiz.gv.at/edikte/ir/iredi18.nsf/liste!OpenForm&subf=r&RestrictToCategory=B

When starting from 'www.lobbyreg.justiz.gv.at' the overview pages are accessible through the menu entry "Liste nach Registerabteil".

On the overview page the data is provided as an table, where each row corresponds to one lobby register entry and consists of the following columns:  
    'Nr': position of the lobby register entry in selected view
    'Bezeichnung/Firma': name, address, commercial register number
    'Registerzahl': lobby register number
    'Registerabteilung': register class
    'Details':details, lobbyists' names
    'Letzte Änderung': date of last change/update of the lobby register entry

    
notes on lobby register number:
The lobby register number is supposed to be a unique id. However scraping showed that the lobby register number LIVR-00303 was asigned twice within the same class to 'Aktienforum - Österreichischer Verband für Aktien-Emittenten und -Investoren, Lothringerstraße 12, 1031 Wien' and 'Österreichischer Apothekerverband, Spitalgasse 31, 1090 Wien'. This was resolved after it was brought to the attention of ministry of justice(BMJ). (see: https://twitter.com/fin/status/676791501121298432)
The scraper assumes uniqueness of the register numbers and would overwrite entries in case of duplication.


Scraper structure
-----------------

The scraper only uses overview sites. 
At every scraper run data which currently isn't present in the official lobby register is deleted. This is facilitated by the last_seen fields in the models.


Model structure
---------------

  The LobbyRegisterEntry model (Representation of an entry in the Austrian lobby register) includes:
    register_number: lobby register number
    name: name and address of the entity
    commercial_register_number: Firmenbuchnummer
    register_class: 'A1' or 'B'
    last_change: as given on website
    last_seen: timestamp of last model save
 

  The LobbyRegisterPerson model (Lobbyist mentioned in the Austrian lobby register) only includes the name of the lobbyist and refers to corresponding LobbyRegisterEntry. It also includes a last_seen field.