React = require 'react'
AutosizeInput = require 'react-input-autosize'
Term = require './Term.cjsx'
Suggest = require './Suggest.cjsx'
AnysearchActions = require '../../actions/AnysearchActions.coffee'
AnysearchStore = require '../../stores/AnysearchStore.coffee'
_ = require 'underscore'


_get_state_from_store = () ->
  return {
    terms: AnysearchStore.get_terms()
    categories: AnysearchStore.get_categories()
    values: AnysearchStore.get_values()
    loading: AnysearchStore.is_loading()
  }


Searchbar = React.createClass

  getInitialState: () ->
    initial_state =
      active_term: null
      suggestion_type: null
    return _.extend(initial_state, _get_state_from_store())

  componentDidMount: () ->
    AnysearchStore.addChangeListener(@_onChange)
    AnysearchActions.createTerm('llps', 'XXV')

  componentWillUnmount: () ->
    AnysearchStore.removeChangeListener(@_onChange)

  onSuggestionSelected: (input) ->
    if @state.active_term?
      if @state.suggestion_type == 'category'
        AnysearchActions.changeTermCategory(@state.active_term.id, input)
        @setState({suggestion_type: 'value'})
      else
        AnysearchActions.changeTermValue(@state.active_term.id, input)
        @setState({suggestion_type: null})

  render: ->
    terms = _.map(@state.terms, (term) =>
      term_input_focused = () =>
        AnysearchActions.updateFacets(term.id)
        if term.helper
          @setState({active_term: term, suggestion_type: 'category'})
        else
          @setState({active_term: term, suggestion_type: 'value'})
      term_clicked = () =>
        AnysearchActions.updateFacets(term.id)
        @setState({active_term: term, suggestion_type: 'category'})
      <Term
        key={term.id}
        id={term.id}
        category={term.category}
        value={term.value}
        onTermClicked={term_clicked}
        onInputFocused={term_input_focused}
      />
    )
    loading = if @state.loading then 'loading...' else ''
    if @state.active_term
      switch @state.suggestion_type
        when 'value' then items = @state.values
        when 'category' then items = @state.categories
      suggest = <Suggest
                  items={items}
                  onSelect={@onSuggestionSelected}
                />
    <div className="anysearch_box">
      {terms}
      {loading}
      {suggest}
    </div>

  _onChange: () ->
    @setState(_get_state_from_store())

module.exports = Searchbar

