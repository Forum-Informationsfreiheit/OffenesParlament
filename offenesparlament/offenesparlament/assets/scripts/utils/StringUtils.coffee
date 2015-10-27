_human_categories =
  party: 'Partei'
  birthplace: 'Geburtsort'
  llps: 'Gesetzgebungsperiode'
  deathplace: 'Todesort'
  occupation: 'Beruf'
  q: 'Text'


module.exports =
  get_category_text: (category) ->
    if _.has(_human_categories, category)
      return _human_categories[category]
    else
      return category

