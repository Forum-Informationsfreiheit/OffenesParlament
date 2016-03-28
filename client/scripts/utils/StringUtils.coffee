_ = require 'underscore'
moment = require 'moment'


_human_categories =
  party: 'Partei'
  birthplace: 'Geburtsort'
  llps: 'Gesetzgebungsperiode'
  deathplace: 'Todesort'
  occupation: 'Beruf'
  q: 'Text'
  category: 'Kategorie'
  keywords: 'Schlagwort'
  type: 'Suchtyp'
  debate_type: 'Art der Debatte'
  NR: 'Nationalrat'
  BR: 'Bundesrat'


module.exports =
  get_category_text: (category) ->
    if _.has(_human_categories, category)
      return _human_categories[category]
    else
      return category

  get_search_title: (terms) ->
    llp_string = ''
    type_string = ''
    rest_terms = _.omit(terms, ['llps', 'type'])
    rest_terms_string = _.values(rest_terms).join(', ')
    if _.has(terms, 'llps')
      llp_string = 'Periode ' + terms['llps']
    if _.has(terms, 'type')
      type_string = terms['type']
    result = _.compact([llp_string, rest_terms_string]).join(': ')
    result = _.compact([type_string, result]).join(' in ')
    return result

  capitalize_first_letter: (input) ->
    return input.charAt(0).toUpperCase() + input.slice(1)

  get_date: (timestamp) ->
    mnt = moment(timestamp)
    return mnt.format('DD.MM.YYYY')

