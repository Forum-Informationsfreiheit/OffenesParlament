React = require 'react'
SearchResults = require './components/SearchResults.cjsx'

$(document).ready( () ->
  #init tooltip react component
  tooltip_container = document.getElementById('react_tooltip_container')
  if tooltip_container
    ReactTooltip = require("react-tooltip")
    React.render(
      React.createElement(ReactTooltip, {
        type: 'light'
        place: 'bottom'
        effect: 'solid'
        multiline: false
        position: {bottom: -16}
      }),
      tooltip_container
    )

  #init visualSearch
  visualSearch = VS.init(
    container: $('.visual_search')
    query: ''
    callbacks:
      search: (query, searchCollection) ->
        console.log 'query', query, searchCollection
        data = {}
        for item in searchCollection.models
          data[item.get('category')] = item.get('value')
        $.ajax
          url: '/search'
          dataType: 'json'
          data: data
          success: (response) ->
            console.log 'result', response
            if response.result?
              React.render(
                  <SearchResults results={response.result} />
                  document.getElementById('content')
              )

      facetMatches: (callback) ->
          callback([
            'Gesetz', 'party', 'Person', 'Gesetzgebungsperiode', 'q'
          ])
      valueMatches: (facet, searchTerm, callback) ->
        switch facet
          when 'party'
            callback([
              { value: 'spö', label: 'SPÖ' }
              { value: 'övp',   label: 'ÖVP' }
              { value: 'grüne',   label: 'GRÜNE' }
              { value: 'neos', label: 'NEOS' }
              { value: 'fpö', label: 'FPÖ' }
            ])
          when 'Gesetzgebungsperiode'
            callback([
              'Pentagon Papers',
              'CoffeeScript Manual',
              'Laboratory for Object Oriented Thinking',
              'A Repository Grows in Brooklyn'
            ])

  )
)
