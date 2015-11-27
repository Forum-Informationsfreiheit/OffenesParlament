React = require 'react'
ReactDOM = require 'react-dom'
SearchResults = require './components/SearchResults.cjsx'
AnysearchStore = require './stores/AnysearchStore.coffee'
_ = require 'underscore'

$(document).ready( () ->
  #init tooltip react component
  tooltip_container = document.getElementById('react_tooltip_container')
  if tooltip_container
    ReactTooltip = require("react-tooltip")
    ReactDOM.render(
      React.createElement(ReactTooltip, {
        type: 'light'
        place: 'bottom'
        effect: 'solid'
        multiline: false
        position: {bottom: -16}
      }),
      tooltip_container
    )

  anysearch_container = document.getElementById('anysearch_container')
  content_container = document.getElementById('content')
  if anysearch_container
    Searchbar = require("./components/anysearch/Searchbar.cjsx")
    ReactDOM.render(
      React.createElement(Searchbar, {}),
      anysearch_container
    )

  render_results = () ->
    results = AnysearchStore.get_search_results()
    if content_container and results
      SearchResults = require("./components/SearchResults.cjsx")
      ReactDOM.render(
        React.createElement(SearchResults, {results: results}),
        content_container
      )
  AnysearchStore.addChangeListener(render_results)
  render_results()

  # _current_facets = []
  # _server_facets = {}

  # _human_readable_facets = {
  #   llps: 'Gesetzgebungsperiode'
  #   occupation: 'Beruf'
  #   party: 'Partei'
  #   birthplace: 'Geburtsort'
  #   deathplace: 'Sterbeort'
  # }

  # _update_server_facets = (facets_obj) ->
  #   _server_facets = _.pick(facets_obj, (x, key) ->
  #     return x.length > 1 and _.findIndex(visualSearch.searchQuery.models, (x) -> return _convert_text_to_serverfacet(x.get('category')) == key) < 0
  #   )
  #   console.log _server_facets, visualSearch.searchQuery

  # _convert_serverfacets_to_text = (facet_list) ->
  #   return _.map(facet_list, (facet) ->
  #     if _.has(_human_readable_facets, facet)
  #       return _human_readable_facets[facet]
  #     else
  #       return facet
  #   )

  # _convert_text_to_serverfacet = (human_facet) ->
  #   server_facet = _.findKey(_human_readable_facets, (x) -> x==human_facet)
  #   if server_facet
  #     return server_facet
  #   else
  #     return human_facet

  # $.ajax
  #   url: '/personen/search'
  #   dataType: 'json'
  #   data: {only_facets: 1}
  #   success: (response) ->
  #     # console.log 'result', response
  #     if response.result?
  #       _update_server_facets(response.facets.fields)

  # #init visualSearch
  # visualSearch = VS.init(
  #   container: $('.visual_search')
  #   query: ''
  #   callbacks:
  #     search: (query, searchCollection) ->
  #       console.log 'query', query, searchCollection
  #       data = {}
  #       for item in searchCollection.models
  #         data[_convert_text_to_serverfacet(item.get('category'))] = item.get('value')
  #       $.ajax
  #         url: '/personen/search'
  #         dataType: 'json'
  #         data: data
  #         success: (response) ->
  #           # console.log 'result', response
  #           if response.result?
  #             _update_server_facets(response.facets.fields)
  #             React.render(
  #                 <SearchResults results={response.result} />
  #                 document.getElementById('content')
  #             )

  #     facetMatches: (callback) ->
  #       callback(_convert_serverfacets_to_text(_.keys(_server_facets)))
  #         #   'Gesetz', 'party', 'Person', 'Gesetzgebungsperiode', 'q'
  #     valueMatches: (human_facet, searchTerm, callback) ->
  #       facet = _convert_text_to_serverfacet(human_facet)
  #       if _.has(_server_facets, facet)
  #         callback(_.map(_server_facets[facet], (x) -> x[0]))
  #       # switch facet
  #       #   when 'party'
  #       #     callback([
  #       #       { value: 'spö', label: 'SPÖ' }
  #       #       { value: 'övp',   label: 'ÖVP' }
  #       #       { value: 'grüne',   label: 'GRÜNE' }
  #       #       { value: 'neos', label: 'NEOS' }
  #       #       { value: 'fpö', label: 'FPÖ' }
  #       #     ])
  #       #   when 'Gesetzgebungsperiode'
  #       #     callback([
  #       #       'Pentagon Papers',
  #       #       'CoffeeScript Manual',
  #       #       'Laboratory for Object Oriented Thinking',
  #       #       'A Repository Grows in Brooklyn'
  #       #     ])

  # )

  # visualSearch.searchQuery.on('add change', (facet) ->
  #   if facet?.get('category') == _human_readable_facets['llps']
  #     console.log 'change to permanent'
  #     # facet.set('permanent', true)
  # )
  # visualSearch.searchQuery.on('all', (which, facet) ->
  #   console.log arguments
  # )
  # # console.log visualSearch
  # model = new VS.model.SearchFacet({
  #   category : _human_readable_facets['llps'],
  #   value    : 'XXV',
  #   permanent: true,
  #   app      : visualSearch
  # });
  # visualSearch.searchQuery.add(model, {at: 0});

)
