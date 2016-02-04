Inquiries
=======================================

General notes about the structure of the inquiries
--------------------------------------------------

- Inquiries can be submitted by members of the national assembly or federal assembly
- Inquiries can be directed at members of the Austrian government, the president of the court of auditors, the president of the national assembly or the chairmen of parliamentary committes
- Generally, inquiries are submitted in written form, with the exception of oral inquiries to the Austrian government
- Urgent inquiries (dringliche Anfragen) are oral inquiries with a written statement that is presented before the corresponding respondent and are structured in a special way to account for the discussion that is planned after the stakeholders have made their cases.
- While the structure of the data in the database is completely flat, there is some structure inherent to the parliamentary inquiries that can be exploited in post-processing or front-end:

	- Each inquiry has only one response, but each response can have multiple inquiries that it responds to, for example: 
		- https://www.parlament.gv.at/PAKT/VHG/XX/AB/AB_05184/index.shtml
	- Some inquiries are similar or equal to others, e.g. mass inquiries to different governmental departments.
		- https://www.parlament.gv.at/PAKT/VHG/XXV/J/J_06447/index.shtml
		- https://www.parlament.gv.at/PAKT/VHG/XXV/J/J_06448/index.shtml
		- https://www.parlament.gv.at/PAKT/VHG/XXV/J/J_06449/index.shtml
- There are multiple types of inquiries, each type has a name and a shorthand. Shorthands are used for referencing and identifying certain inquiries in general communication and URLs.
+----------------------------------------------------------+-----------+
| Type                                                     | Shorthand |
+==========================================================+===========+
| Schriftliche Anfragen an die Bundesregierung             | J         |
+----------------------------------------------------------+-----------+
| Schriftliche Anfragen an die Bundesregierung (Bundesrat  | J-BR      |
+----------------------------------------------------------+-----------+
| Mündliche Anfragen an die Bundesregierung                | M         |
+----------------------------------------------------------+-----------+
| Mündliche Anfragen (Bundesrat)                           | M-BR      |
+----------------------------------------------------------+-----------+
| Dokumentenanfragen betr. EU an die Bundesregierung       | JEU       |
+----------------------------------------------------------+-----------+
| Schriftliche Anfragen an Ausschussvorsitzende            | JPR       |
+----------------------------------------------------------+-----------+
| Schriftliche Anfragen an PräsidentInnen des Nationalrats | JPR       |
+----------------------------------------------------------+-----------+
| Schriftliche Anfragen an RechnungshofpräsidentInnen      | J         |
+----------------------------------------------------------+-----------+


Scraper Structure
-----------------
The scraper starts out using the RSS feed of the inquiry overview site

	- Site: http://www.parlament.gv.at/PAKT/JMAB/index.shtml  
	- Feed: http://www.parlament.gv.at/PAKT/JMAB/filter.psp

The function get_urls in inquiries.py iterates over NR/BR and all legislative periods (LLP) to collect the links that will be parsed. The code includes a debugging variable containing assorted links for testing changes on all types of inquiries. get_urls will take approx. 2-3 minutes to record all available links to inquiries, and outputs the number of inquiries to be scraped in the terminal. Full scraping and parsing of all inquiries will take about 1-3 hours, depending on your internet connection and database speed.

In the parser, information is extracted and written into an Inquiry object and foreign keys are attached. If the inquiry is urgent (dringliche Anfrage), a more elaborate steps-parser is called (it is *almost* the same as the one for laws) than when it is not urgent.
When a link to a written response can be found in the inquiry's history, that link is recorded and handed over to the callback function when the parser terminates.
At the end of the function, the Inquiry object is saved and the output indicates which inquiry was created or updated.
The functions parse_keywords, parse_docs, parse_steps and parse_parliamentary steps are self-explanatory helper-functions, they are parsers pulled out of the main parser function for clarity.

The callback function for inquiry responses is very similar to the main parser function. 90% of it is merely a simplification of what the parser function does, because lots of restrictions/edge cases don't apply to the responses of inquiries, e.g. urgent inquiries where the response is always oral. At the end of the inquiry response parser, the created or updated response object is attached to the original inquiry and the inquiry item is again saved to the database.

Model structure
---------------

The Inquiry and InquiryResponse models are subclasses of the Law model (cf. models.py), inheriting all of its properties and augmented by a few that are unique to inquiries, specifically senders/receivers and responses.

Example Inquiry
---------------

	- title
		- "Gender Budgeting" im BMEIA
	- source_link
		- https://www.parlament.gv.at/PAKT/VHG/XXV/J/J_06440/index.shtml
	- parl_id
		- J_06440
	- legislative_period
		- XXV

	- description
		- Schriftliche Anfrage der Abgeordneten Mag. Aygül Berivan Aslan, Kolleginnen und Kollegen an den Bundesminister für Europa, Integration und Äußeres betreffend "Gender Budgeting" (im) BMEIA (Bundesministerium für Europa, Integration und Äußeres)
	- category
		- Schriftliche Anfrage
	- keywords
		- Bundeshaushalt III. Sonstiges
	- documents
		- https://www.parlament.gv.at/PAKT/VHG/XXV/J/J_06440/imfname_465628.pdf
		- https://www.parlament.gv.at/PAKT/VHG/XXV/J/J_06440/fname_465724.pdf
		- https://www.parlament.gv.at/PAKT/VHG/XXV/J/J_06440/fnameorig_465724.html
	- sender
		- Mag. Aygül Berivan Aslan
	- receiver
		- Sebastian Kurz
	- steps
		- 10.09.2015 Einlangen im Nationalrat (Frist: 10.11.2015)	 
		- 10.09.2015 Übermittlung an das Bundesministerium für Europa, Integration und Äußeres
		- 23.09.2015 91. Sitzung des Nationalrates: Mitteilung des Einlangens
		- 10.11.2015 Schriftliche Beantwortung (6251/AB)
	- response
		- https://www.parlament.gv.at/PAKT/VHG/XXV/AB/AB_06251/index.shtml