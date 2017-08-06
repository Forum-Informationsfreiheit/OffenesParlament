class LawPhases(object):
    PATTERN = [['Vorparlamentarisches Verfahren',
                    ['Entwurf eingegangen',
                        'Stellungnahmen'],
                    ],
                ['Parlamentarisches Verfahren',
                    ['Einlangen im Nationalrat',
                        'Ausschuss',
                        'Plenarberatung',
                        'Beschluss im Nationalrat'
                        'Beschluss im Bundesrat'],
                    ]
                ]

    MATCH_NAMES = {
            'Entwurf eingegangen':
                r'Einlangen im Nationalrat',
            'Stellungnahmen':
                r'Ende der Begutachtungsfrist ([0-9]{1-2}.[0-9]{1-2}.[0-9]{4})', 

            'Einlangen im Nationalrat':
                r'Einlangen im Nationalrat',
            'Ausschuss': 
